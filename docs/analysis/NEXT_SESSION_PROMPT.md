Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 61bb488 docs: handover; PROGRESS: 2026-11-25 | 61bb488 | vol | ok ok FAIL FAIL ok FAIL - | probe_a34cap_20261125_110401_2 | non-black=5%
Next step: 1) Who zeroes vector 6FFFE910 (obj 619E0000+0x3C55C, entries NULL in CD2ABC): static: push/clear sites (caller 920720, 9206A8); run GT6_GUARD=6fffe910:6fffe910; check heap overlap/alias of 6FFFxxxx. Persist guard [A34G] (gen 023 AE6388) via post-lift or fix cause. 2) Script blocker: main.adc GameItem.ad l275 (nil).ColorBegin on every Presents run: bypass = new overlay with COPY of main.adc (break hardlink), JUMP_IF_FALSE(0x0F) at file 0xEB893 -> JUMP(0x0D), target 48; then look for next error / find why SPECDB AVATAR_* row is missing.
Do not repeat: 0xC00000FD = fflush symptom (root: TOC wipe by AE6388, solved by guard); PPU_RESV_STORE/PRIO_MAP; PS3_WD for the legal screen hang before fixing ColorBegin.
Still running: nothing
Read: STATE.md Arbeit34 lines; eu-boot-log.md Arbeit34; scripts/probe.ps1 (line ranges)
