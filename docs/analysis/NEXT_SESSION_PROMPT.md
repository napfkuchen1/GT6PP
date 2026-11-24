Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit b97a60e Arbeit20: Np2Init lead, IsLoaded(0x45) unknown; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Test: our cellSysmoduleIsLoaded(0x45) returns ERROR_UNKNOWN (slot<0 in libs/*/cellSysmodule.c); guest B4D668 bails on nonzero. Make 0x45 a known module (loaded/OK, check RPCS3 table), rebuild (scripts/build-all.ps1), ONE probe -Hdd0Src work/gt6_hdd0_rp PS3_LANG=en-gb, look for Np2Init/Trophy/F044. Oracle does Np2Init before AutoLoad2s; ours never.
Do not repeat: override-off; save rename; F044/isOnline script chain; GPROF has no call counts
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail)
