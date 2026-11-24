Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit b07be6e docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Get 1.22 plaintext boot.adc/main.adc: decrypt PDIPFS overlay (work/gt6_hdd0_rp) via tools/gt6_pfs_*.py + GT6_PFS_KEYMAP (stubs.cpp l190-420), replace gt6_vol 1.00 scripts (backup first), run probe -Boot orig Env A22_BLOCK=1;A29_JMP=1, expect no [A29E] errors; if keymap/decrypt missing, diff 1.00 vs 1.22 module list as mismatch proof
Do not repeat: A29: MMuseum2 NameError (1.00 script vs 1.22 ELF) triggers node-start flush; GT6_PFS_OVERRIDE=0 stalls
Still running: nothing
Read: STATE.md (last 3 lines)
