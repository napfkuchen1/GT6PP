#!/usr/bin/env python3
"""Workaround (Arbeit34/35): func_00AE6388 zeroes the 8-byte items in [*(obj+8), *(obj+0xC)-8). The caller CD2ABC
hands it NULL entries from a corrupted vector, so it wipes guest memory from the NULL page up to the TOC
(later symptom: fflush recursion, 0xC00000FD). Guard: skip the call if the range is implausible. Logs [A34G].
Idempotent, EOL-agnostic. Applied to the generated cpp by post-lift.ps1.
Usage: guard_ringzero.py [generated_dir]"""
import sys
from pathlib import Path

HEAD = "void func_00AE6388(ppu_context* ctx) {"
MARK = "[A34G]"
GUARD = [
    "        { uint32_t o = (uint32_t)ctx->gpr[3];   /* A34 guard: bad range wipes guest memory */",
    "          uint32_t b = o >= 0x10000u ? vm_read32(o + 8) : 0u, e = o >= 0x10000u ? vm_read32(o + 12) : 0u;",
    "          if (b < 0x10000u || e < b || e - b > 0x01000000u) { static int n = 0; if (n++ < 20)",
    '              fprintf(stderr, "[A34G] skip AE6388 obj=%08X begin=%08X end=%08X lr=%08X' + chr(92) + 'n", o, b, e,',
    "                  (uint32_t)ctx->lr);",
    "              return; } }",
]

gen = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated")
for p in sorted(gen.glob("ppu_recomp_*.cpp")):
    s = p.read_bytes().decode("latin-1")
    i = s.find(HEAD)
    if i < 0:
        continue
    eol = "\r\n" if "\r\n" in s[:4000] else "\n"
    end = s.find(eol + "}" + eol, i)
    assert end > 0, "end of func_00AE6388 not found"
    if MARK in s[i:end]:
        print("already", p.name)
        sys.exit(0)
    anchor = "PPU_MM_SNAP" + eol
    j = s.find(anchor, i, end)
    at = j + len(anchor) if j > 0 else i + len(HEAD) + len(eol)
    s = s[:at] + eol.join(GUARD) + eol + s[at:]
    p.write_bytes(s.encode("latin-1"))
    print("patched", p.name)
    sys.exit(0)
sys.exit("func_00AE6388 not found in " + str(gen))
