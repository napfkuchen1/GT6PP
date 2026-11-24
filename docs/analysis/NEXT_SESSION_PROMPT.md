Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 8e9d2ff docs: handover; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Np2 lead CLOSED (Np2Init runs in ours, same slot as oracle). Chain Save/Term/NP/Quit exhausted again. Strategy (3): bypass the finalize guard (find who calls PDINetwork.finalize 9AD1DC via script run 13C44/13D94, skip it with a guarded env patch) and look at the next blocker, or strategy (4) SIBLING_SOURCES.md checks (GT5P/gt5-recomp: what makes tid1 stay in game loop). Oracle: main waits, worker 9qstY runs game loop, ours main runs it inline (A7E5F4/A7BC50 submit-vs-inline decision) - static check first.
Do not repeat: Np2Init/IsLoaded(0x45) lead (verified present); GT6_SAVE_CBRES/empty savedata (no effect); pagefile.sys/VMPageFile (page-fault consequence)
Still running: nothing
Read: STATE.md (last 3 lines)
