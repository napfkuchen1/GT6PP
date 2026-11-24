#!/usr/bin/env python
"""Claude Code Stop hook: keep the session working after a finished hypothesis.

Blocks the stop (decision=block) unless the last assistant text has a line starting
'STOP-GRUND: MENUE|BLOCKER|UEBERGABE' or MAX (25) continuations without a new commit were forced.
Disable: create work/.stop-guard-off. Counter: work/.stop-guard-count.
"""  # token kept literal: the SENT regex below depends on it
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CNT = os.path.join(ROOT, "work", ".stop-guard-count")
OFF = os.path.join(ROOT, "work", ".stop-guard-off")
MAX = 25  # consecutive blocks WITHOUT a new commit
HEADF = os.path.join(ROOT, "work", ".stop-guard-head")
SENT = re.compile(r"^\s*STOP-GRUND:\s*(MENUE|BLOCKER|UEBERGABE)", re.I | re.M)


def last_text(d):
    t = d.get("last_assistant_message")
    if isinstance(t, str) and t:
        return t
    p = d.get("transcript_path")
    out = ""
    try:
        for line in open(p, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") == "assistant":
                c = (o.get("message") or {}).get("content")
                if isinstance(c, list):
                    s = "".join(b.get("text", "") for b in c if b.get("type") == "text")
                    if s:
                        out = s
    except Exception:
        pass
    return out


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    if os.path.exists(OFF):
        return 0
    cwd = str(d.get('cwd', '')).replace(chr(92), '/')
    if '/.claude/worktrees/' in cwd:  # do not throttle Monitor/worktree sessions
        return 0
    txt = last_text(d)
    n = 0
    try:
        n = int(open(CNT).read().strip() or 0)
    except Exception:
        pass
    # Fortschritt (neuer Commit seit letztem Block) setzt den Zaehler zurueck
    try:
        head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        head = ""
    try:
        old = open(HEADF).read().strip()
    except Exception:
        old = ""
    if head and head != old:
        n = 0
        try:
            open(HEADF, "w").write(head)
        except Exception:
            pass
    reason_ok = bool(SENT.search(txt))
    if reason_ok or n >= MAX:
        try:
            os.remove(CNT)
        except Exception:
            pass
        return 0
    try:
        open(CNT, "w").write(str(n + 1))
    except Exception:
        pass
    print(json.dumps({
        "decision": "block",
        "reason": "Stop-Guard (%d/%d): a finished hypothesis is not the end of the turn (CLAUDE.md turn-end rule). "
                  "Update STATE.md, commit locally (napfkuchen1, no trailer), IMMEDIATELY start the next hypothesis. "
                  "Stop ONLY with a line at the start of a line: STOP-GRUND: MENUE / BLOCKER <reason> / UEBERGABE" % (n + 1, MAX)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
