Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 58205b9 docs: handover; PROGRESS: 2026-11-24 | 94997a5 | notut | ok FAIL - - - - - | probe_a22c1_20261124_172347_1 | non-black=1%
Next step: Presents frame frozen; snapshot diff shows no scene var. Identify Presents scene object (find draw caller via RSX draw 2 ops/frame, e.g. PS3 callstack at first draw_arrays) and its fade/anim state; run with -Env GT6_PUMP_ITERS=0;A22_BLOCK=1 (build has A22_BLOCK; tools/apply_block.py)
Do not repeat: snap diff 60/130s done (no var); ADB780 single target ADB918
Still running: nothing
Read: STATE.md (last 3 lines)
