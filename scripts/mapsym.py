#!/usr/bin/env python3
"""Resolve host addresses against gt6.map (MSVC /MAP).

Usage: python scripts/mapsym.py <gt6.map> <backtrace.txt> [--base 0x...]
Reads "frame #N: 0x<addr>" lines (lldb) and prints symbol+offset plus the
distance to the previous (outer) frame is not known to lldb, so none is shown.
Without --base the load address is taken from the "image list" line.
"""
import bisect
import re
import sys


def load_map(path):
    syms, preferred = [], 0x140000000
    rx = re.compile(r"^\s*[0-9a-f]{4}:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{16})\s")
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "Preferred load address is" in line:
                preferred = int(line.split()[-1], 16)
            m = rx.match(line)
            if m:
                rva = int(m.group(2), 16) - preferred
                if rva >= 0:
                    syms.append((rva, m.group(1)))
    syms.sort()
    return syms


def main():
    syms = load_map(sys.argv[1])
    keys = [s[0] for s in syms]
    text = open(sys.argv[2], encoding="utf-8", errors="replace").read()
    if "--base" in sys.argv:
        base = int(sys.argv[sys.argv.index("--base") + 1], 16)
    else:
        base = int(re.search(r"\[ *0\] \S+ (0x[0-9a-f]+)", text).group(1), 16)
    seen = set()
    for num, addr in re.findall(r"frame #(\d+): (0x[0-9a-f]+) gt6\.exe", text):
        if num in seen:
            continue
        seen.add(num)
        rva = int(addr, 16) - base
        i = bisect.bisect_right(keys, rva) - 1
        name = "%s+0x%X" % (syms[i][1], rva - syms[i][0]) if i >= 0 else "?"
        print("#%s %s" % (num, name))


if __name__ == "__main__":
    main()
