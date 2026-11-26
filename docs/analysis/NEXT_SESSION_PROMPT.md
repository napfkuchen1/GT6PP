Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 6ea021e fix: parse the real PAMF header layout in cellPamf; record menu pad resu; PROGRESS: 2026-11-26 | 6ea021e | vol | ok FAIL - - - - - | probe_a50deal_20261126_004329_1 | non-black=0%
Next step: Dealer load hang (a50deal): find owner of lwmutex 0x6FF52FF0 that blocks tid30 (AD4294<6166A4); snapshot or watchdog owner print; also r2 stall before menu (tid30 8A7B90). Then I1: real cellDmux + FFmpeg headers.
Do not repeat: SPU stall img5, shredded text, PAMF header parse (fixed), pad popup/dealer press (works)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit50; side note arbeit50-movie.md
