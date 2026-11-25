Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 6393d62 fix: apply the guest key cipher to host-served keyed files (car database; PROGRESS: 2026-11-25 | 58d9306 | vol | ok ok FAIL FAIL ok FAIL - | probe_a42full_20261125_153650_1 | non-black=71%
Next step: Find xFileSize of SQLite VFS (xOpen C1FE74; xRead C1FC3C, xFileControl C1F9B8, xClose ~C1F8B0): log its result for DB0106 vs 16602112; if smaller, fix the size source. Verify 90 s probe GT6_VOL_ROOT=work/gt6_vol_a40t;GT6_A42SQL=1: no rc=11 on DB0106.
Do not repeat: key decrypt itself (dumps integrity ok); cache buffer corruption (stable 120 s); guest-path read (1.00 volume)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit44
