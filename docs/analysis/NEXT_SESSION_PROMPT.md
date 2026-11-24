Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 3d167b3 docs: handover; PROGRESS: 2026-11-24 | 60b588c | notut | ok FAIL - - - - - | probe_a22pad_20261124_174006_1 | non-black=1%
Next step: Verify empty scene tree: PPU_WWATCH on node1 6FF42AB0+0x30 (len 0x10) env GT6_PUMP_ITERS=0;A22_BLOCK=1 to see who ever writes node map; if none -> find caller that should attach project items (project load completion callback after gpb loads). Also check if RSX draws are stale (frame hash same with draw-count 2).
Do not repeat: pad presses; dt/time (ok); tid27/F7AF20; 69098C deep read; 402F0F90 sentinel (reused heap)
Still running: nothing
Read: docs/analysis/STATE.md (last 8 lines)
