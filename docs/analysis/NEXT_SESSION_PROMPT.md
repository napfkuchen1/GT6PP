Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit c48e1f1 docs: Arbeit25 project class; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Project class vt 15B31E0 (update slot 0x178=6A68C0); 5 instances in snap_83435343 (6FF38200,6FF38600,6FF39400,6FF86E00,6FF87800): snap_walk obj each, find the one owning boot task B90 40393B90 and why its per-frame update (node tree 6B7C48) is not called after wait-resume (task polled once then never). skip-load bypass and A25_POLL refuted
Do not repeat: A25_POLL; skip-load bypass; save-load
Still running: nothing
Read: docs/analysis/STATE.md
