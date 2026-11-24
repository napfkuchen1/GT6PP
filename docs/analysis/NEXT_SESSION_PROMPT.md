Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit f05c51d Arbeit21: finalize-neuter negative, teardown chain to 13FD0; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Find which main stage in 14010 (calls 148b4,1416c,147bc,13de4,143e8,ce2170,146e8,141e8,91e464,1414c, each followed by AD2998 check -> bne 14114 exit) returns first and why; use PS3_CALLTRACE_FROM or snap at 10s; then fix. Rebuild first (generated restored, binary still has A21_NOFIN hook, harmless).
Do not repeat: Np2Init/0x45; finalize neuter (A21_NOFIN) no effect; GT6_SAVE_CBRES/empty savedata
Still running: nothing
Read: STATE.md (last 3 lines)
