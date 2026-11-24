Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 12dcec3 Arbeit21: tasks only run on tid1 (no worker claims), shutdown wait chain; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Only tid1 ever runs task bodies (A2F0AC via poll A2F290/A2FFCC loop; no worker, sleep-race refuted). Main later waits in shutdown 14884->AAE0F0->..->AE2844 lwcond. Oracle: worker 9qstY runs 6171FC task and creates Z-9m6/PDI threads. Find how a task is dispatched to a worker vs run inline: task state +0x28/request r4 machine A2EA5C, A4F938, A8548C, A2F0AC type switch; look for a config/flag (thread count, SPU/cpu query) choosing mt mode. Use PS3_WD_AT for thread states. Rebuild first (generated restored).
Do not repeat: Np2Init; finalize neuter; AFDFC0 title check legit; BFF0A0 default callbacks by design; 14010 stages all return; poll sleep race
Still running: nothing
Read: STATE.md (last 3 lines)
