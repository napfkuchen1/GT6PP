Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 0498bee fix: drop duplicate job chain completion that broke sgx buffer sizes (he; PROGRESS: 2026-11-25 | 717ae2d | vol | ok FAIL - - - - - | probe_a38list_20261125_123210_2 | non-black=0%
Next step: probe.ps1 -Name a39f -Parallel 2 -Seconds 320 -Frame 12000 -PadScript '220:0x4000 245:0x4000 265:0x4000' -Env 'GT6_VOL_ROOT=work/gt6_vol_a35;A29_JMP=1;PS3_VERBOSE=0;GT6_UNBUF=1'. View captured frames: if AdjustScreen renders and X yields no AutoSave2, inspect input/funcStat path; if save completes and black, analyse tid1 wait 6171D0 -> AE27AC.
Do not repeat: Heap/list corruption fixed (LEDGER A39, 0498bee); do not re-chase SPU DMA/listener list. LEDGER §4 + CLAUDE.md locked chains.
Still running: nothing (env-gated hooks GT6_A39SZ gen 028, GT6_A39EV cellSpurs.c; backups work/_bk_a39)
Read: STATE.md (Arbeit39 lines); eu-boot-log.md Arbeit39
