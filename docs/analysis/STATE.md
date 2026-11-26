# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-26. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: game 1.22 + ps3recomp v0.20.
Rules: `CLAUDE.md`. Grep: `LEDGER.md`, `PROGRESS.md`, `eu-boot-log.md`.

## Goal
M1 (user 2026-11-25): complete, correct main menu, intro plays, controllable, no gfx/text errors; then M2: race.
STOP-GRUND: MENUE only when all M1 items are verified, incl. a live (non-headless) run with persistent save + pad input.

## M1 checklist (open until verified)
Done (evidence in CHECKLIST_DONE.md): T1 T2 G1 I1a I1b I1c C1 C2 G4 G6a G6b G6c S3 D3 G5
- [ ] I3 movie audio: ATRAC3plus decoder wired (A61 log "ATRAC3plus audible"), not verified by ear
- [ ] I2 tutorial/intro flow without skip overlay: movie -> race c204 loads + TutorialDialog name entry (A64,
  play_a64tut_20261126_120625); cellOskDialog stub never answered, now does (play_a64osk_20261126_124112)
- [ ] W5 workaround: cellOskDialog has no input UI, auto-confirms with initial text or PS3_OSK_TEXT (Player)
- [ ] G8 tutorial race: window flickers between a stale UI frame and a broken 3D frame, dialog state unreadable
  (A64; guest buffers 0/0x660000/0xCC0000 hold only dark 3D, work/_a64/fb3.png)
- [ ] G6d showroom washed out (parked A58, bypass: SPU upload off, SPU_FB=1 shows it): job input 0x60579000 =
  NV3089 of RT 0x022C0000 is noise (guest VRAM seed), also with split surface slots (a58 patch)
- [ ] D4 rest interpreted, car view 5 FPS: image 76 LS 0x108EC/0x7D28/0x8048, image 74 0x54BC, PM 0xA68
  (play_a55lift2_20261126_061944)
- [ ] G7 popup bar draws several popups on top of each other (work/_a55/home_after.png): check vs real
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
Overlays (env `GT6_VOL_ROOT`): a32 = plain 1.22, a35 = +ColorBegin bypass, a40t = skip tutorial,
a45 = skip tutorial+opening (play.py default). `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Never modify work/gt6_vol or gt6_vol_122+.
Car repro: play.py start, work/_a53/to_home2.sh, work/_a53/dealer.py.

## State

- (A46) Main menu reached: GT Mode home, Ver. 1.22. Frame work/_a46/main_menu_home.png; overlay gt6_vol_a45 (skip tutorial + opening), pad X 220..395.

## Next step
G8 first: map flipped display buffer 0/1/2 to the host image presented (rsx_d3d12_backend.c, spu_fb_upload only
handles buffer 0; SPU post-process writes guest VRAM, G6d). Then finish I2: name entry (to_name.sh in work/_a64,
overlay a40 = movie skipped), O.K., race, Home. PS3_OSK_TEXT default is built, not yet exercised.

## Refuted / symptom (do not repeat)
"Dealer load hang" (A50-52) = attract demo.
Quit flag, userdb, exit race, Hyp. 1-116. More: LEDGER §4.
Never run GTToolsSharp/PDTools.
