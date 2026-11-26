Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 1267aab docs: handover; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: C1 0/3, total without check-off 0/6, boxes done 3.
Next step: C2/S1: repro (play.py start; sh work/_a53/to_home2.sh; python -I work/_a53/dealer.py). Find jumper to io 146A084, patcher of ea 0x6146A08C, releaser of label 0x53 (write watch, SEMA log off 0x530, SPU img 5 pc 0x7C44 wait value). If runtime drops the release: fix there.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: dealer hang = attract demo (done); GCM_SEMA_ACQUIRE=1 unusable
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit53; cellGcmSys.c 2744-2797
