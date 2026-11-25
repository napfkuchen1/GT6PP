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

## Next step
Find what the script/tid30 waits for after SAVE complete: PS3_WD_AT dump at stall, [null-call] AD23EC (tid30/27, opd 0x2200208x) check;
LEDGER l17-27 (spinner, 59/FI trigger). Pad run: -Env GT6_VOL_ROOT=work/gt6_vol_a35;A29_JMP=1 -PadScript "180:0x4000 200:0x4000 220:0x4000" -Seconds 300.

## Refuted / symptom (do not repeat)
Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
