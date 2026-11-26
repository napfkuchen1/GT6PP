Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 8922086 perf: add indirect-only SPU job entries; interpreter at 0.4M steps/s in ; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: S3 0/3, total without check-off 0/6, boxes done 8.
Next step: M1 next item: G6 (car view black, no 3D car): capture draws there and find why the car/background is missing. Repro work/_a55/repro.sh (boot to car view); buy: cross (color), down x3, cross, cross; delivery ~3 min. If G6 stalls, take I1 (opening movie).
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: LEDGER A55: slowness was unlifted WWS job modules (fixed); interpreter no longer the bottleneck (0.4M steps/s).
Still running: nothing
Read: STATE.md, LEDGER.md (grep A55)
