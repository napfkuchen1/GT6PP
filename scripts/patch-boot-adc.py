"""Bypass first-boot gates in work/gt6_vol/projects/gt6/boot/boot.adc (data patch, 1 byte each).
Usage: python -I scripts/patch-boot-adc.py [lang] [adjust] [tutorial]   (default: all)
Original saved as work/ARCHIV/boot.adc.orig (restore = copy back). Offsets from work/boot_adc.txt.
"""
import sys
P = 'work/gt6_vol/projects/gt6/boot/boot.adc'
d = bytearray(open(P, 'rb').read())
want = set(sys.argv[1:]) or {'lang', 'adjust', 'tutorial'}
if 'lang' in want:      # LanguageSelectRoot.open only if langs.size > 99 (never)
    for o in (0x18924, 0x196D6):
        assert d[o] == 0x0c and d[o+1:o+5] == b'\0\0\0\0' or d[o+1] == 99; d[o+1] = 99
if 'adjust' in want:    # skip AdjustScreenRoot: JUMP_IF_FALSE(15) -> JUMP_IF_TRUE(14)
    assert d[0x18A69] in (14, 15); d[0x18A69] = 14
if 'tutorial' in want:  # skip intro tutorial race -> TutorialUtil.done + startProject("gtmode")
    assert d[0x18FDA] in (14, 15); d[0x18FDA] = 14
open(P, 'wb').write(d); print('patched', sorted(want), len(d))
