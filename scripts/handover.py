"""handover.py --schritt TXT [--ziel TXT] [--nicht TXT] [--laeuft TXT] [--lesen TXT] [--commit]
Trimmt STATE.md auf <=5000 Byte (aelteste '- ' Zeilen aus '## Stand' / '## Widerlegt' nach eu-boot-log.md)
und schreibt NEXT_SESSION_PROMPT.md nach Vorlage (Ziel|Stand|Naechster Schritt|Nicht wiederholen|Laeuft noch|Lesen).
Stand = letzter Commit + letzte PROGRESS-Zeile (automatisch). --commit: lokaler Commit als napfkuchen1 ('docs: handover')."""
import argparse, os, subprocess, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(R, "docs", "analysis")
p = argparse.ArgumentParser()
p.add_argument("--schritt", required=True)
p.add_argument("--ziel", default="Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.")
p.add_argument("--nicht", default="LEDGER §4 + gesperrte Ketten in CLAUDE.md 'Audit-Regeln'.")
p.add_argument("--laeuft", default="nichts")
p.add_argument("--lesen", default="STATE.md (letzte 3 Zeilen)")
p.add_argument("--commit", action="store_true")
a = p.parse_args()
def git(*x): return subprocess.run(["git", "-C", R, *x], capture_output=True, text=True).stdout.strip()
# 1) STATE trimmen
sp = os.path.join(A, "STATE.md"); L = open(sp, encoding="utf-8").read().split("\n"); moved = []
def size(): return len("\n".join(L).encode("utf-8"))
sec = ""; idx = []
for i, l in enumerate(L):
    if l.startswith("## "): sec = l
    elif l.startswith("- ") and (sec.startswith("## Stand") or sec.startswith("## Widerlegt")): idx.append(i)
while size() > 5000 and len(idx) > 3:
    i = idx.pop(0); moved.append(L[i]); L[i] = None; L = [x for x in L]  # markieren
    L = [x for x in L if x is not None]; idx = [j - 1 if j > i else j for j in idx]
if moved:
    open(sp, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    open(os.path.join(A, "eu-boot-log.md"), "a", encoding="utf-8", newline="\n").write(
        "\n\n## STATE-Trim %s\n%s\n" % (datetime.date.today(), "\n".join(moved)))
# 2) Prompt
prog = ""
try: prog = [l for l in open(os.path.join(A, "PROGRESS.md"), encoding="utf-8").read().splitlines() if l.strip()][-1][:160]
except Exception: pass
stand = "letzter Commit %s; PROGRESS: %s" % (git("log", "-1", "--format=%h %s")[:80], prog)
txt = "Ziel: %s\nStand: %s\nNaechster Schritt: %s\nNicht wiederholen: %s\nLaeuft noch: %s\nLesen: %s\n" % (a.ziel, stand, a.schritt, a.nicht, a.laeuft, a.lesen)
if len(txt.encode()) > 1500: print("WARN: Prompt >1,5 KB (%d)" % len(txt.encode()))
open(os.path.join(A, "NEXT_SESSION_PROMPT.md"), "w", encoding="utf-8", newline="\n").write(txt)
print("STATE %d B, %d Zeilen verschoben; Prompt %d B" % (size(), len(moved), len(txt.encode())))
if a.commit:
    git("add", "docs/analysis/STATE.md", "docs/analysis/NEXT_SESSION_PROMPT.md", "docs/analysis/eu-boot-log.md")
    print(subprocess.run(["git", "-C", R, "-c", "user.name=napfkuchen1", "-c", "user.email=122364471+napfkuchen1@users.noreply.github.com",
                          "commit", "-qm", "docs: handover"], capture_output=True, text=True).stdout or "committed")
