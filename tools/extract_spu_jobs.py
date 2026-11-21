#!/usr/bin/env python3
"""Cut the raw SPURS job images out of the decrypted EMAIN.elf.

The 15 job binaries GT6 hands to spu_workload_dispatch_job() are plain byte
ranges of EMAIN.elf. scripts/spu-jobs-manifest.json lists fingerprint, size and
file offset of each; every slice is checked against the runtime fingerprint
(FNV-1a-64, basis 1469598103934665603) before spujob_<FP>_<size>.bin is written.
An existing dump with identical bytes is left alone; a differing one is an error.

Usage:
    python tools/extract_spu_jobs.py work/bin/EMAIN.elf work/spu_jobs/dump
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "scripts" / "spu-jobs-manifest.json"


def fnv(b: bytes) -> int:
    h = 1469598103934665603
    for x in b:
        h = ((h ^ x) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    elf = Path(argv[1]).read_bytes()
    out = Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for e in json.loads(MANIFEST.read_text()):
        b = elf[e["offset"]:e["offset"] + e["size"]]
        fp = f"{fnv(b):016X}"
        if len(b) != e["size"] or fp != e["fp"]:
            print(f"{e['fp']}: slice at 0x{e['offset']:X} has fp {fp}, size {len(b)}; "
                  "EMAIN.elf differs from the manifest", file=sys.stderr)
            return 1
        dst = out / f"spujob_{fp}_{e['size']}.bin"
        if dst.exists():
            if dst.read_bytes() != b:
                print(f"{dst.name}: exists with different content", file=sys.stderr)
                return 1
            print(f"{dst.name}: ok (present)")
        else:
            dst.write_bytes(b)
            print(f"{dst.name}: written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
