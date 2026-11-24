Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit f1b6a23 Arbeit22: tools/trace_enter.py, findings: main returns after MGOM.start ; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Oracle-emulation done (main blocked after MGOM.start, GT6_PUMP_ITERS=0): workers idle, 49 opens, no 3rd AutoLoad thread. Find who should wake worker events AC1C78/AD8C08 and why tid38-40 exit (AF0B94+0xE8); diff vs oracle thread/event sequence
Do not repeat: A2F290 force-2 on main refuted; MGOM.start ack is instant (legit); main-exit chain done
Still running: nothing
Read: STATE.md (last 3 lines)
