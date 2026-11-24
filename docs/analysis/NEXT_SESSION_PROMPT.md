Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 622a2af docs: handover; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: With GT6_PUMP_ITERS=0 MGOM job 6170AC runs on pool worker tid34, 616C80 loads boot project but then tid34 idles w/o iter log => abnormal exit (setjmp/fiber guard C61F88/C620AC) or deadlock: tid30 blocked on lwm 0x17E8888 owner=main. Run probe -Env 'GT6_PUMP_ITERS=0;PS3_LWMUTEX_TRACE=1' (-Hdd0Src work\gt6_hdd0_rp -Seconds 90) and log 616C80 exits; decide: if fiber unwind, fix guard; if lock, find who locks 17E8888 on main.
Do not repeat: sync-pump inline = tid1 inline cause (done); AD4754/AF0254 thread create works; SNAP_AT broken use PS3_WD_AT
Still running: nothing
Read: docs/analysis/STATE.md (last 6 lines)
