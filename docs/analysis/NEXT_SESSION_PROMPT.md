Goal: Main menu (C6).
State: last commit = Arbeit17 commit (guard_conswait); PROGRESS: 2026-11-24 | probe_arb17_conswait_20261124_114217_1 | notut | consumer-wait guard 8A7AD0 fires, no load progress (no PDIPFS/59/FI, Pamf, Vdec).
Next step: snapshot diff guard run vs baseline (scripts/snap_diff.py, work/probe_arb17_conswait_20261124_114217_1 vs work/probe_a15loop_20261124_110206_1, ~140 s). Decision rule: if the consumer wait is passed but no producer/job progress -> find the first game-level wait after loading (snap_walk.py); if no difference -> change strategy (workaround for the next wait only after its guard shows no effect).
Do not repeat: LEDGER §4; Save/Term/NP; 146E8 forcing; 798C1C force; xref --field on 0x1d8/0x240 without --in; 8A7AD0 consumer guard alone (Arbeit17).
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail: Arbeit16, Arbeit17); tools/guard_conswait.py.
