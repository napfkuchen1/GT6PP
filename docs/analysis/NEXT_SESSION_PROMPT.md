Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 1e2ddb2 docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Boot script waits on trophy init + save background load. Make cellSaveData AutoLoad2 sequence -4,-4,ok (oracle: 3 calls) in third_party/ps3recomp-v020 cellSaveData.c (check GT6_SAVE_NODATA knob), run with GT6_PUMP_ITERS=0;A22_BLOCK=1 and watch for sceNpTrophyInit / LoadModule 0xF044 + Presents advance.
Do not repeat: pad presses; dt/time; node flag 1A2; tid27; empty containers; 69098C
Still running: nothing
Read: docs/analysis/STATE.md (last 5 lines)
