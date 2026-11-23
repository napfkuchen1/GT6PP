#!/usr/bin/env python3
"""Locate SPURS job images (raw ranges of EMAIN) by runtime fingerprint (FNV-1a-64) + size.
Usage: find_spu_jobs.py <EMAIN.elf> <fp:size> ...   (fp hex, size dec). Scans 128-aligned offsets with header prefilter."""
import sys
d = open(sys.argv[1], 'rb').read()
want = [(int(a.split(':')[0], 16), int(a.split(':')[1])) for a in sys.argv[2:]]
M = (1 << 64) - 1
def fnv(b):
    h = 1469598103934665603
    for c in b:
        h = ((h ^ c) * 0x100000001b3) & M
    return h
cands = [o for o in range(0, len(d) - 64, 128)
         if d[o] in (0x42, 0x43) and d[o + 3] in (0x02, 0x82) and d[o + 4] in (0x42, 0x43) and d[o + 7] in (0x02, 0x82)]
print("candidates", len(cands), file=sys.stderr)
for fp, size in want:
    hit = None
    for o in cands:
        if o + size <= len(d) and fnv(d[o:o + size]) == fp:
            hit = o; break
    print("%016X %d %s" % (fp, size, hex(hit) if hit is not None else "NOT FOUND"))
