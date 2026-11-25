#!/usr/bin/env python3
"""Workaround (Arbeit35/36): AB-BA deadlock between the heap locks 017B4BD8 (heap list) and 017B4C08 (recovery).
func_00B04CD8 (purge walk over all heaps) takes BD8 and then C08 per heap (func_00B08728); the allocation-failure
path of operator new (B0CCAC -> B08498) holds C08 and then calls func_00B04CD8. Guard: take C08 (recursive lwmutex,
1 ms timeout) before BD8; skip the optional walk if another thread owns it. Logs [A36HL].
Idempotent, EOL-agnostic. Applied to the generated cpp by post-lift.ps1.
Usage: guard_heaplock.py [generated_dir]"""
import sys
from pathlib import Path

HEAD = "void func_00B04CD8(ppu_context* ctx) {"
MARK = "[A36HL]"
LOCK = [
    "        { uint64_t lr = ctx->lr;   /* A36 guard: lock order C08 -> BD8 */",
    "          ctx->gpr[3] = 0x017B4C08u; ctx->gpr[4] = 1000; func_010C0CD0(ctx); DRAIN_TRAMPOLINE(ctx);",
    "          ctx->lr = lr;",
    "          if ((uint32_t)ctx->gpr[3] != 0u) { static int n = 0; if (n++ < 20)",
    '              fprintf(stderr, "[A36HL] skip heap walk tid=%llu lr=%08X rc=%08X' + chr(92) + 'n",',
    "                  (unsigned long long)ctx->thread_id, (uint32_t)lr, (uint32_t)ctx->gpr[3]);",
    "              return; } }",
]
UNLOCK = "        ctx->gpr[3] = 0x017B4C08u; func_010C0D08(ctx); DRAIN_TRAMPOLINE(ctx);   /* A36 guard unlock */"

gen = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated")
for p in sorted(gen.glob("ppu_recomp_*.cpp")):
    s = p.read_bytes().decode("latin-1")
    i = s.find(HEAD)
    if i < 0:
        continue
    eol = "\r\n" if "\r\n" in s[:4000] else "\n"
    end = s.find(eol + "}" + eol, i)
    assert end > 0, "end of func_00B04CD8 not found"
    body = s[i:end]
    if MARK in body:
        print("already", p.name)
        sys.exit(0)
    anchor = "PPU_MM_SNAP" + eol
    j = body.find(anchor)
    at = j + len(anchor) if j >= 0 else len(HEAD) + len(eol)
    body = body[:at] + eol.join(LOCK) + eol + body[at:]
    rel = "func_00B038EC(ctx); DRAIN_TRAMPOLINE(ctx);" + eol
    k = body.find(rel)
    assert k > 0 and body.count(rel) == 1, "list unlock call not found"
    k += len(rel)
    body = body[:k] + UNLOCK + eol + body[k:]
    s = s[:i] + body + s[end:]
    p.write_bytes(s.encode("latin-1"))
    print("patched", p.name)
    sys.exit(0)
sys.exit("func_00B04CD8 not found in " + str(gen))
