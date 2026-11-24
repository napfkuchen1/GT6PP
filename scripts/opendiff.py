#!/usr/bin/env python3
"""Compare file-open sequence: RPCS3 oracle log vs our probe run.
Usage: opendiff.py <probe-run-dir|run.log.err> [oracle.log] [--max N]
Normalizes paths to the part after USRDIR/ (or basename for others), collapses repeats.
Prints: counts, items only in one side, first order divergences."""
import re, sys, os
args = [a for a in sys.argv[1:] if not a.startswith('--')]
mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 14
if '--max' in sys.argv: args.remove(sys.argv[sys.argv.index('--max') + 1])
ours_p = args[0]
orc_p = args[1] if len(args) > 1 else 'work/oracle/RPCS3_user_oracle.log'
if os.path.isdir(ours_p): ours_p = os.path.join(ours_p, 'run.log.err')

def norm(p):
    p = p.replace('\\', '/')
    m = re.search(r'USRDIR/(.*)$', p)
    if m: return m.group(1)
    return p.rsplit('/', 1)[-1]

def collapse(seq):
    out = []
    for x in seq:
        if not out or out[-1] != x: out.append(x)
    return out

ours = [norm(m.group(1)) for l in open(ours_p, encoding='utf-8', errors='replace')
        for m in [re.search(r"\[fs\] open '([^']*)'", l)] if m]
orc = [norm(m.group(1)) for l in open(orc_p, encoding='utf-8', errors='replace')
       for m in [re.search(r'sys_fs_open\(path=“([^”]*)”', l)] if m]
ours, orc = collapse(ours), collapse(orc)
print(f'ours={len(ours)} oracle={len(orc)}')
so, sr = set(ours), set(orc)
print('only-ours:', [x for x in dict.fromkeys(ours) if x not in sr][:mx])
print('only-oracle (first, order):', [x for x in dict.fromkeys(orc) if x not in so][:mx])
# first order divergence over common items
co = [x for x in ours if x in sr]
cr = [x for x in orc if x in so]
n = 0
for i, (a, b) in enumerate(zip(co, cr)):
    if a != b:
        print(f'first common-order divergence at #{i}: ours={a} oracle={b}')
        print('  ours ctx:', co[max(0, i - 2):i + 3]); print('  orc  ctx:', cr[max(0, i - 2):i + 3])
        break
else:
    print('common items same order up to', min(len(co), len(cr)))
