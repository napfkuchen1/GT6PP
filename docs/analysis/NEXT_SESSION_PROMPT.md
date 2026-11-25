Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit d089493 fix: pin guest PPU threads to one host core (boot race), guest stores ho; PROGRESS: 2026-11-25 | 4093277 | vol | ok FAIL - - - - - | probe_a32see_20261125_095738_1 | non-black=1%
Next step: Binary default PPU_ONECORE=1 (boot race gone). 1) Capture a pinned run (probe -Frame, -Seconds 200) to see how far the image gets. 2) 3/8 runs wait at SettingProjectComponent.gpb at 60 fps: PS3_WD_AT=90, find tid1 wait (monitor A4FBE8). 3) 0xC00000FD = fflush(NULL) C59350: read the 3 FILE* (r2-0x6F4C..44) and r2, find caller (C52C80/A444A4); if NULL, guard like gt6_purecall.
Do not repeat: PPU_RESV_STORE (1/6), PPU_PRIO_MAP (no gain), map-walk race (solved by PPU_ONECORE).
Still running: nothing
Read: STATE.md Arbeit33 lines; eu-boot-log.md Arbeit33; scripts/boot-batch.ps1
