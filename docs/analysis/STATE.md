# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-25. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Facts: `LEDGER.md` (grep). Checkpoints/runs: `PROGRESS.md`. History: `eu-boot-log.md` (grep). One line per finding.

## Goal
User definition 2026-11-25: reaching the menu was only step 1. M1 DONE only when main menu is complete and correct: intro
sequence plays, menu controllable, no graphics errors, no text errors. M2 afterwards: first race.
STOP-GRUND: MENUE only when all M1 items are verified, incl. a live (non-headless) run with persistent save + pad input.

## M1 checklist (open until verified; Arbeit47 inventory)
- [ ] T1 raw message ID in popup (GT003_GET_FIRST_CAR0) instead of text
- [ ] T2 garbled glyphs in some frames (credit dialog, menu header)
- [ ] G1 menu tiles black (only dealer tile drawn)
- [ ] I1 opening movie plays (535 MB .pam skipped by host cap; cellPamf 0 streams)
- [ ] I2 tutorial/intro flow runs without skip overlay (remove gt6_vol_a45 skips)
- [ ] C1 pad controls menu (popup X, cursor, dealer enter/back)
- [ ] L1 live non-headless run, persistent save, real pad input

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch tools: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.

## State

  fails -> B08498 holds lock 17B4C08 -> B0921C -> B1A0F4/B04CD8 wants 17B4BD8; tid30 per-frame AE73BC -> B04CD8 holds BD8, wants C08.
  SettingProjectComponent.gpb, ~37 fps (older mode, Arbeit33). OOM cause still unmeasured. Repeat batch until the deadlock hits.

  garbage; B0C524 args are align,size) -> endless retry. Hook now prints call chain. Deadlock guard tools/guard_heaplock.py (post-lift).
  Fix: probe.ps1 sets PS3_GAMEDATA_ROOT per run (-SaveSrc seeds it); that save is in work/ARCHIV/savedata_a35pad3_20261125_1132. Verified a37sv + a37ps: 4/4 AdjustScreen.

  copy AD3DFC -> new AE73BC (alloc retry); saved run: AD4294 walk/free, tid1 waits 6171D0 -> AE27AC. Saved+black: no loads, X no effect.

  0/shifted -> 16-byte buffer, SPU 16 KB DMA over heap. patches/gt6-a39-jobchain-selfreport.patch (0498bee), a39fix 2/2 sizes stable.

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
Work the M1 checklist, order T1 -> G1 -> T2 -> C1 -> I1 -> I2 -> L1.

## Refuted / symptom (do not repeat)
Post-save movie stall (Arbeit40). Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
