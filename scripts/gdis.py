#!/usr/bin/env python
"""Disassemble guest code from EMAIN.elf (capstone PPC64 BE).

Usage: python -I scripts/gdis.py <ea> [n=40]       n instructions from ea
       python -I scripts/gdis.py <ea> --fn [max=400]  until blr (or max insns)
       python -I scripts/gdis.py <ea> --opd         treat ea as OPD, follow code ptr
Output capped (default 40 lines, --fn 400).
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _elfdis as E


def main(a):
    if len(a) < 1:
        print(__doc__); return 1
    segs = E.load_segments()
    ea = E.parse_int(a[0]); fn = "--fn" in a; opd = "--opd" in a
    nums = [x for x in a[1:] if not x.startswith("--")]
    if opd:
        ea = struct.unpack(">I", E.read(segs, ea, 4))[0]
        print("OPD -> %08X" % ea)
    n = E.parse_int(nums[0]) if nums else (400 if fn else 40)
    buf = E.read(segs, ea, n * 4)
    if not buf:
        print("ea %08X not in ELF" % ea); return 1
    cnt = 0
    for i in E.disasm_all(E.md(), buf, ea):
        print(E.fmt(i)); cnt += 1
        if fn and i.mnemonic in ("blr", "bctr") and cnt > 1:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
