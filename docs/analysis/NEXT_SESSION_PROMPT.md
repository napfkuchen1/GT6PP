Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 1ece32b fix: stamp audio port timestamps with the time of the last read index ad; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: I1 1/3, total without check-off 1/6, boxes done 13.
Next step: I1b: find who releases video frame ring slots (player 624007D0 +0x78, ring full 4/4; callers of 8A9AA0 at 8AB8B0/8AB970/8AC0F4) and its clock in snap_00248 (eu-boot-log A62); if decode is only too slow, time ms/picture in cellVdec
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: A62: freeze is not the audio port clock (stamps fixed, feeder runs, freeze unchanged; LEDGER §4)
Still running: nothing
Read: STATE.md, eu-boot-log.md section A62 (grep)
