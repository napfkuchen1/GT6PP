#!/usr/bin/env python
"""checkpoints.py <probe-dir> [--commit H]: score C0..C6 (docs/analysis/PROGRESS.md) and append ONE table row.
C2/C3 are heuristics (orig boot + non-black frame; PAD press + changed 2nd frame): confirm visually once."""
import os, re, struct, subprocess, sys, datetime

def nonblack(bmp):
    d = open(bmp, "rb").read()
    off, = struct.unpack_from("<I", d, 10); w, h, _, bpp = struct.unpack_from("<iiHH", d, 18)
    bp = bpp // 8; row = (w * bp + 3) & ~3; h = abs(h); n = nb = 0
    for y in range(0, h, 4):
        base = off + y * row
        for x in range(0, w, 4):
            p = base + x * bp
            if p + 2 < len(d):
                n += 1
                if max(d[p], d[p + 1], d[p + 2]) >= 16: nb += 1
    return nb / n if n else 0.0, d

def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    pd = a[0].rstrip(chr(92) + "/")
    com = sys.argv[sys.argv.index("--commit") + 1] if "--commit" in sys.argv else \
        subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    txt = open(os.path.join(pd, "boot.txt"), errors="ignore").read()
    log = ""
    for f in ("run.log", "run.log.err"):
        p = os.path.join(pd, f)
        if os.path.exists(p): log += open(p, errors="ignore").read()
    boot = (re.search(r"boot=(\w+)", txt) or [0, "?"])[1]
    c = {}
    c["C0"] = "gt6.exe" in txt and "unresolved NID" not in log and len(log) > 1000 and "STALLED@" not in txt
    frac = None; f0 = os.path.join(pd, "frame_00", "backbuffer.bmp")
    if os.path.exists(f0): frac, d0 = nonblack(f0)
    c["C1"] = frac is not None and frac > 0.05
    c["C2"] = c["C1"] and boot == "orig"
    f1 = os.path.join(pd, "frame_01", "backbuffer.bmp")
    c["C3"] = bool(c["C2"] and re.search(r"press 0x", log) and os.path.exists(f1) and open(f1, "rb").read() != d0)
    c["C4"] = c["C1"] and "PDIPFS/59/FI" not in log
    c["C5"] = "PDIPFS/59/FI" in log
    c["C6"] = False
    flag = ""; ok = True
    for k in ("C0", "C1", "C2", "C3", "C4", "C5", "C6"):
        if not ok: flag += " -"; continue
        flag += " ok" if c[k] else " FAIL"; ok = bool(c[k]) if k not in ("C2", "C3") or boot == "orig" else True
    lang = (re.search(r"PS3_LANG=([\w-]+)", txt) or [0, ""])[1]
    row = "%s | %s | 1.22 | %s | %s | %s | non-black=%s%s" % (
        datetime.date.today(), com, boot, flag.strip(), os.path.basename(pd),
        "nocapture" if frac is None else "%.0f%%" % (frac * 100), (" lang=" + lang) if lang else "")
    pr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "analysis", "PROGRESS.md")
    if "--dry" in sys.argv: print(row); return
    if frac is None and "--force" not in sys.argv:
        print("NOT appended (no frame capture = C1 unmeasured; run with -Frame N or --force):", row); return
    with open(pr, "ab") as f: f.write((row + "\r\n").encode())
    print(row)

main()
