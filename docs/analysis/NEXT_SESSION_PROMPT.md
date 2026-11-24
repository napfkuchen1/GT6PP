Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 60b588c docs: handover; PROGRESS: 2026-11-24 | 60b588c | notut | ok FAIL - - - - - | probe_a22pad_20261124_174006_1 | non-black=1%
Next step: Presents frame frozen (dim text, no change with pad). Identify Presents scene object + fade state: find draw caller of the 2 text draws/frame, read its alpha/time vars; run -Env GT6_PUMP_ITERS=0;A22_BLOCK=1 (tools/apply_block.py)
Do not repeat: snap diff 60/130s (no var); pad press no effect; main-exit chain
Still running: nothing
Read: STATE.md (last 3 lines)
