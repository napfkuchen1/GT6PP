Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 8ff9852 Arbeit22: sync-pump hack runs game loop inline on main; GT6_PUMP_ITERS=0; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: MGOM thread (entry 6170AC, created by AD4754 from 619198) never starts with GT6_PUMP_ITERS=0 (main waits in 6171D0). gdis AF003C + vtable slot8 of the thread object returned by AF003C (AD4794 vcall) -> why start skipped/deferred; log slot8 target + AD4390 at runtime via generated patch. Make PUMP_ITERS=0 default once the thread starts. Probe: probe.ps1 -Boot notut -Hdd0Src work\gt6_hdd0_rp -Env 'GT6_PUMP_ITERS=0;PS3_THREAD_BT=1' -Seconds 90
Do not repeat: sync-pump inline was the cause of tid1 inline loop (done, STATE Arbeit22); SNAP_AT env broken, use PS3_WD_AT; workers AD1670 idle is normal
Still running: nothing
Read: docs/analysis/STATE.md (last 4 lines)
