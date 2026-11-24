Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit c34065e Arbeit18: snapshots show tid1 always in finalizer; conswait guard is a s; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: SNAP_AT works (cause: parallel probe kill). Snapshots guard/base/A15_LOOP: tid1 always in finalizer 13FD0->AC746C (main 14010 returned); 8A7AD0 guard = shutdown symptom, drop it. NEW STRATEGY (SIBLING check 1/oracle compare): Oracle's AutoLoad2 -> job in worker 9qstY (AF0B94 task pool) submitted by main_thread at ~75 s; find who submits it (xref --call AF0B94 task submit) and why main 14010 returns before. If nothing: diff stage returns of 14010 vs Oracle trace.
Do not repeat: 8A7AD0 guard / conswait (Arbeit18: symptom of shutdown); PS3_SNAP_AT debugging (fixed); A15_LOOP env (not in build, was temp patch)
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail: Arbeit18, lines 334-338)
