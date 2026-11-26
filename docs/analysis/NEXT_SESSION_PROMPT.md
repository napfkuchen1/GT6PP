Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 9c3cd2c fix: answer every demux stream reset with DEMUX_DONE so the movie teardo; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: I1 0/3, total without check-off 0/6, boxes done 15.
Next step: I2: boot with opening movie and without tutorial-skip overlay (gt6_vol_a32/a35 instead of a40t) via scripts/play.py; if it stalls: dump --snap, snap_walk bt, fix; if it reaches the menu: check off I2 with frame
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: A63: I1b/I1c solved (AVC frameRateCode, DEMUX_DONE); decode speed is not a problem (LEDGER §4)
Still running: nothing
Read: STATE.md, eu-boot-log.md Arbeit40 (grep tutorial)
