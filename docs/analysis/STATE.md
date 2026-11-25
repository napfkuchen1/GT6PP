# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-25. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Facts: `LEDGER.md` (grep). Checkpoints/runs: `PROGRESS.md`. History: `eu-boot-log.md` (grep). One line per finding.

## Goal
Main menu (C6). 1.22 overlay route reaches legal screen + 'Sony Computer Entertainment presents'.

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch tools: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.

## State
- (Arbeit32) Fixes: /STACK:64M; purecall guard (C68B8C logs, returns 0); stale 11-22 savedata moved to ARCHIV (caused DISKFULL).
- (Arbeit33) Boot race solved by pinning guest PPU threads to 1 host core (PPU_ONECORE=1): 6/6 reach PresentsRootSCEE.
- (Arbeit34) 0xC00000FD = fflush(NULL) symptom; root: AE6388 (from CD2ABC, vector 6FFFE910 with 2 NULL entries) wipes NULL page..TOC.
- (Arbeit35) AE6388 guard persisted (tools/guard_ringzero.py in post-lift). ColorBegin bypass: tools/patch_adc_colorbegin.py, overlay work/gt6_vol_a35.
- (Arbeit35) MILESTONE (probe_a35pad_..112132_2, pad3_..112834_2): AdjustScreen renders (German); X at 220 s -> AutoSave2 -> SAVE complete.
- (Arbeit35) Shared PDIPFS junction: parallel runs both wrote K/CQ.fdup* -> 2x AV at 85 s. probe.ps1 now copies PDIPFS per run (CQ moved to ARCHIV).
- (Arbeit35) After SAVE complete: black frame, no further opens/loads for 60 s (frame 15000, 1 draw op). Oracle opens PDIPFS/59/FI (film) here.

- (Arbeit35) New (a35wd run1, PS3_WD_AT): heap AB-BA deadlock at ~200 s, AdjustScreen never loads. tid1 operator new B0CCAC: alloc B0C524
  fails -> B08498 holds lock 17B4C08 -> B0921C -> B1A0F4/B04CD8 wants 17B4BD8; tid30 per-frame AE73BC -> B04CD8 holds BD8, wants C08.
- (Arbeit35) a35wd run2: flip stall at 156 s, purecall storm lr=2CD5F4 + linear read faults 0x100x0000 upward (runaway walk).
- (Arbeit35) a35oom (2 runs, hook [A35OOM] in gen 024 B0CCAC, bk work/_bk_a35, binary carries it): 0 OOM, both stop at
  SettingProjectComponent.gpb, ~37 fps (older mode, Arbeit33). OOM cause still unmeasured. Repeat batch until the deadlock hits.

- (Arbeit36) OOM cause seen (a36hl_2): operator new retry loop AE73BC (callers via AE752C/40/54) asks ~161 MB (size 099F6844 =
  garbage; B0C524 args are align,size) -> endless retry. Hook now prints call chain. Deadlock guard tools/guard_heaplock.py (post-lift).
- (Arbeit36) SettingProject stall: tid1 takes the script task meant for tid30 (A27T after tid31 post) and waits in A0498C
  (sync wait, 88F2B4 loop) inside its own main tick (correlation). PPU_PRIO_MAP=1 (a36pm, 2 runs) no fix, tid30 case stalls too.

- (Arbeit37) "AdjustScreen 0/14" was no code regression: pad run pad3_2 saved to shared ./gamedata (11:32); later boots had a save.
  Fix: probe.ps1 sets PS3_GAMEDATA_ROOT per run (-SaveSrc seeds it); that save is in work/ARCHIV/savedata_a35pad3_20261125_1132. Verified a37sv + a37ps: 4/4 AdjustScreen.

- (Arbeit37) a37wd (WD 225/240): tid30 sits in list notify AD4294 (called 6166A4, list obj+0x2B0; also A7F074). Stalled run: inside
  copy AD3DFC -> new AE73BC (alloc retry); saved run: AD4294 walk/free, tid1 waits 6171D0 -> AE27AC. Saved+black: no loads, X no effect.

- (Arbeit38/39) FIXED: heap corruption/OOM. HLE job chain added a data3=0 completion beside the SPU job's reply; sgx sizes came back
  0/shifted -> 16-byte buffer, SPU 16 KB DMA over heap. patches/gt6-a39-jobchain-selfreport.patch (0498bee), a39fix 2/2 sizes stable.

- (Arbeit39) a39long 131435_1/2 (320 s): oom=0, list bad=0, AdjustScreenRoot loaded, X 220/245/265 s logged but no later load; frame 15000
  not reached (~13400 flips), save not confirmed. Probe started only 2 of -Parallel 4.

## Next step
1) Long runs with the fix (probe -Parallel 4 -Seconds 320 -Frame 12000, pad "220:0x4000 245:0x4000" space-separated): look at frames; does AdjustScreen render, does X reach AutoSave2?
2) Post-save black screen: tid1 waits 6171D0 -> AE27AC after SAVE complete; re-measure, old stalls may be gone with the fix.

## Refuted / symptom (do not repeat)
Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
