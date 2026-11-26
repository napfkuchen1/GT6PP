"""handover.py --item ID --step TXT [--goal TXT] [--not-repeat TXT] [--running TXT] [--read TXT] [--commit]
Trims STATE.md to <=5000 bytes (oldest bullets incl. continuation lines under '## State' move to eu-boot-log.md).
Loop guard: appends item + checked-box count to LOOP.tsv and writes the 'Loop' line (CLAUDE.md 'Loop guard').
and writes NEXT_SESSION_PROMPT.md from the template (Goal|State|Next step|Do not repeat|Still running|Read).
State = last commit + last PROGRESS line (automatic). --commit: local commit as napfkuchen1 ('docs: handover')."""
import argparse, os, re, subprocess, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(R, "docs", "analysis")
p = argparse.ArgumentParser()
p.add_argument("--item", required=True, help="checklist ID this session worked on, e.g. I1")
p.add_argument("--step", required=True)
p.add_argument("--reset", action="store_true", help="only after the user lifted a loop-guard BLOCKER: restart counters")
p.add_argument("--goal", default="M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.")
p.add_argument("--not-repeat", default="LEDGER §4 + locked chains in CLAUDE.md 'Audit rules'.")
p.add_argument("--running", default="nothing")
p.add_argument("--read", default="STATE.md (last 3 lines)")
p.add_argument("--commit", action="store_true")
a = p.parse_args()
def git(*x): return subprocess.run(["git", "-C", R, *x], capture_output=True, text=True).stdout.strip()
# 1) trim STATE: whole bullet blocks only; orphaned continuation lines left by older trims move too
sp = os.path.join(A, "STATE.md"); L = open(sp, encoding="utf-8").read().split("\n"); moved = []
def size(lines): return len("\n".join(lines).encode("utf-8"))
def blocks(lines):
    """[(start, end, is_orphan)] of blocks in the '## State' section."""
    out, inside, i = [], False, 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("## "): inside = l.startswith("## State"); i += 1; continue
        if inside and l.strip():
            j = i + 1
            while j < len(lines) and lines[j].startswith("  ") and lines[j].strip(): j += 1
            if l.startswith("- "): out.append((i, j, False))
            elif l.startswith("  "): out.append((i, j, True))
            i = j; continue
        i += 1
    return out
while True:
    bl = blocks(L)
    orphans = [x for x in bl if x[2]]
    if orphans: s, e, _ = orphans[0]
    elif size(L) > 5000 and len(bl) > 3: s, e, _ = bl[0]
    else: break
    moved += L[s:e]; del L[s:e]
text = re.sub(r"\n{3,}", "\n\n", "\n".join(L))
if moved:
    open(sp, "w", encoding="utf-8", newline="\n").write(text)
    open(os.path.join(A, "eu-boot-log.md"), "a", encoding="utf-8", newline="\n").write(
        "\n\n## STATE trim %s\n%s\n" % (datetime.date.today(), "\n".join(moved)))
if size(text.split("\n")) > 5000: print("WARN: STATE.md still >5000 B, shorten it by hand")
# 1b) loop guard
PARK, STOP = 3, 6
def base(i): return re.sub(r"(?<=\d)[a-z]+$", "", i.strip())
done = len(re.findall(r"(?m)^- \[[xX]\]", text))
lp = os.path.join(A, "LOOP.tsv"); rows = []
if os.path.exists(lp):
    rows = [l.split("\t") for l in open(lp, encoding="utf-8").read().splitlines() if l and not l.startswith("#")]
else:
    open(lp, "w", encoding="utf-8", newline="\n").write("# time\titem\tchecked_boxes\n")
row = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), a.item, str(done)]
# a second handover run within the same session (<60 min) replaces the previous row
if a.reset: rows.append([row[0], "RESET", row[2]])
if rows and rows[-1][1] == a.item and (datetime.datetime.now() - datetime.datetime.strptime(rows[-1][0], "%Y-%m-%d %H:%M")).total_seconds() < 3600:
    rows[-1] = row
else:
    rows.append(row)
with open(lp, "w", encoding="utf-8", newline="\n") as f:
    f.write("# time\titem\tchecked_boxes\n" + "".join("\t".join(r) + "\n" for r in rows))
def streak(match):
    """sessions at the end of the log that satisfy match and saw no new check-off."""
    n = 0
    for k in range(len(rows) - 1, -1, -1):
        before = int(rows[k - 1][2]) if k else int(rows[k][2])
        if not match(rows[k]) or int(rows[k][2]) > before: break
        n += 1
    return n
item_n = streak(lambda r: base(r[1]) == base(a.item))
all_n = streak(lambda r: r[1] != "RESET")
if all_n >= STOP:
    loop = "STOP: %d sessions without check-off. Do no new work; end with STOP-GRUND: BLOCKER (tried, blocking, human option)." % all_n
elif item_n >= PARK:
    loop = "PARKED %s (%d sessions without check-off): take another open item or a bypass. Total without check-off %d/%d." % (base(a.item), item_n, all_n, STOP)
else:
    loop = "%s %d/%d, total without check-off %d/%d, boxes done %d." % (base(a.item), item_n, PARK, all_n, STOP, done)
# 2) prompt
prog = ""
try: prog = [l for l in open(os.path.join(A, "PROGRESS.md"), encoding="utf-8").read().splitlines() if l.strip()][-1][:160]
except Exception: pass
state = "last commit %s; PROGRESS: %s" % (git("log", "-1", "--format=%h %s")[:80], prog)
txt = "Goal: %s\nState: %s\nLoop: %s\nNext step: %s\nTool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.\nDo not repeat: %s\nStill running: %s\nRead: %s\n" % (a.goal, state, loop, a.step, a.not_repeat, a.running, a.read)
if len(txt.encode()) > 1500: print("WARN: prompt >1.5 KB (%d)" % len(txt.encode()))
open(os.path.join(A, "NEXT_SESSION_PROMPT.md"), "w", encoding="utf-8", newline="\n").write(txt)
print("STATE %d B, %d lines moved; prompt %d B" % (size(text.split("\n")), len(moved), len(txt.encode())))
print("Loop: " + loop)
if a.commit:
    git("add", "docs/analysis/STATE.md", "docs/analysis/NEXT_SESSION_PROMPT.md", "docs/analysis/eu-boot-log.md", "docs/analysis/LOOP.tsv")
    print(subprocess.run(["git", "-C", R, "-c", "user.name=napfkuchen1", "-c", "user.email=122364471+napfkuchen1@users.noreply.github.com",
                          "commit", "-qm", "docs: handover"], capture_output=True, text=True).stdout or "committed")
