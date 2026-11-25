#!/usr/bin/env python3
"""Workaround (Arbeit35): main.adc (1.22), GameItem.ad addItem, line 277 reads avatar_info.ColorBegin/ColorEnd.
The SPECDB query returns nil on our boot, the script throws and the boot script dies. Replace both reads by
INT_CONST 0 (+ NOP, so the instruction count stays). Writes a NEW file: the overlay entry is a hardlink,
it is unlinked first so the source tree stays untouched.
Usage: patch_adc_colorbegin.py <overlay_dir>"""
import os
import struct
import sys
from pathlib import Path

REL = "scripts/gt6/main.adc"
# (start of VARIABLE_EVAL avatar_info, start of the following ARRAY_PUSH), file offsets, higher one first
SPANS = [(0xEB99F, 0xEB9B9), (0xEB980, 0xEB99A)]
INT_CONST, NOP, VARIABLE_EVAL = 0x0C, 0x17, 0x26

if len(sys.argv) != 2:
    sys.exit(__doc__)
p = Path(sys.argv[1]) / REL
d = bytearray(p.read_bytes())
if all(d[a + 4] != VARIABLE_EVAL for a, _ in SPANS[1:]):
    sys.exit("unexpected bytes (already patched or other version)")
for a, b in SPANS:
    line = bytes(d[a:a + 4])
    assert struct.unpack("<I", line)[0] == 277 and d[a + 4] == VARIABLE_EVAL, "mismatch at 0x%X" % a
    d[a:b] = line + bytes([INT_CONST]) + struct.pack("<i", 0) + line + bytes([NOP])
os.unlink(p)
p.write_bytes(bytes(d))
print("patched", p, len(d))
