"""ctxwatch.py [--limit 110000] [--session <id-prefix>]
Schaetzt den Kontext der laufenden Claude-Session aus dem Transcript (.jsonl, chars/3.6 + 25k Fixanteil).
Exit 0 = ok, 10 = Handoff faellig (>= limit). Grobe Schaetzung, bewusst konservativ."""
import glob, os, sys

FIX = 25000  # System-Prompt + Tools + CLAUDE.md + Memory
a = sys.argv[1:]
limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 110000
sess = a[a.index("--session") + 1] if "--session" in a else ""
d = os.path.join(os.path.expanduser("~"), ".claude", "projects", "C--Users-user-Downloads-Games-GT6-ClaudeCode-GT6PP")
fs = [f for f in glob.glob(os.path.join(d, "*.jsonl")) if os.path.basename(f).startswith(sess)]
if not fs:
    print("ctxwatch: kein Transcript"); sys.exit(0)
f = max(fs, key=os.path.getmtime)
chars = os.path.getsize(f)
est = FIX + int(chars / 3.6)
state = "HANDOFF" if est >= limit else "ok"
print(f"ctxwatch {os.path.basename(f)[:8]} ~{est//1000}k Token (Limit {limit//1000}k) -> {state}")
sys.exit(10 if est >= limit else 0)
