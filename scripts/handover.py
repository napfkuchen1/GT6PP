"""handover.py --item ID --step TXT [--goal TXT] [--not-repeat TXT] [--running TXT] [--read TXT] [--commit]
Moves checked items to CHECKLIST_DONE.md (STATE.md keeps their IDs).
Trims STATE.md to <=5000 bytes (oldest bullets incl. continuation lines under '## State' move to eu-boot-log.md).
Loop guard: appends item + checked-box count to LOOP.tsv and writes the 'Loop' line (CLAUDE.md 'Loop guard').
and writes NEXT_SESSION_PROMPT.md from the template (Goal|State|Next step|Do not repeat|Still running|Read).
State = last commit (automatic). --commit: local commit as napfkuchen1 ('docs: handover')."""
import argparse, os, re, subprocess, sys, datetime
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
p.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID", ""), help="session key; only a rerun with the same key replaces its LOOP row")
a = p.parse_args()
def git(*x): return subprocess.run(["git", "-C", R, *x], capture_output=True, text=True).stdout.strip()
# 0) archive checked items: whole '- [x]' blocks move to CHECKLIST_DONE.md, STATE keeps their IDs
dp = os.path.join(A, "CHECKLIST_DONE.md"); DONE_LINE = "Done (evidence in CHECKLIST_DONE.md):"
def read(path):
    try: return open(path, encoding="utf-8").read()
    except FileNotFoundError: return ""
def checklist(lines):
    """split into (other lines, {id: block lines} of checked items)."""
    keep, found, i = [], {}, 0
    while i < len(lines):
        m = re.match(r"- \[[xX]\] (\w+)", lines[i])
        if not m: keep.append(lines[i]); i += 1; continue
        j = i + 1
        while j < len(lines) and lines[j].startswith("  ") and lines[j].strip(): j += 1
        found[m.group(1)] = lines[i:j]; i = j
    return keep, found
sp = os.path.join(A, "STATE.md")
L, new_done = checklist(read(sp).split("\n"))
head, done_items = checklist(read(dp).split("\n"))
head = [l for l in head if l.strip()] or ["# GT6PP - checked-off items with evidence (moved here by handover.py, counted by the loop guard)"]
done_items.update(new_done)
if new_done:
    open(dp, "w", encoding="utf-8", newline="\n").write("\n".join(head + [""] + [l for b in done_items.values() for l in b]) + "\n")
if done_items:
    L = [l for l in L if not l.startswith(DONE_LINE)]
    ids, lines = list(done_items), []
    while ids:
        line = DONE_LINE + " " + ids.pop(0)
        while ids and len(line) + len(ids[0]) < 190: line += " " + ids.pop(0)
        lines.append(line)
    at = next((k + 1 for k, l in enumerate(L) if l.startswith("## ") and "checklist" in l.lower()), None)
    if at is None: at = next((k for k, l in enumerate(L) if l.startswith("- [ ]")), len(L))
    L[at:at] = lines
    open(sp, "w", encoding="utf-8", newline="\n").write("\n".join(L))
# 1) trim STATE: whole bullet blocks only; orphaned continuation lines left by older trims move too
moved = []
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
PARK, STOP, CAP = 3, 6, 4
def base(i): return re.sub(r"(?<=\d)[a-z]+$", "", i.strip())
open_ids = re.findall(r"(?m)^- \[ \] (\w+)", text)
done = len(set(done_items) - set(open_ids))   # a reopened item does not count as done
lp = os.path.join(A, "LOOP.tsv"); rows = []
if os.path.exists(lp):
    rows = [l.split("\t") for l in open(lp, encoding="utf-8").read().splitlines() if l and not l.startswith("#")]
else:
    open(lp, "w", encoding="utf-8", newline="\n").write("# time\titem\tchecked_boxes\tsession\n")
row = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), a.item, str(done)]
if a.session: row.append(a.session[:8])
if a.reset: rows.append([row[0], "RESET", row[2]])
# only a rerun by the same session (same key and item) replaces its row; other sessions always append
if a.session and rows and rows[-1][1] == a.item and rows[-1][3:] == row[3:]:
    rows[-1] = row
else:
    rows.append(row)
with open(lp, "w", encoding="utf-8", newline="\n") as f:
    f.write("# time\titem\tchecked_boxes\tsession\n" + "".join("\t".join(r) + "\n" for r in rows))
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
# sessions spent on this main item since the last reset, consecutive or not; capped while a sub-item is open
since = rows[max([k for k, r in enumerate(rows) if r[1] == "RESET"], default=-1) + 1:]
base_n = sum(base(r[1]) == base(a.item) for r in since)
base_open = any(base(i) == base(a.item) for i in open_ids)
if all_n >= STOP:
    loop = "STOP: %d sessions without check-off. Do no new work; end with STOP-GRUND: BLOCKER (tried, blocking, human option)." % all_n
elif item_n >= PARK:
    loop = "PARKED %s (%d sessions without check-off): take another open item or a bypass. Total without check-off %d/%d." % (base(a.item), item_n, all_n, STOP)
elif base_open and base_n >= CAP:
    loop = "PARKED %s (%d sessions spent, still open): take another open item or a bypass. Total without check-off %d/%d." % (base(a.item), base_n, all_n, STOP)
else:
    cap = ", sessions %d/%d" % (base_n, CAP) if base_open else ""
    loop = "%s %d/%d%s, total without check-off %d/%d, boxes done %d." % (base(a.item), item_n, PARK, cap, all_n, STOP, done)
# 2) prompt
state = "last commit %s" % git("log", "-1", "--format=%h %s")[:80]
txt = "Goal: %s\nState: %s\nLoop: %s\nNext step: %s\nTool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.\nDo not repeat: %s\nStill running: %s\nRead: %s\n" % (a.goal, state, loop, a.step, a.not_repeat, a.running, a.read)
if len(txt.encode()) > 1500: print("WARN: prompt >1.5 KB (%d)" % len(txt.encode()))
open(os.path.join(A, "NEXT_SESSION_PROMPT.md"), "w", encoding="utf-8", newline="\n").write(txt)
print("STATE %d B, %d lines moved; prompt %d B" % (size(text.split("\n")), len(moved), len(txt.encode())))
print("Loop: " + loop)
if a.commit:
    files = ["docs/analysis/" + n for n in ("STATE.md", "NEXT_SESSION_PROMPT.md", "eu-boot-log.md", "LOOP.tsv",
                                           "CHECKLIST_DONE.md", "LEDGER.md", "PROGRESS.md")]
    git("add", *[f for f in files if os.path.exists(os.path.join(R, f))])
    c = subprocess.run(["git", "-C", R, "-c", "user.name=napfkuchen1", "-c", "user.email=122364471+napfkuchen1@users.noreply.github.com",
                        "commit", "-qm", "docs: handover"], capture_output=True, text=True)
    print("committed" if c.returncode == 0 else "COMMIT FAILED: " + (c.stderr or c.stdout).strip())
    sys.exit(1 if c.returncode else 0)
