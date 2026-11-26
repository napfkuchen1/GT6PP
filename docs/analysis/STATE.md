# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-26. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Grep: `LEDGER.md`, `PROGRESS.md`, `eu-boot-log.md`.

## Goal
M1 (user 2026-11-25): complete, correct main menu, intro plays, controllable, no gfx/text errors; then M2: race.
STOP-GRUND: MENUE only when all M1 items are verified, incl. a live (non-headless) run with persistent save + pad input.

## M1 checklist (open until verified)
- [x] T1 popup shows real German text (A49 a49menu frame 30, work/_a49/menu_home_a49.png)
- [x] T2 garbled glyphs fixed (A49: DS-as-texture UV scale, patches/gt6-a49-ds-texscale.patch; 16/16 frames clean)
- [x] G1 all Home tiles drawn after the first car buy (work/_a55/home_after.png)
- [x] I1a opening movie decodes and shows on screen (A61: ATRAC PTS/size + video queue fix, patches/gt6-a61-*;
  work/_a61/movie.png = PD logo, play_a61mov_20261126_101824)
- [ ] I1b movie freezes after ~4 s: display stops after 199 pictures, video ES ring (4.6 MB) full, demux blocks,
  audio ends at AU 188 (play_a61mov_20261126_100927, _102655)
- [ ] I3 movie audio: ATRAC3plus decoder wired (A61 log "ATRAC3plus audible"), not verified by ear
- [ ] I2 tutorial/intro flow runs without skip overlay (remove gt6_vol_a45 skips)
- [x] C1 pad menu: popup X, dealer (~7 s), Honda car list (a53c: work/_a53/dealer_honda_cars.png)
- [x] C2 car view after FIT RS renders, pad works, buy completes (play_a54retire_20261126_052113, work/_a54/buy7.png)
- [x] G4 device hung = upload buffer freed while its copy was in the open command list (d3d_retire; same run: 0 DEVICE REMOVED)
- [x] G6a showroom car is drawn into the offscreen scene surface (A56 views patch; work/play_a56cap_20261126_063223 frame_01/rt_01F00000.bmp)
- [x] G6b NV3089 reads host RTs back into guest memory (A57 rt-readback patch; work/play_a57cap_20261126_065731
  run.log [NV3089RB] 444 copies, non-zero pixels)
- [x] G6c consumer of 0x602A0000: SPURS wid=5 (image 5) reads the correct car image and writes the display buffers
  (play_a57dma_20261126_072632 [dma-range] reader put img=5; work/_a57/spuget.png)
- [ ] G6d showroom washed out (parked A58, bypass: SPU upload off, SPU_FB=1 shows it): job input 0x60579000 =
  NV3089 of RT 0x022C0000 is noise (guest VRAM seed), also with split surface slots (a58 patch)
- [x] S3 delivery screen ends, dealer list returns (~2-3 min; same run, work/_a55/buy4.png, buy5.png)
- [x] D3 SPU interpreter off the hot path: 38 -> 2.6M steps/s, car view 0.9 -> 4.8 FPS (car.png)
- [ ] D4 rest interpreted, car view 5 FPS: image 76 LS 0x108EC/0x7D28/0x8048, image 74 0x54BC, PM 0xA68
  (play_a55lift2_20261126_061944)
- [ ] G7 popup bar draws several popups on top of each other (work/_a55/home_after.png): check vs real
- [x] G5 FP register arrays 48 -> 64 (work/play_a57cap_20261126_070409: 0 PS compile FAIL)
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
Never modify work/gt6_vol or gt6_vol_122+.
Car repro: play.py start, work/_a53/to_home2.sh, work/_a53/dealer.py.

## State

- (A46) Main menu reached: GT Mode home, Ver. 1.22. Frame work/_a46/main_menu_home.png; overlay gt6_vol_a45 (skip tutorial + opening), pad X 220..395.

## Next step
I1b: find the display clock. Trace cellAudioGetPortTimestamp/GetPortBlockTag and the port 1 read index during the
movie (work/_a61/movie.sh). Clock frozen: fix cellAudio. Else walk the consumer of the frame ring (player+0x78,
full wait 8AA25C, commit 8AA310) and read its release condition from a snapshot.
NID 0xA1709ABD: sceNpManagerGetEntitlementById.

## Refuted / symptom (do not repeat)
"Dealer load hang" (A50-52) = attract demo. Post-save movie stall (A40).
Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_*, exit race. More: LEDGER §4.
Never run GTToolsSharp/PDTools.
