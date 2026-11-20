#!/usr/bin/env python3
"""Add the computed-jump entry points of the memset family to a function list.

The memset at 0xA4FDBC (and the 0xA4FEE8 tail) finishes small sizes with a
Duff's-device jump: it loads a base address, subtracts `4 * n` (or `n / 2` for
the 8-byte store run) and does `mtctr` / `bctr` into the middle of a run of
`stb` / `std` instructions. The lifter's jump-table pass only knows table
based switches, so these targets are never discovered. At run time every such
call ends in `unresolved indirect call -> 0x00A4FDE0..0x00A4FF24` and the
memset silently stops before its tail bytes are written.

The entry addresses are fixed by the disassembly, so they are listed here
explicitly. Each one runs to the shared `blr` (or, for the last group, to the
end of the 0xA4FEE8 function) and is appended as its own function. Existing
entries are left alone; running the script twice does nothing the second time.

    python tools/add_computed_entries.py work/analysis/emain/functions_corrected.json
"""
import json
import sys

# (first entry, last entry, step, end)
GROUPS = [
    # lis 0xA5 / addi -0x1e4 / subf n*4  ->  stb r4,0xe(r6) ... stb r4,0(r6); blr
    (0xA4FDE0, 0xA4FE1C, 4, 0xA4FE20),
    # lis 0xA5 / addi -0x15c / subf n/2  ->  std r4,0x70(r6) ... add; addi; stdx; blr
    (0xA4FE68, 0xA4FEA4, 4, 0xA4FEB4),
    # lis 0xA5 / addi -0xdc  / subf n/2  ->  second run inside func_00A4FEE8
    (0xA4FEEC, 0xA4FF24, 4, 0xA4FFAC),
]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as fh:
        funcs = json.load(fh)
    have = {int(f["start"], 16) for f in funcs}
    added = 0
    for lo, hi, step, end in GROUPS:
        for a in range(lo, hi + 1, step):
            if a in have:
                continue
            funcs.append({"start": "0x%08X" % a, "end": "0x%08X" % end})
            have.add(a)
            added += 1
    funcs.sort(key=lambda f: int(f["start"], 16))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(funcs, fh, indent=1)
    print("added %d computed-jump entries (%d functions total)" % (added, len(funcs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
