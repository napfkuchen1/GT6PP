#!/usr/bin/env python3
"""Fill the file cache in func_00B5B260 (EU boot 2 with an existing userdb).

func_00B5B260 allocates the cache buffer (size = (filesz+0xFFFF)&~0xFFFF) after
the A26510 call but nothing fills it. B5B028 then reads a zero buffer, SQLite
returns SQLITE_NOTADB for the existing 8 MB userdb0101.dat and the game shows
"Nicht genuegend Speicherplatz". The fix routes the success path through a block
that calls func_00B5A944 + func_00F7666C (same pair the game uses to read the
file into the buffer) before continuing at loc_00B5B838.

Fails loudly if the anchors are missing (changed lift output). Idempotent.
Re-run after every relift (relift-gt6.ps1 does).

Usage:
    python tools/b5b260_cache_fill_patch.py gt6/generated
"""
from __future__ import annotations

import sys
from pathlib import Path

FUNC = "func_00B5B260"
MARK = "loc_FILL_B5B838"
CALL = "ctx->lr = 0x00B5B734; func_00A26510(ctx); DRAIN_TRAMPOLINE(ctx);"
BRANCH = "if ((!((ctx->cr >> 1) & 1))) goto loc_00B5B838;"
TAIL_LABEL = "loc_00B5B754:"  # lifter output mixes LF/CRLF: no newline in the anchor
FILL = (
    "loc_FILL_B5B838:\n"
    "        { uint32_t _o=(uint32_t)ctx->gpr[30]; uint32_t _b=vm_read32(_o+0x28); uint32_t _s=vm_read32(_o+0x30);\n"
    "          if(_b && _s){\n"
    "            ctx->gpr[3]=_o; ctx->gpr[4]=0; ctx->lr=0x00B5B740; func_00B5A944(ctx); DRAIN_TRAMPOLINE(ctx);\n"
    "            ctx->gpr[3]=_o; ctx->gpr[4]=_b; ctx->gpr[5]=_s; ctx->lr=0x00B5B740; func_00F7666C(ctx); DRAIN_TRAMPOLINE(ctx);\n"
    "          } }\n"
    "        goto loc_00B5B838;\n"
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    hits = 0
    for path in sorted(Path(argv[1]).glob("ppu_recomp_*.cpp")):
        text = path.read_bytes().decode("latin-1")
        start = text.find(f"void {FUNC}(ppu_context* ctx)")
        if start < 0:
            continue
        hits += 1
        end = text.find("\nvoid func_", start + 20)
        end = len(text) if end < 0 else end
        body = text[start:end]
        if MARK in body:
            print(f"{path.name}: {FUNC} already patched")
            continue
        c = body.find(CALL)
        b = body.find(BRANCH, c) if c >= 0 else -1
        t = body.find(TAIL_LABEL, b) if b >= 0 else -1
        if body.count(CALL) != 1 or b < 0 or t < 0:
            print(f"{path.name}: anchors for {FUNC} not found (call={body.count(CALL)} "
                  f"branch={b >= 0} tail={t >= 0}); lift output changed", file=sys.stderr)
            return 1
        seg = body[b:t]
        if seg.count("goto loc_00B5B838;") != 2:
            print(f"{path.name}: unexpected branch layout in {FUNC}", file=sys.stderr)
            return 1
        seg = seg.replace(BRANCH, BRANCH.replace("loc_00B5B838", MARK), 1)
        body = body[:b] + seg + FILL + body[t:]
        path.write_bytes((text[:start] + body + text[end:]).encode("latin-1"))
        print(f"{path.name}: patched {FUNC} cache fill")
    if hits != 1:
        print(f"expected exactly one {FUNC}, found {hits}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
