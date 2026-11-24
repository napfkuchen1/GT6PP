"""handover.py --step TXT [--goal TXT] [--not-repeat TXT] [--running TXT] [--read TXT] [--commit]
Trims STATE.md to <=5000 bytes (oldest '- ' lines under '## State' / '## Refuted' move to eu-boot-log.md)
and writes NEXT_SESSION_PROMPT.md from the template (Goal|State|Next step|Do not repeat|Still running|Read).
State = last commit + last PROGRESS line (automatic). --commit: local commit as napfkuchen1 ('docs: handover')."""
import argparse, os, subprocess, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(R, "docs", "analysis")
p = argparse.ArgumentParser()
p.add_argument("--step", required=True)
p.add_argument("--goal", default="Main menu (C6), EU 1.22 + ps3recomp v0.20.")
p.add_argument("--not-repeat", default="LEDGER §4 + locked chains in CLAUDE.md 'Audit rules'.")
p.add_argument("--running", default="nothing")
p.add_argument("--read", default="STATE.md (last 3 lines)")
p.add_argument("--commit", action="store_true")
a = p.parse_args()
def git(*x): return subprocess.run(["git", "-C", R, *x], capture_output=True, text=True).stdout.strip()
# 1) trim STATE
sp = os.path.join(A, "STATE.md"); L = open(sp, encoding="utf-8").read().split("\n"); moved = []
def size(): return len("\n".join(L).encode("utf-8"))
sec = ""; idx = []
for i, l in enumerate(L):
    if l.startswith("## "): sec = l
    elif l.startswith("- ") and (sec.startswith("## State") or sec.startswith("## Refuted")): idx.append(i)
while size() > 5000 and len(idx) > 3:
    i = idx.pop(0); moved.append(L[i]); L[i] = None; L = [x for x in L]  # mark
    L = [x for x in L if x is not None]; idx = [j - 1 if j > i else j for j in idx]
if moved:
    open(sp, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    open(os.path.join(A, "eu-boot-log.md"), "a", encoding="utf-8", newline="\n").write(
        "\n\n## STATE trim %s\n%s\n" % (datetime.date.today(), "\n".join(moved)))
# 2) prompt
prog = ""
try: prog = [l for l in open(os.path.join(A, "PROGRESS.md"), encoding="utf-8").read().splitlines() if l.strip()][-1][:160]
except Exception: pass
state = "last commit %s; PROGRESS: %s" % (git("log", "-1", "--format=%h %s")[:80], prog)
txt = "Goal: %s\nState: %s\nNext step: %s\nDo not repeat: %s\nStill running: %s\nRead: %s\n" % (a.goal, state, a.step, a.not_repeat, a.running, a.read)
if len(txt.encode()) > 1500: print("WARN: prompt >1.5 KB (%d)" % len(txt.encode()))
open(os.path.join(A, "NEXT_SESSION_PROMPT.md"), "w", encoding="utf-8", newline="\n").write(txt)
print("STATE %d B, %d lines moved; prompt %d B" % (size(), len(moved), len(txt.encode())))
if a.commit:
    git("add", "docs/analysis/STATE.md", "docs/analysis/NEXT_SESSION_PROMPT.md", "docs/analysis/eu-boot-log.md")
    print(subprocess.run(["git", "-C", R, "-c", "user.name=napfkuchen1", "-c", "user.email=122364471+napfkuchen1@users.noreply.github.com",
                          "commit", "-qm", "docs: handover"], capture_output=True, text=True).stdout or "committed")
