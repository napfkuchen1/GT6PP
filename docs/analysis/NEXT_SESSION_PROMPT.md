Goal: Main menu (C6).
State: last commit = Arbeit17 commit (guard_conswait); PROGRESS: 2026-11-24 | probe_arb17_conswait_20261124_114217_1 | notut | consumer-wait guard 8A7AD0 fires, no load progress (no PDIPFS/59/FI, Pamf, Vdec).
Next step: PS3_SNAP_AT never fires (3 runs, eu-boot-log Arbeit17). Fix arming: ppu_loader.cpp:3581 (lv2_syscall) or trigger the snapshot via watchdog thread; then snap_diff (guard run vs a15loop). Decision rule: no snapshot after fix -> skip snapshot, go to first game-level wait after loading.
Do not repeat: LEDGER §4; Save/Term/NP; 146E8 forcing; 798C1C force; 8A7AD0 guard alone (Arbeit17); parallel probe.ps1 runs (taskkill kills each other); PS3_SNAP_AT as is.
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail: Arbeit16, Arbeit17); tools/guard_conswait.py.
