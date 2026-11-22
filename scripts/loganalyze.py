"""Compact log summary for probe runs (keeps raw logs out of the model context).
Usage: python scripts/loganalyze.py <run-dir|log-file> [--grep REGEX] [--max N] [--top N]
Prints <=40 lines: size, boot variant, error/stub counters, top repeated line patterns,
first/last match of --grep (+count). Never prints more than --max lines (default 40).
"""
import sys, re, os, collections, argparse
ap = argparse.ArgumentParser()
ap.add_argument('target'); ap.add_argument('--grep', action='append', default=[])
ap.add_argument('--max', type=int, default=40); ap.add_argument('--top', type=int, default=8)
a = ap.parse_args()
t = a.target
logs = [t] if os.path.isfile(t) else [os.path.join(t, n) for n in ('run.log', 'run.log.err') if os.path.exists(os.path.join(t, n))]
if not logs: sys.exit('no log found in ' + t)
out = []
def emit(s): out.append(s[:220])
boot = os.path.join(t, 'boot.txt') if os.path.isdir(t) else ''
if boot and os.path.exists(boot): emit(open(boot).read().strip())
lines = []
for f in logs:
    emit('%s: %d bytes' % (os.path.basename(f), os.path.getsize(f)))
    lines += open(f, encoding='utf-8', errors='replace').read().splitlines()
emit('lines: %d' % len(lines))
keys = ['unresolved NID', 'dispatch MISS', 'DROPPED', 'REJECTED', 'LanguageSelectRoot', 'AdjustScreenRoot', 'gtmode', 'sound_gt/track', 'FATAL', 'abort', 'stuck', 'crash']
cnt = {k: sum(1 for l in lines if k in l) for k in keys}
emit('counters: ' + ', '.join('%s=%d' % (k, v) for k, v in cnt.items() if v) or 'none')
pat = collections.Counter(re.sub(r'0x[0-9A-Fa-f]+|\b[0-9A-Fa-f]{6,}\b|\d+', 'N', l)[:90] for l in lines)
emit('top patterns:')
for p, n in pat.most_common(a.top): emit('  %6d  %s' % (n, p))
for g in a.grep:
    rx = re.compile(g); m = [(i, l) for i, l in enumerate(lines) if rx.search(l)]
    emit('grep /%s/: %d hits' % (g, len(m)))
    for i, l in m[:3]: emit('  first L%d: %s' % (i + 1, l.strip()))
    if len(m) > 6: emit('  ...')
    for i, l in m[-3:] if len(m) > 3 else []: emit('  last  L%d: %s' % (i + 1, l.strip()))
print('\n'.join(out[:a.max]))
