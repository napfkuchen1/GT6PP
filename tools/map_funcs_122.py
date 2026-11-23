#!/usr/bin/env python3
"""Map 1.00 guest functions to 1.22 by masked-instruction hash (relocations/immediates masked).
Usage: map_funcs_122.py 0xADDR [0xADDR ...]   (or --from-src to scan tools/ + gt6/src for func_XXXXXXXX)
Prints: addr100 -> addr122 | status (unique / ambiguous(N) / none) | len100 len122
Exact masked-hash + length match; ambiguous = same body >1x (take by call-order/xref manually)."""
import json, re, struct, sys, hashlib
from pathlib import Path
R = Path(__file__).resolve().parent.parent
def load(elf, fj):
    d = open(R / elf, 'rb').read()
    fs = sorted((int(f['start'], 16), int(f['end'], 16)) for f in json.load(open(R / fj)))
    return d, dict(fs)
def key(d, s, e):
    n = (e - s) // 4
    ws = struct.unpack('>%dI' % n, d[s - 0x10000:s - 0x10000 + n * 4])
    out = []
    for w in ws:
        op = w >> 26
        if op in (18,): w &= 0xFC000003
        elif op == 16: w &= 0xFFFF0003
        elif op in (14, 15, 12, 13, 8, 9, 10, 11, 24, 25, 26, 27, 28, 29, 20, 21, 7) or 32 <= op <= 55 or op in (58, 62): w &= 0xFFFF0000
        out.append(w)
    return hashlib.sha1(struct.pack('>%dI' % n, *out)).hexdigest(), n
def main(a):
    d0, f0 = load('work/bin/EMAIN.elf', 'work/analysis/emain/functions_corrected.json')
    d1, f1 = load('work/bin122/EMAIN.elf', 'work/analysis/emain122/functions_corrected.json')
    if a and a[0] == '--from-src':
        s = set()
        for p in list((R / 'tools').glob('*.py')) + list((R / 'gt6/src').glob('*.cpp')) + list((R / 'gt6/src').glob('*.h')):
            s |= set(int(x, 16) for x in re.findall(r'func_([0-9A-F]{8})', p.read_text(encoding='latin-1')))
        a = sorted(s)
    else:
        a = [int(x, 16) for x in a]
    idx = {}
    for s, e in f1.items():
        if e - s >= 8:
            idx.setdefault(key(d1, s, e), []).append(s)
    for t in a:
        if t not in f0: print('%08X -> ? (not a 1.00 func start)' % t); continue
        k = key(d0, t, f0[t])
        h = idx.get(k, [])
        st = 'unique' if len(h) == 1 else ('none' if not h else 'ambiguous(%d)' % len(h))
        print('%08X -> %s | %s | %d' % (t, ','.join('%08X' % x for x in h[:3]) or '-', st, k[1]))
main(sys.argv[1:])
