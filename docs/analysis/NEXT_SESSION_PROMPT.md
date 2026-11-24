Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit 9e9d155 docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Boot script task never resumes after SaveDataUtilGT6.loadEveryWhereForGame (l94; load itself completes): find script-task resume mechanism (A2F290/A2EA5C state machine, SET_STATE yield) and why tid30 pump does not run the task; A22_BLOCK patch in generated 016 (copy work/_bk_a22/ppu_recomp_016_blockpatched.cpp); calltrace: PS3_CALLTRACE_LR=A74734 grep '^\[CALL\] ->'; boot script dump python -I -X utf8 tools/adch_disasm.py work/gt6_vol/projects/gt6/boot/boot.adc
Do not repeat: MGOM node state 144; PDINetwork/Trophy natives; load completion (done); pad presses
Still running: nothing
Read: docs/analysis/STATE.md (last 6 lines)
