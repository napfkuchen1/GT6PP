Goal: Main menu (C6): find why per-frame task poll of B90 stops (MGOM loop 616C80 spins, polls only first ~100 iters)
State: last commit 8bc544f docs: Arbeit26 task driver loop found, handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Hook 6D968C (616FA0) and vcall at 616FFC in gen 013: per-iter args/ret/target ctr; read 6D968C (gdis --fn) = per-frame project/task update? check if it polls task B90 (A2F860 via 737C60 only in first 100 iters). If yes: find why it skips after load; compare node+0x96 setter 68FDB4.
Do not repeat: 6B7D0C loop is tid1-only (refuted); A2F860/737C60/686C58/68FF84 chain mapped (STATE Arbeit27); hooks A27* in gen 013/014/015/022 (clean copies work/_bk_a26/*_a27pre|clean)
Still running: nothing
Read: docs/analysis/STATE.md
