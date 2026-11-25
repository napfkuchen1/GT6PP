Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit ab8c54a fix: probe early-kill timing, add guest backtrace to snap_walk; handover; PROGRESS: 2026-11-25 | 148db74 | vol | ok ok FAIL FAIL ok FAIL - | probe_a39h_20261125_133715_2 | non-black=81%
Next step: Post-save black: boot script should run MovieRoot (t_movie OPENING -> .pam, Tv2.decodeContentsKey, load; wait isFinished). Find which native is reached (env-gated hook, python -X utf8 tools/adch_disasm.py boot.adc). If load/pamf stubbed or stuck: force end_movie/skipOpening workaround -> next screen; if movie never reached: trace applySaveData/BackupSave step.
Do not repeat: Heap corruption fixed; save completes 4/4; no script throw; MGOM wait/loop 616C80 is normal ticking
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit39
