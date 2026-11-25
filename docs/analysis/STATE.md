# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-25. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Facts: `LEDGER.md` (grep). Checkpoints/runs: `PROGRESS.md`. History: `eu-boot-log.md` (grep). One line per finding.

## Goal
Main menu (C6). 1.22 overlay route reaches legal screen + 'Sony Computer Entertainment presents'.

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch tools: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.

## State

  fails -> B08498 holds lock 17B4C08 -> B0921C -> B1A0F4/B04CD8 wants 17B4BD8; tid30 per-frame AE73BC -> B04CD8 holds BD8, wants C08.
  SettingProjectComponent.gpb, ~37 fps (older mode, Arbeit33). OOM cause still unmeasured. Repeat batch until the deadlock hits.

  garbage; B0C524 args are align,size) -> endless retry. Hook now prints call chain. Deadlock guard tools/guard_heaplock.py (post-lift).
  Fix: probe.ps1 sets PS3_GAMEDATA_ROOT per run (-SaveSrc seeds it); that save is in work/ARCHIV/savedata_a35pad3_20261125_1132. Verified a37sv + a37ps: 4/4 AdjustScreen.

- (Arbeit37) a37wd (WD 225/240): tid30 sits in list notify AD4294 (called 6166A4, list obj+0x2B0; also A7F074). Stalled run: inside
  copy AD3DFC -> new AE73BC (alloc retry); saved run: AD4294 walk/free, tid1 waits 6171D0 -> AE27AC. Saved+black: no loads, X no effect.

- (Arbeit38/39) FIXED: heap corruption/OOM. HLE job chain added a data3=0 completion beside the SPU job's reply; sgx sizes came back
  0/shifted -> 16-byte buffer, SPU 16 KB DMA over heap. patches/gt6-a39-jobchain-selfreport.patch (0498bee), a39fix 2/2 sizes stable.

- (Arbeit39) WITH FIX 4/4 (a39g/h, pad X every 25 s 220..395): language select -> AdjustScreen -> dialog -> AutoSave2 -> SAVE complete.
  probe.ps1 early-kill bug fixed ($last unset with explicit -Seconds). Frames: RSX_CAP=start:count:stride.
- (Arbeit39) After save: black 4/4 for 100-190 s. a39s snapshots work/snap_a39black_{1,2}: tid1 in MGOM.start wait (6171D0, obj 6FF36000),
  tid30 loop 616C80 keeps ticking 3 slots; script task 403D1910 reaches state 3 (done), no further task polls, no throw (A29 hooks), no file opens.
  Tool: `snap_walk.py <dir> bt` (guest call chains).

- (Arbeit39) Static boot flow (boot_sequence_gt6.ad in boot.adc): AdjustScreen -> applySaveData -> voucher dialog -> BackupSave ->
  unless skipOpening: MovieRoot.open, loop until isFinished -> start_project_gt6. play_movie: t_movie 'OPENING' -> /movies/<f>.pam,
  pdistd.Exist (else end_movie) -> Tv2.decodeContentsKey -> load. No .pam open / cellVdec call logged: black = likely stuck there.

- (Arbeit40) Post-save black = intro tutorial race (start_project_gt6 -> executeEvent), VM stops at 399.7 s after its save; movie skip no help.
  Trace tool: GT6_A40VM=<sec>, tools/a40_vm_hook.inc, scripts/adc_trace_match.py.
- (Arbeit40) MILESTONE: overlay work/gt6_vol_a40t (tools/patch_adc_skiptutorial.py) 2/2: credit dialogs, then GT Mode loading screen (GT logo)
  to 460 s. GTModeRoot script error "(nil).toInt" (GroupData, SPECDB-like query) on tid1.

- (Arbeit41) FIXED eb71225: guest stat took sizes from the 1.00 TOC -> overlay files truncated (SPECDB, adc, DE.rt2). Run a41full: 26298 flips
  (before 15477), but '(nil).toInt' still 10x, no frames captured (needs -Frame). CarName.dat still read 97984/103008.

- (Arbeit42) ROOT of (nil).toInt: SPECDB (specdb/GT6/DB0106.dat) prepare returns SQLite rc=26 NOTADB; page 1 handed to SQLite is the
  raw encrypted file (0E 94 7D BF), menudb.dat same. Reads served by hostov n=512 + n=full; no filter at stream+0x48 (only CarName.dat).
  probe.ps1 now derives -Frame from RSX_CAP. Frames a42full: credit dialogs, GT Mode loading screen.

- (Arbeit43) DB key found: script open passes key string; aac2a8 stores {1,str,len} at FileObject+0x90, ptr +0x9C. Host open override
  ignores it (read at AAF74C). xOpen C1FE74 pager fill AE6C34 leaves zeros (no page fault); p4 hook (port_hooks.py:131) copies raw.

## Next step
1) gdis around AAF720-AAF774 (reader of FileObject+0x9C) + callers: find guest decrypt routine and its args. Then apply it to the
   override-served bytes when file+0x9C != 0 (gt6/src/stubs.cpp gt6_pfs_stream_read_override). Keep p4 cache fill. Verify with
   GT6_A42SQL=1: [A42N] page1 = 'SQLite format 3', no rc=26. DB opens at ~4 s: 90 s probe suffices (GT6_A43BT=1 backtrace).

## Refuted / symptom (do not repeat)
Post-save movie stall (Arbeit40). Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
