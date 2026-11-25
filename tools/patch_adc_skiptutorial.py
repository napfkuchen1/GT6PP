#!/usr/bin/env python3
"""Workaround test (Arbeit40): boot.adc (1.22), start_project_gt6 ins 28 (TutorialUtil.isBegin or skip_tutorial).
Turns JUMP_IF_FALSE 84 into JUMP_IF_TRUE 84: a new game skips the intro tutorial race and starts project gtmode.
Writes a NEW file: the overlay entry is a hardlink, it is unlinked first so the source tree stays untouched.
Usage: patch_adc_skipopening.py <overlay_dir>"""
import os
import struct
import sys
from pathlib import Path

REL = "projects/gt6/boot/boot.adc"
AT = 0x1C9CB  # file offset of the instruction (u8 opcode, i32 target)
JUMP_IF_TRUE, JUMP_IF_FALSE = 14, 15

if len(sys.argv) != 2:
    sys.exit(__doc__)
p = Path(sys.argv[1]) / REL
d = bytearray(p.read_bytes())
if d[AT] != JUMP_IF_FALSE or struct.unpack_from("<i", d, AT + 1)[0] != 84:
    sys.exit("unexpected bytes (already patched or other version)")
d[AT] = JUMP_IF_TRUE
os.unlink(p)
p.write_bytes(bytes(d))
print("patched", p, len(d))
