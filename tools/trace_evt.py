#!/usr/bin/env python3
"""Diagnostic (Arbeit22): trace event wait AE2844 from 6171FC (lr 617218) and every AE2890 (event set) on the same object.
Applied to generated ppu_recomp_023.cpp; restore from work/_bk_a22 afterwards. Idempotent."""
import sys
from pathlib import Path
p = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated/ppu_recomp_023.cpp")
s = p.read_bytes().decode("latin-1")
if "A22EVT" in s:
    print("already"); sys.exit(0)
def ins(fn, hook, after="PPU_MM_SNAP"):
    global s
    i = s.find("void " + fn + "(ppu_context* ctx) {")
    assert i > 0, fn
    j = s.find(after, i) + len(after)
    s = s[:j] + chr(10) + hook + s[j:]
g = "static uint32_t g_a22evt;" + chr(10)
i = s.find("void func_00AE2844(ppu_context* ctx) {")
s = s[:i] + g + s[i:]
ins("func_00AE2844", '        if ((uint32_t)ctx->lr == 0x00617218u) { g_a22evt = (uint32_t)ctx->gpr[3]; fprintf(stderr, "[A22EVT] wait enter obj=%08X\\n", g_a22evt); }')
ins("func_00AE2890", '        { static int n; if (g_a22evt && (uint32_t)ctx->gpr[3] == g_a22evt && n++ < 40) fprintf(stderr, "[A22EVT] SET obj=%08X lr=%08X sp=%08X\\n", (uint32_t)ctx->gpr[3], (uint32_t)ctx->lr, (uint32_t)ctx->gpr[1]); }')
k = "ctx->lr = 0x00AE2870; func_00AE27AC(ctx); DRAIN_TRAMPOLINE(ctx);"
i = s.find("void func_00AE2844(ppu_context* ctx) {")
j = s.find(k, i) + len(k)
assert j > len(k)
s = s[:j] + chr(10) + '        if (g_a22evt && (uint32_t)ctx->gpr[29] == g_a22evt) fprintf(stderr, "[A22EVT] wait EXIT obj=%08X sp=%08X" "\\n", g_a22evt, (uint32_t)ctx->gpr[1]);' + s[j:]
p.write_bytes(s.encode("latin-1")); print("patched")
