#!/usr/bin/env python3
"""Hyp. freeloop-guard: AD4334-AD4350 free loop spins when a node next==0 (null read forever).
Force next=head so the loop ends. Idempotent, EOL-agnostic."""
import sys
from pathlib import Path
p = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated/ppu_recomp_023.cpp")
s = p.read_bytes().decode("latin-1")
eol = "\r\n" if "\r\n" in s[:4000] else "\n"
key = eol.join([
    "loc_00AD4334:",
    "        ctx->gpr[9] = ppc_rldicl(ctx->gpr[3], 0, 32);",
    "        ctx->gpr[3] = ctx->gpr[9] | ctx->gpr[9];",
    "        ctx->gpr[31] = vm_read32(ctx->gpr[9] + 0x0);",
    ""])
hook = ('        if (!(uint32_t)ctx->gpr[31] && getenv("GT6_NO_FREEGUARD") == nullptr) { static int n; '
        'if (n++ < 3) fprintf(stderr, "[GT6] AD4334 free-loop guard: null next, leaving loop' + chr(92) + 'n"); '
        'ctx->gpr[31] = ctx->gpr[30]; }' + eol)
if "free-loop guard" in s:
    print("already")
else:
    assert s.count(key) == 1, s.count(key)
    p.write_bytes(s.replace(key, key + hook).encode("latin-1"))
    print("patched")
