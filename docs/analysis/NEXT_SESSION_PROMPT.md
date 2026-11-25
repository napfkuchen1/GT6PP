Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 2385ea9 docs: Arbeit45 results; PROGRESS: 2026-11-25 | b219eca | vol | ok FAIL - - - - - | probe_a45gm_20261125_174602_1 | non-black=0%
Next step: GT Mode reload loop: run GT6_VOL_ROOT=work/gt6_vol_a45;GT6_A42SQL=1 (no PFS trace, pad X 220..395, 480 s); find why step of 'SELECT PP FROM GENERIC_CAR' returns rc=1 (xRead off!=0 / key layer / bound ID); if IO error fix reader, if ID nil check first-car state (tutorial skip).
Do not repeat: xFileSize/size fixes (f8ef048), grim007 (b219eca), GT6_PFS_TRACE long runs (too slow)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit45
