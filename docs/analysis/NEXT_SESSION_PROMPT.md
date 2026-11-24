Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit 860b739 docs: Arbeit25 poll driver finding; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Task B90 (40393B90) polled once after HMonitor wait then never; skip-load bypass same stall => generic missing per-frame poll driver. All polls inside project start 6DD7C8 / one-shot node flush 683318. Find what 6B5570 attaches project into (node r4, project+0x40 readers 6B5FC4/6B60AC/6B6138/6B7194/6B7CC0) and who should call per-frame project update; snap_83435343 (heap may differ)
Do not repeat: A25_POLL; skip-load bypass; HMonitor wake; save-load
Still running: nothing
Read: docs/analysis/STATE.md
