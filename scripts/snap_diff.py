"""snap_diff.py <snapA> <snapB> [maxpages=15]: changed be32 words per 4KB page between two PS3_SNAP_AT dirs."""
import sys, os, struct, collections
a, b = sys.argv[1], sys.argv[2]; mx = int(sys.argv[3]) if len(sys.argv) > 3 else 15
pages = []; tot = 0
for f in sorted(os.listdir(a)):
    if not f.startswith('reg_') or not os.path.exists(os.path.join(b, f)): continue
    base = int(f[4:12], 16)
    da = open(os.path.join(a, f), 'rb').read(); db = open(os.path.join(b, f), 'rb').read()
    n = min(len(da), len(db)) // 4
    wa = struct.unpack('>%dI' % n, da[:n*4]); wb = struct.unpack('>%dI' % n, db[:n*4])
    cnt = collections.Counter()
    for i in range(n):
        if wa[i] != wb[i]: cnt[i >> 10] += 1
    for p, c in cnt.items(): pages.append((c, base + p * 4096)); tot += c
pages = [p for p in pages if p[0] <= 200 and (0x01000000 <= p[1] < 0x02000000 or 0x70000000 <= p[1] < 0x80000000 or 0x20000000 <= p[1] < 0x30000000)]
pages.sort(reverse=True)
print('total changed words', tot, 'pages', len(pages))
for c, ea in pages[:mx]: print('%08X %d' % (ea, c))
