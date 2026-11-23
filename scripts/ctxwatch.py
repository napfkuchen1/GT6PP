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
fs.sort(key=os.path.getmtime, reverse=True)
def is_worker(p):
    try:
        return "Du bist die Arbeitssession" in open(p, errors="ignore").read(20000)
    except OSError:
        return False
f = next((p for p in fs if is_worker(p)), fs[0])  # Arbeitssession bevorzugt, nicht den Ueberwacher
import json
def txt(o):
    if isinstance(o, str): return len(o)
    if isinstance(o, list): return sum(txt(x) for x in o)
    if isinstance(o, dict):
        if o.get("type") == "image": return 1500
        return sum(txt(v) for k, v in o.items() if k in ("text", "content", "input", "thinking", "command"))
    return 0
chars = 0
for ln in open(f, errors="ignore"):
    try: m = json.loads(ln).get("message")
    except ValueError: continue
    if isinstance(m, dict): chars += txt(m.get("content"))
est = FIX + int(chars / 3.6)
state = "HANDOFF" if est >= limit else "ok"
print(f"ctxwatch {os.path.basename(f)[:8]} ~{est//1000}k Token (Limit {limit//1000}k) -> {state}")
sys.exit(10 if est >= limit else 0)
