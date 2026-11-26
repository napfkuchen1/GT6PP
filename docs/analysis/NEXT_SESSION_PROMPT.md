Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit c465f62 fix: loop guard (parked items, blocker after 6 sessions), STATE trim kee; PROGRESS: 2026-11-26 | c465f62 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51fix_20261126_013431_1 | non-black=81%
Loop: C1 1/3, total without check-off 1/6, boxes done 2.
Next step: Run rebuilt exe (old p3 flush guard removed, no env) with a51deal pad script, -Seconds 1100 -Parallel 2, RSX_CAP past 27000: expect 0 [LWM-LONG], tid6 alive; if dealer still loading, walk tid30 chain (6752E0<67D140<6C7664<7B51B8) over WD samples; second stall before menu: tid30 AD321C<AD555C<8A7B90.
Do not repeat: 6FF52FF0 lock (stale WD register); dealer deadlock cause fixed (AC75B0 guard)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit51
