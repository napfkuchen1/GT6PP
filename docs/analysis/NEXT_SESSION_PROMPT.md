Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 0686f53 fix: honour semaphore acquire for display-list labels 0x500-0x55F; env-g; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: C2 1/3, total without check-off 1/6, boxes done 3.
Next step: Disassemble C4797C/C479E8 (tid30 null object, precedes park 1A6A5F0) and callers; fix producer; repro: play.py start --env GCM_PARKTRACE=1, to_home2.sh, dealer.py.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: GCM_SEMA_ACQUIRE=1 globally (label 0xFE0); hunting the 0x530 releaser (done, LEDGER A54).
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit54
