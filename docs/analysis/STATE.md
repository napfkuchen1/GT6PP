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
- [ ] I1 opening movie plays (535 MB .pam skipped by host cap; cellPamf 0 streams)
- [ ] I2 tutorial/intro flow runs without skip overlay (remove gt6_vol_a45 skips)
- [ ] C1 pad controls menu (popup X, cursor, dealer enter/back)
- [ ] L1 live non-headless run, persistent save, real pad input

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch tools: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.

## State


  probe.ps1 early-kill bug fixed ($last unset with explicit -Seconds). Frames: RSX_CAP=start:count:stride.
  tid30 loop 616C80 keeps ticking 3 slots; script task 403D1910 reaches state 3 (done), no further task polls, no throw (A29 hooks), no file opens.
  Tool: `snap_walk.py <dir> bt` (guest call chains).

  unless skipOpening: MovieRoot.open, loop until isFinished -> start_project_gt6. play_movie: t_movie 'OPENING' -> /movies/<f>.pam,
  pdistd.Exist (else end_movie) -> Tv2.decodeContentsKey -> load. No .pam open / cellVdec call logged: black = likely stuck there.

  Trace tool: GT6_A40VM=<sec>, tools/a40_vm_hook.inc, scripts/adc_trace_match.py.
  to 460 s. GTModeRoot script error "(nil).toInt" (GroupData, SPECDB-like query) on tid1.

  (before 15477), but '(nil).toInt' still 10x, no frames captured (needs -Frame). CarName.dat still read 97984/103008.

  raw encrypted file (0E 94 7D BF), menudb.dat same. Reads served by hostov n=512 + n=full; no filter at stream+0x48 (only CarName.dat).
  probe.ps1 now derives -Frame from RSX_CAP. Frames a42full: credit dialogs, GT Mode loading screen.

  ignores it (read at AAF74C). xOpen C1FE74 pager fill AE6C34 leaves zeros (no page fault); p4 hook (port_hooks.py:131) copies raw.

  stubs.cpp gt6_pfs_key_layer). Dumps of DB0106 + menudb pass sqlite integrity_check. Runtime: queries on DB0106 still
  rc=11 (CORRUPT); xRead C1FC3C only ever reads off=0 (page 1), cache stable -> likely xFileSize reports old/small size.

  gt6_pfs_fstat_fix. Probe a45fix2: no rc=11, no toInt.

  is skipped by host override cap and cellPamf shows 0 streams (video not working).
  PFS slot (16, LRU) evicted -> xFileSize fell back to 1.00 TOC size. Size table per FileObject now. Run a46fix: 0 errors.
- (Arbeit46) Next crash a46fix: host stack overflow 0xC00000FD in SQLite on a guest ctx fiber (4 MB) -> HOST_STACK 32 MB.
- (Arbeit46) Legacy sqlite step returns rc=1; real code = Vdbe+0x5C, message +0x38. sqlite3CorruptError = BD532C (r3=line).

- (Arbeit46) MAIN MENU REACHED (C6): a46menu GT Mode home "Zuhause", Ver. 1.22, tiles + popup GT003_GET_FIRST_CAR.
  Frame work/_a46/main_menu_home.png; overlay gt6_vol_a45 (skip tutorial + opening), pad X 220..395.

## Next step
S1 + T2 fixed (A49, commit 99db830); 6/6 long runs no stall; a49menu 2/2 reach Zuhause (flip ~23000, 540 s).
Next: same run with more X presses after 470 s (popup close, dealer enter/back, cursor) -Seconds 700, capture late
(RSX_CAP=23000:40:301): C1 + G1 + stacked banner. Then I1 movie without skipopening overlay (gt6_vol_a45 skips).

## Refuted / symptom (do not repeat)
Post-save movie stall (Arbeit40). Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
