Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 99db830 fix: wait longer on FIFO parks, scale depth-surface textures by host siz; PROGRESS: 2026-11-26 | 99db830 | vol | ok ok FAIL FAIL ok FAIL - | probe_a49menu_20261126_002007_2 | non-black=81%
Next step: C1/G1: probe -Parallel 2 -Seconds 700, GT6_VOL_ROOT=work/gt6_vol_a45, same pad + X/dir presses after 470 s, RSX_CAP=23000:40:301; popup close, dealer tile, stacked banner; then I1 movie without skipopening
Do not repeat: SPU stall img5 (fixed, park grace); shredded text (fixed, ds texscale); GCM_SEMA_ACQUIRE
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit49
