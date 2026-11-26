Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 6cda99e feat: play.py interactive control of one running game, on-demand watchdo; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: C1 2/3, total without check-off 2/6, boxes done 2.
Next step: Dealer: walk work/play_a52c_*/snap_00539 tid30 (interpreter 1FA204/1FA968, stack names GT-ALL, leavedemo); several play.py dump samples: constant outer frame = loop owner. If loop over car DB rows: check rc/row count, else find exit condition. S1 after.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: dealer hang is not a blocked wait / lost wakeup (tid30 runs script code, no file opens); boot via timed probe for menu questions
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit52
