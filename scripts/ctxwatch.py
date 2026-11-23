"""ctxwatch.py [--limit 200000] [--session <id-prefix>]
Kontext der laufenden Claude-Session aus dem Transcript (.jsonl): echte usage-Werte der letzten
Assistant-Antwort (input + cache_creation + cache_read). Fallback: chars/3.6 + 90k Fixanteil.
Exit 0 = ok, 10 = Handoff faellig (>= limit)."""
import glob, json, os, sys

FIX = 90000  # gemessener Startkontext (Tools+System+CLAUDE.md), nur Fallback
a = sys.argv[1:]
limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 200000
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
def txt(o):
    if isinstance(o, str): return len(o)
    if isinstance(o, list): return sum(txt(x) for x in o)
    if isinstance(o, dict):
        if o.get("type") == "image": return 1500
        return sum(txt(v) for k, v in o.items() if k in ("text", "content", "input", "thinking", "command"))
    return 0
chars, last = 0, 0
for ln in open(f, errors="ignore"):
    try: o = json.loads(ln)
    except ValueError: continue
    m = o.get("message")
    if not isinstance(m, dict): continue
    chars += txt(m.get("content"))
    u = m.get("usage")
    if isinstance(u, dict):
        t = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
        if t: last = t
est = last if last else FIX + int(chars / 3.6)
src = "usage" if last else "schaetz"
state = "HANDOFF" if est >= limit else "ok"
print(f"ctxwatch {os.path.basename(f)[:8]} ~{est//1000}k Token [{src}] (Limit {limit//1000}k) -> {state}")
sys.exit(10 if est >= limit else 0)
