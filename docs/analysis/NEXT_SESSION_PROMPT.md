Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit 8f3799a (Arbeit26 findings); PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Boot task B90 (40393B90, tid30) is resumed once after load (poll A305AC, st 2->0->1) then yields via SET_STATE 1 (AA1A04) and is never run again; task body = A2F290 (big fn: A2EA5C state, A2ED74 msg flush, A2F0AC exec; callers A2F86C/A30024/A85F28/A86164/1062474; inline in a lifted fn, trace_enter cannot hook it). Find which caller runs project tasks each frame (static xref of those callers' parents, then 1 run with hook on A2F86C or A30024 lr) and why it stops after load; also boot script after l94 (getBackgroundLoadResultFromFile native never reached). Rule: if caller is a per-frame updater of a registry -> find its missing registration; else compare with tid1 task runner.
Do not repeat: A25_POLL; A26_UPD (6A68C0 forced per frame); A26_TP (direct A2ED74 ends task); skip-load; HMonitor wake; project-registry/hash-map walking (403869A0 map has no live owner)
Still running: nothing
Read: docs/analysis/STATE.md
