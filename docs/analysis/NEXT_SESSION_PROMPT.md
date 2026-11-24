Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 3aa7f22 docs: handover; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Oracle: worker 9qstY runs 6171FC task and creates Z-9m6/PDI threads; main_thread silent. Ours: tid1 polls A2F290 (A30020 loop in A2FFCC) and runs the task inline via A2F0AC (setjmp fiber). Find the claim/owner logic: A2F290 fields +0x28 state, +0x64, calls A2EA5C/A4F938/A8548C; log tid entering A2F0AC (patch fprintf, generated 022, restore after). Rebuild first.
Do not repeat: Np2Init; finalize neuter; AFDFC0 title check legit; BFF0A0 default callbacks by design; 14010 stages all return
Still running: nothing
Read: STATE.md (last 3 lines)
