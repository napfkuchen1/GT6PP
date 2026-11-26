Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit e642c41 docs: handover note on lock owner logging; PROGRESS: 2026-11-26 | 6ea021e | vol | ok FAIL - - - - - | probe_a50deal_20261126_004329_1 | non-black=0%
Next step: a50deal hang: rerun with PS3_LWMUTEX_TRACE=1;PS3_LWM_WATCH=0x6FF52FF0 (-Seconds 700, X 560..620), find [LWM-CONVOY] holder of the lock tid30 waits on; walk that thread. Also r2 stall before menu (tid30 8A7B90). Then I1: real cellDmux + FFmpeg headers.
Do not repeat: SPU stall img5, shredded text, PAMF header parse (fixed), pad popup/dealer press (works)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit50; side note arbeit50-movie.md
