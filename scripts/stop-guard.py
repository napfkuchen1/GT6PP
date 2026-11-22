#!/usr/bin/env python
"""Claude Code Stop hook: keep the session working after a finished hypothesis.

Blocks the stop (decision=block) unless the last assistant text has a line starting
'STOP-GRUND: MENUE|BLOCKER|UEBERGABE' or 8 continuations in a row were already forced.
Disable: create work/.stop-guard-off. Counter: work/.stop-guard-count.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CNT = os.path.join(ROOT, "work", ".stop-guard-count")
OFF = os.path.join(ROOT, "work", ".stop-guard-off")
MAX = 8
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
    txt = last_text(d)
    n = 0
    try:
        n = int(open(CNT).read().strip() or 0)
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
        "reason": "Stop-Guard (%d/%d): Hypothese fertig ist kein Turn-Ende (CLAUDE.md Turn-Ende-Regel). "
                  "STATE.md aktualisieren, lokal committen (napfkuchen1, kein Trailer), SOFORT die naechste Hypothese starten. "
                  "Anhalten NUR mit Zeile am Zeilenanfang: STOP-GRUND: MENUE / BLOCKER <grund> / UEBERGABE" % (n + 1, MAX)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
