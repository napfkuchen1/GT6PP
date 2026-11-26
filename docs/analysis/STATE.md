# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-26. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Facts: `LEDGER.md` (grep). Checkpoints/runs: `PROGRESS.md`. History: `eu-boot-log.md` (grep). One line per finding.

## Goal
User definition 2026-11-25: reaching the menu was only step 1. M1 DONE only when main menu is complete and correct: intro
sequence plays, menu controllable, no graphics errors, no text errors. M2 afterwards: first race.
STOP-GRUND: MENUE only when all M1 items are verified, incl. a live (non-headless) run with persistent save + pad input.

## M1 checklist (open until verified; Arbeit47 inventory)
- [x] T1 popup shows real German text (A49 a49menu frame 30, work/_a49/menu_home_a49.png)
- [x] T2 garbled glyphs fixed (A49: DS-as-texture UV scale, patches/gt6-a49-ds-texscale.patch; 16/16 frames clean)
- [ ] G1 only dealer tile drawn, rest dark: maybe tutorial dimming; check after popup close; stacked banner x3 too
- [ ] I1 opening movie: cellPamf layout fixed (A50, patches/gt6-a50-pamf-header.patch, not run); cellDmux is a stub, no FFmpeg headers
- [ ] I2 tutorial/intro flow runs without skip overlay (remove gt6_vol_a45 skips)
- [ ] C1 pad controls menu: popup X + dealer enter OK (a50pad 2/2); dealer screen/back/cursor unverified (loading >100 s)
- [ ] L1 live non-headless run, persistent save, real pad input

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch tools: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.

## State

- (Arbeit46) Next crash a46fix: host stack overflow 0xC00000FD in SQLite on a guest ctx fiber (4 MB) -> HOST_STACK 32 MB.
- (Arbeit46) Legacy sqlite step returns rc=1; real code = Vdbe+0x5C, message +0x38. sqlite3CorruptError = BD532C (r3=line).

- (Arbeit46) MAIN MENU REACHED (C6): a46menu GT Mode home "Zuhause", Ver. 1.22, tiles + popup GT003_GET_FIRST_CAR.
  Frame work/_a46/main_menu_home.png; overlay gt6_vol_a45 (skip tutorial + opening), pad X 220..395.

## Next step
a50deal (2x 900 s): dealer load never finishes. r1 tid30 in sys_lwmutex_lock(0x6FF52FF0), chain AD4294+0x78 <6166A4
<7B51B8, same at 780/880 s; tid3 in B091FC (heap). r2 only 18745 flips (stall before menu; tid30 8A7B90). Find the lock
owner (lwmutex struct at that EA, snapshot or WD print), compare with tools/guard_heaplock.py deadlock (Arbeit37).
Then I1: real MPEG-PS demux in cellDmux.c + FFmpeg headers (avcodec-63/avutil-61, DLLs in tools/RPCS3), run without
skipopening; check served .pam size (old run passed 1.00 size 351096832). Notes: side-session note arbeit50-movie.md.

## Refuted / symptom (do not repeat)
Post-save movie stall (Arbeit40). Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
