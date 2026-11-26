# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-26. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Facts: `LEDGER.md` (grep). Checkpoints/runs: `PROGRESS.md`. History: `eu-boot-log.md` (grep). One line per finding.

## Goal
User 2026-11-25: M1 DONE only when main menu is complete and correct: intro
sequence plays, menu controllable, no graphics errors, no text errors. M2 afterwards: first race.
STOP-GRUND: MENUE only when all M1 items are verified, incl. a live (non-headless) run with persistent save + pad input.

## M1 checklist (open until verified; Arbeit47 inventory)
- [x] T1 popup shows real German text (A49 a49menu frame 30, work/_a49/menu_home_a49.png)
- [x] T2 garbled glyphs fixed (A49: DS-as-texture UV scale, patches/gt6-a49-ds-texscale.patch; 16/16 frames clean)
- [x] G1 all Home tiles drawn after the first car buy (work/_a55/home_after.png)
- [ ] I1 opening movie: cellPamf layout fixed (A50, patches/gt6-a50-pamf-header.patch, not run); cellDmux is a stub, no FFmpeg headers
- [ ] I2 tutorial/intro flow runs without skip overlay (remove gt6_vol_a45 skips)
- [x] C1 pad menu: popup X, dealer (~7 s), Honda car list (a53c: work/_a53/dealer_honda_cars.png)
- [x] C2 car view after FIT RS renders, pad works, buy completes (play_a54retire_20261126_052113, work/_a54/buy7.png)
- [x] G4 device hung = upload buffer freed while its copy was in the open command list (d3d_retire; same run: 0 DEVICE REMOVED)
- [x] G6a showroom car is drawn into the offscreen scene surface (A56 views patch; work/play_a56cap_20261126_063223 frame_01/rt_01F00000.bmp)
- [x] G6b NV3089 reads host RTs back into guest memory (A57 rt-readback patch; work/play_a57cap_20261126_065731
  run.log [NV3089RB] 444 copies, non-zero pixels)
- [x] G6c consumer of 0x602A0000: SPURS wid=5 (image 5) reads the correct car image and writes the display buffers
  (play_a57dma_20261126_072632 [dma-range] reader put img=5; work/_a57/spuget.png)
- [ ] G6d showroom washed out (parked A58, bypass: SPU upload stays off, SPU_FB=1 to see it): job input 0x60579000 =
  NV3089 of RT 0x022C0000, noise (guest VRAM seed); surface is RGBA16F + RGBA8, slots split (a58 patch), still noise
- [x] S3 delivery screen ends, dealer list returns (~2-3 min; same run, work/_a55/buy4.png, buy5.png)
- [x] D3 SPU interpreter off the hot path: 38 -> 2.6M steps/s, car view 0.9 -> 4.8 FPS (same run, car.png)
- [ ] D4 rest interpreted, car view 5 FPS: image 76 LS 0x108EC/0x7D28/0x8048, image 74 0x54BC, PM 0xA68
  (play_a55lift2_20261126_061944)
- [ ] G7 popup bar draws several popups on top of each other (work/_a55/home_after.png): check vs real
- [x] G5 FP register arrays 48 -> 64 (A57; work/play_a57cap_20261126_070409: 0 PS compile FAIL)
- [ ] G2 car-name text in dealer list smeared/overbold (work/_a53/dealer_cars_full.png)
- [ ] G3 dealer tiles: grey backing covers only upper-left part of each tile (same frame)
- [ ] D1 attract demo (autodemo race) loads very slowly, window FPS 0.29 (a53a)
- [ ] D2 idle demo starts ~10 s after Home; input during the countdown does not cancel it (a53b, a53i): check
- [ ] S2 boot crash 0xC00000FD, recursive tree walk func_00AE0464 on tid34 (a53g 1 of 8; play_a57fb_20261126_080148)
- [ ] S1 car-view stall: ACQUIRE wait + lost user causes fixed; verify over more runs
- [ ] W4 workaround: GCM_SEMA_BLOCK=500-560 (gt6 main.cpp); blocking all ACQUIREs breaks on label 0xFE0
- [ ] W1 workaround: interpreter bodies spliced into gen 037; confirm with a full re-lift (patches/gt6-a51-jt-loop-base.patch)
- [ ] W2 workaround: PPU_ONECORE=1 default (one-core pinning); run without it
- [ ] W3 workaround: GCM_PARK_GRACE_MS=5000 in gt6/src/main.cpp (FIFO self-JUMP resync), see S1
- [ ] L1 live non-headless run, persistent save, real pad input

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.
Car repro: scripts/play.py start,
sh work/_a53/to_home2.sh, python -I work/_a53/dealer.py.

## State

- (Arbeit46) MAIN MENU REACHED (C6): GT Mode home, Ver. 1.22, tiles + popup.
  Frame work/_a46/main_menu_home.png; overlay gt6_vol_a45 (skip tutorial + opening), pad X 220..395.

## Next step
M1 next item: I1 opening movie. cellDmux is a stub (needs PAMF demux), cellVdec needs FFmpeg headers
(avcodec-63/avutil-61; DLLs in tools/RPCS3). First run check: PAMF patch on a vol without skipopening, GT6_PFS_TRACE=1.
G6d later: per-op surface format into manifest (op1231-1239 on 0x022C0000), then which slot NV3089 must read.

## Refuted / symptom (do not repeat)
"Dealer load hang" (Arbeit50-52) = attract demo. Post-save movie stall (Arbeit40).
Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Never run GTToolsSharp/PDTools. 1.00-era findings: obsolete, see LEDGER.
