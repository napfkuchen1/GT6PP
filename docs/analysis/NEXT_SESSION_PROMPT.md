Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 321886f docs: handover, 1.22 script extraction needs human; PROGRESS: 2026-11-24 | 321886f | orig | ok FAIL - - - - - | probe_a30font_20261124_233313_1 | non-black=0%
Next step: Guest PFS path (GT6_VOL_ROOT=work/gt6_vol_a30, -Hdd0Src <abs>\work\gt6_hdd0_rp, -Env A22_BLOCK=1) deadlocks on first compressed file. gdis 0xAC74FC/0xAC75B0/0xAC8698; find vtable caller of AC75B0 (output-buffer side, signals P+0x1b98); if tid1/tid9 cannot reach it before AC78F4 returns, check lwcond HLE/spurious wake (AE27AC, sysPrxForUser.c l733), fix, rerun probe with A29_JMP=1
Do not repeat: A30: do NOT run GTToolsSharp (authors forbid AI use, only human owner); 1.00 scripts mismatch 1.22 ELF
Still running: nothing
Read: STATE.md (Arbeit30 lines at end)
