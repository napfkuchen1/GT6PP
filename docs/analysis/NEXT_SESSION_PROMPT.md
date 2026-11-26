Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 44920e0 fix: defer release of GPU resources used by the open command list (devic; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: C2 0/3, total without check-off 0/6, boxes done 5.
Next step: S3/D3: ripsample shows SPU interpreter (spu_interp_run_until < pm_clean_spu_func_00001A30) dominating; find interpreted LS ranges and why no lifted code matches, lift or cache lookup; then check delivery screen ends and G1. Repro: play.py start; sh work/_a53/to_home2.sh; python -I work/_a53/dealer.py; cross, cross. New item: pick S3.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: LEDGER A54: car-view TDR was a freed upload buffer (fixed, 44920e0), not a shader/draw.
Still running: nothing
Read: STATE.md, LEDGER.md (grep A54)
