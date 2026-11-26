Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 1b2a269 fix: lift interpreter jump tables with a hidden table base; keep call de; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: C1 1/3, total without check-off 1/6, boxes done 2.
Next step: Run a51jt command as a52deal: -Seconds 1500, RSX_CAP=25000:30:2000, PS3_WD_AT=700,900,1100,1300,1480. If dealer still loading, compare tid30/tid27 chains + last file opens across samples; moving = slow, fixed = walk the wait. S1: who patches the FIFO self-JUMP before label 0x53.
Do not repeat: GCM_PARK_GRACE_MS above 30 s (SPU guard fires first)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit51 part 2
