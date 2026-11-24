Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 4edfc40 docs: handover; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Find where oracle main_thread blocks after rsx_iomap 75.98s (-SBXs thread, K/CF, 9/56/PW opens) that ours skips: our 14010 stages all return in ms (A21STG). Compare 1414C/BFF0A0 and shutdown 13FD0 (A7BF50, A1EAD0) wait paths with oracle thread creates (-SBXs missing in ours); use PPU_WWATCH=<hex> [ww] to find writers. Rebuild first.
Do not repeat: Np2Init; finalize neuter; AFDFC0 boot check legit (title match); BFF0A0 default callbacks by design
Still running: nothing
Read: STATE.md (last 3 lines)
