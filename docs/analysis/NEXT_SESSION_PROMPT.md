Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit eb71225 fix: report served overlay file size in guest stat (SPECDB, scripts, rte; PROGRESS: 2026-11-25 | 94b5218 | vol | ok ok FAIL FAIL ok FAIL - | probe_a40tut_20261125_142341_2 | non-black=81%
Next step: Rerun probe_a41full with -Frame 13000 and GT6_A40VM=390 (overlay a40t): find site of remaining 10x '(nil).toInt' after fix eb71225; if still getGTModeFirstCarPP l376 check SPECDB query + CarName.dat short read (97984/103008), else disassemble new site
Do not repeat: SPECDB/adc truncation fixed (eb71225); do not re-trace sizes except CarName
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit41
