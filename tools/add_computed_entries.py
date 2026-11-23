#!/usr/bin/env python3
"""Add the computed-jump entry points of the memset family to a function list.

The memset at 0xB118E0 (1.22; 0xA2F158 switch too) finishes small sizes with a
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

# 1.22 layout (EMAIN 1.22, memset rebuilt: found by scanning bctr + stb/std runs)
# (first entry, last entry, step, end)
GROUPS = [
    (0xB118E0, 0xB1191C, 4, 0xB11920),
    (0xB11968, 0xB119A0, 4, 0xB119B4),
    (0xB119E8, 0xB11A20, 4, 0xB11AE4),
    (0xB11A64, 0xB11A9C, 4, 0xB11AE4),
    # run tails (n == full run): first non-store word after each run
    (0xB119A4, 0xB119A4, 4, 0xB119B4),
    (0xB11A24, 0xB11A24, 4, 0xB11AE4),
    (0xB11AA0, 0xB11AA0, 4, 0xB11AE4),
    # absolute 6-entry switch table at 0x1569DEC (bctr A2F158) not found by the lifter
    (0xA2F100, 0xA2F100, 4, 0xA2F288),
    (0xA2F15C, 0xA2F15C, 4, 0xA2F288),
    (0xA2F174, 0xA2F174, 4, 0xA2F288),
    (0xA2F250, 0xA2F250, 4, 0xA2F288),
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
