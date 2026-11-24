Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit a341c1e Arbeit22: tools/apply_block.py (main blocks after MGOM.start, env A22_BL; PROGRESS: 2026-11-24 | 94997a5 | notut | ok FAIL - - - - - | probe_a22c1_20261124_172347_1 | non-black=1%
Next step: Presents frame frozen (frame 2000..14000 identical). Build has A22_BLOCK patch (run -Env GT6_PUMP_ITERS=0;A22_BLOCK=1; tools/apply_block.py re-applies after lift). Find what scene waits for: snapshot diff of MGOM/scene objects 60s vs 120s, or next-project load request
Do not repeat: A2F290 force2; main exit chain; vblank/timebase fine
Still running: nothing
Read: STATE.md (last 3 lines)
