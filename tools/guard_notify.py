#!/usr/bin/env python3
"""Hyp. ctxfiber-guard: AD4294 notify loop spins on a zeroed copy-list node. Idempotent patch on generated cpp."""
import sys
from pathlib import Path
p = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated/ppu_recomp_023.cpp")
s = p.read_text(encoding="latin-1")
key = ("        ctx->gpr[9] = ppc_rldicl(ctx->gpr[31], 0, 32);\n"
       "        ctx->gpr[9] = vm_read32(ctx->gpr[9] + 0x0);\n")
hook = ("        if (!(uint32_t)ctx->gpr[31] && getenv(\"GT6_NO_NOTIFYGUARD\") == nullptr) { static int n; if (n++ < 3) fprintf(stderr, \"[GT6] AD4294 guard: null node, leaving loop"+chr(92)+"n\"); ctx->gpr[9] = ctx->gpr[30]; } else\n")
i = s.find("ctx->lr = 0x00AD430C; ps3_indirect_call(ctx); DRAIN_TRAMPOLINE(ctx);\n")
assert i > 0
j = s.find(key, i)
assert j > 0 and j - i < 120
if "AD4294 guard" not in s[i:j + 400]:
    k = j + len(key)
    # keep the load; override r9 after it
    s = s[:k] + hook.replace(" else\n", "\n") + s[k:]
    p.write_text(s, encoding="latin-1")
    print("patched")
else:
    print("already")
