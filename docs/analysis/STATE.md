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
- (Arbeit34) Guard [A34G] only in gt6/generated ppu_recomp_023.cpp (clean: work/_bk_a34/ppu_recomp_023_pre.cpp); not persisted.
- (Arbeit34) CD2ABC: lock 1713700 (920458/920480), CD255C, loop; guard run2 still stalls (hot=19443) -> other corruption remains.
- (Arbeit34) Script blocker on every Presents run: main.adc GameItem.ad l275 (nil).ColorBegin (SPECDB AVATAR_* row missing) kills boot script.

## Next step
1) Persist AE6388 guard via tracked post-lift patch. 2) Bypass ColorBegin: new overlay with COPY of main.adc (break hardlink),
JUMP_IF_FALSE(0x0F) at file 0xEB893 -> JUMP(0x0D), target 48; find next error / why SPECDB AVATAR_* row is missing.

## Refuted / symptom (do not repeat)
Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
