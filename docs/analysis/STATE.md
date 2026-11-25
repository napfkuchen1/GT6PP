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

  copy AD3DFC -> new AE73BC (alloc retry); saved run: AD4294 walk/free, tid1 waits 6171D0 -> AE27AC. Saved+black: no loads, X no effect.

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

- (Arbeit44) FIXED keyed open: host bytes now pass guest key layer 0xAC874C (Salsa20, state [FileObject+0x60]+0x1C;
  stubs.cpp gt6_pfs_key_layer). Dumps of DB0106 + menudb pass sqlite integrity_check. Runtime: queries on DB0106 still
  rc=11 (CORRUPT); xRead C1FC3C only ever reads off=0 (page 1), cache stable -> likely xFileSize reports old/small size.

- (Arbeit45) FIXED f8ef048: xFileSize C1F848 -> stream stat ABD328 gave 1.00 TOC size (16041984 vs 16602112); hook
  gt6_pfs_fstat_fix. Probe a45fix2: no rc=11, no toInt.

- (Arbeit45) FIXED b219eca: port cache-fill hook clobbered cr7 -> grim007.db buffer freed, ptr=1 -> rc=26. Gone.
- (Arbeit45) Overlay work/gt6_vol_a45 (a40t + skipopening): readable credit dialogs -> GT Mode loading. Opening .pam (535 MB)
  is skipped by host override cap and cellPamf shows 0 streams (video not working).
- (Arbeit45) Debug prints [A2x] in gen 013/014/015/022 gated by GT6_A27 (backup work/_bk_a45/a27); GT6_PFS_TRACE slows load.
- (Arbeit45) NOW: GT Mode reload loop (gtmode.mproject ~38x, ~0.4 s/cycle in a45vm). CarDealerRoot got_first_car ->
  getGTModeFirstCarPP l376 is last op; 'SELECT PP FROM GENERIC_CAR WHERE ID=?' step returns rc=1 (9x in a45op).

## Next step
1) Why step rc=1 on SELECT PP (DB0106)? Run GT6_A42SQL=1 (no PFS trace), get errmsg/reset code; check xRead C1FC3C /
   ABD3D0 for off!=0 on DB0106 (key layer offset, short read) and bound ID (nil without first car?). Snapshot of loop:
   work/snap_a45gm_540.

## Refuted / symptom (do not repeat)
Post-save movie stall (Arbeit40). Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
