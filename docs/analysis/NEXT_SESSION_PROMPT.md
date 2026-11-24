Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit 9d856ff docs: Arbeit25 boot task re-poll finding; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Boot task B90 (40393B90, script task, checkGameData/loadEveryWhere l94, st=1) never re-polled after final SET_STATE 1; polled earlier via node tree 6B7E4C (69098C/6DD844). snap_83435343 (PS3_SNAP_AT=70) has B90/C10 st=1, +0x34 ctx 40384C88. Find where task is parked / which list should poll it (snap_walk, xref writers of task +0x34/+0x1C), or compare oracle. Gen 014/017/022 carry A25 hooks
Do not repeat: A25_POLL 683318 per-frame (refuted); HMonitor wake A4FBE8; AD4294 loop alive
Still running: nothing
Read: docs/analysis/STATE.md
