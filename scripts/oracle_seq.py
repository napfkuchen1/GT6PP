#!/usr/bin/env python3
"""Extract syscall/HLE call sequence from an RPCS3 log window, run-length compressed.
Usage: oracle_seq.py <log> <from_line> <to_line> [--max N] [--raw]"""
import re, sys
log, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 40
rx = re.compile(r'\{PPU\[0x[0-9a-f]+\] Thread \(([^)]*)\)[^}]*\} (\w+): (\w+)\((?!\))')
seq = []
for i, l in enumerate(open(log, encoding='utf-8', errors='replace'), 1):
    if i < a: continue
    if i > b: break
    m = rx.search(l)
    if not m: continue
    th, mod, fn = m.groups()
    if fn in ('savedata_op',): continue
    key = (th, fn)
    if seq and seq[-1][0] == key: seq[-1][1] += 1
    else: seq.append([key, 1])
print(len(seq), "runs")
for (th, fn), n in seq[:mx]:
    print("%-8s %-40s x%d" % (th, fn, n))
