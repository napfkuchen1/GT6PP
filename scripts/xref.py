#!/usr/bin/env python
"""Find readers/writers of a struct field offset, or callers of a function, in EMAIN.elf.

Usage: python -I scripts/xref.py --field 0x90 [--rw r|w] [--in LO-HI] [--max 60]
         loads/stores whose displacement == 0x90 (lwz/stw/lbz/stb/lhz/sth/ld/std/lfs/stfs ...)
       python -I scripts/xref.py --call 0x9B89D8 [--max 60]
         direct bl/b to that address
       python -I scripts/xref.py --imm 0x164AB90 [--max 60]
         lis+addi/ori pairs forming that 32-bit constant (global address users)
--imm misses TOC-relative access (r2+off): use --field <off> --in range for those.
--in restricts the scanned address range (hex, e.g. 0x560000-0x580000).
Output is capped by --max (default 60). Summary line shows total hits.
"""
import re, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _elfdis as E

LOAD = ("lbz", "lhz", "lha", "lwz", "lwa", "ld", "lfs", "lfd", "lbzu", "lhzu", "lwzu", "ldu")
STORE = ("stb", "sth", "stw", "std", "stfs", "stfd", "stbu", "sthu", "stwu", "stdu")


def args(a):
    o = {"max": 60, "rw": None, "rng": None}
    i = 0
    while i < len(a):
        k = a[i]
        if k in ("--field", "--call", "--imm", "--max", "--rw", "--in"):
            v = a[i + 1]; i += 2
            if k == "--in":
                lo, hi = v.split("-"); o["rng"] = (int(lo, 0), int(hi, 0))
            elif k == "--rw":
                o["rw"] = v
            else:
                o[k[2:]] = int(v, 0)
        else:
            i += 1
    return o


def main(a):
    o = args(a)
    if not any(k in o for k in ("field", "call", "imm")):
        print(__doc__); return 1
    segs = E.load_segments(); md = E.md()
    hits = []
    lis = {}   # reg -> (value, addr)
    rx_mem = re.compile(r"(-?(?:0x)?[0-9a-fA-F]+)\((r\d+)\)")
    for base, data in E.code_segments(segs):
        lo, hi = o["rng"] or (base, base + len(data))
        lo = max(lo, base); hi = min(hi, base + len(data))
        if hi <= lo:
            continue
        chunk = data[lo - base: hi - base]
        for ins in E.disasm_all(md, chunk, lo):
            m, op = ins.mnemonic, ins.op_str
            if "field" in o and (m in LOAD or m in STORE):
                if (o["rw"] == "r" and m not in LOAD) or (o["rw"] == "w" and m not in STORE):
                    continue
                mm = rx_mem.search(op)
                if mm and int(mm.group(1), 0) & 0xFFFF == o["field"]:
                    hits.append((ins.address, "R" if m in LOAD else "W", m, op))
            elif "call" in o and m in ("bl", "b") and op.startswith("0x"):
                if int(op, 0) == o["call"]:
                    hits.append((ins.address, "C", m, op))
            elif "imm" in o:
                if m in LOAD or m in STORE:
                    mm = rx_mem.search(op)
                    if mm and mm.group(2) in lis:
                        d = int(mm.group(1), 0) & 0xFFFF
                        d = d - 0x10000 if d >= 0x8000 else d
                        if (lis[mm.group(2)] + d) & 0xFFFFFFFF == o["imm"]:
                            hits.append((ins.address, "R" if m in LOAD else "W", m, op))
                if m == "lis":
                    r, v = [x.strip() for x in op.split(",")]
                    lis[r] = (int(v, 0) & 0xFFFF) << 16
                elif m in ("addi", "ori"):
                    p = [x.strip() for x in op.split(",")]
                    if len(p) == 3 and p[1] in lis:
                        v = int(p[2], 0)
                        val = (lis[p[1]] + (v if m == "ori" else (v - 0x10000 if v >= 0x8000 else v))) & 0xFFFFFFFF
                        if val == o["imm"]:
                            hits.append((ins.address, "I", m, op))
    for ea, k, m, op in hits[: o["max"]]:
        print("%08X %s %-5s %s" % (ea, k, m, op))
    print("-- %d hits%s" % (len(hits), " (capped)" if len(hits) > o["max"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
