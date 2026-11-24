Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit 2bd1f80 docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Trace 8146B8 (MSaveDataUtil poll native; vcall obj+0xC then 89D59C -> bool) + 815ED4/815BDC returns via tools/trace_enter-like r3 log; boot script stalls in checkGameData (l80). A22_BLOCK patch re-created in generated ppu_recomp_016 (copy work/_bk_a22/ppu_recomp_016_blockpatched.cpp); calltrace: PS3_CALLTRACE_LR=A74734, grep '^\[CALL\] ->'
Do not repeat: MGOM node state 0x144; PDINetwork/Trophy natives (stall earlier); pad presses
Still running: nothing
Read: docs/analysis/STATE.md (last 6 lines)
