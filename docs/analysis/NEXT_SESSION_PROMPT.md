Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit d54015c docs: handover findings (heap deadlock after allocation failure); PROGRESS: 2026-11-25 | a080c1b | vol | ok ok FAIL FAIL ok FAIL - | probe_a35wd_20261125_113422_1 | non-black=5%
Next step: 1) Heap deadlock: repeat a35 pad runs until [A35OOM] fires (heap/size/caller), find why alloc fails. 2) Post-SAVE black screen: WD dump after 'SAVE complete'. 3) SettingProjectComponent stall (most common now): PS3_WD_AT=150, read tid1/tid30 chains.
Do not repeat: ColorBegin/PDIPFS AV fixed (STATE Arbeit35); run only -Parallel with probe.ps1 PDIPFS copy.
Still running: nothing
Read: STATE.md Arbeit35 lines; eu-boot-log.md Arbeit35
