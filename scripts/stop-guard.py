#!/usr/bin/env python
"""Claude Code Stop hook: keep the session working after a finished hypothesis.

Blocks the stop (decision=block) unless the last assistant text names a real stop reason
(menu reached, blocker, handover ready) or 8 continuations in a row were already forced.
Disable: create work/.stop-guard-off. Counter: work/.stop-guard-count.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CNT = os.path.join(ROOT, "work", ".stop-guard-count")
OFF = os.path.join(ROOT, "work", ".stop-guard-off")
MAX = 8
OK = ("hauptmenue erreicht", "hauptmenü erreicht", "uebergabe bereit", "übergabe bereit", "blocker:", "stop-grund")


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
    txt = last_text(d).lower()
    n = 0
    try:
        n = int(open(CNT).read().strip() or 0)
    except Exception:
        pass
    reason_ok = any(k in txt for k in OK)
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
                  "Nur bei Hauptmenue erreicht / echtem Blocker / 'Uebergabe bereit' anhalten." % (n + 1, MAX)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
