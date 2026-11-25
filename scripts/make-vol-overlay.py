#!/usr/bin/env python3
"""Build a volume overlay from hardlinks: newer tree first, base tree fills the gaps.

Usage: python scripts/make-vol-overlay.py <base> <update> <dest>
No data is copied. Files in <dest> share storage with the sources: never write
into <dest> in place (that would modify the source tree).
"""
import os
import sys


def link_tree(src, dst):
    linked = skipped = 0
    for base, _, files in os.walk(src):
        out = os.path.join(dst, os.path.relpath(base, src))
        os.makedirs(out, exist_ok=True)
        for name in files:
            target = os.path.join(out, name)
            if os.path.exists(target):
                skipped += 1
                continue
            os.link(os.path.join(base, name), target)
            linked += 1
    return linked, skipped


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    base, update, dest = sys.argv[1:]
    for d in (base, update):
        if not os.path.isfile(os.path.join(d, "VER_INFO")):
            sys.exit("not a volume tree (no VER_INFO): " + d)
    if os.path.exists(dest):
        sys.exit("destination already exists: " + dest)
    print("update: linked %d, skipped %d" % link_tree(update, dest))
    print("base:   linked %d, shadowed by update %d" % link_tree(base, dest))


if __name__ == "__main__":
    main()
