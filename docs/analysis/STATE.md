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
- [ ] G1 only dealer tile drawn: popup says "buy a FIT RS '10 first" (A53), likely locked; confirm after first buy
- [ ] I1 opening movie: cellPamf layout fixed (A50, patches/gt6-a50-pamf-header.patch, not run); cellDmux is a stub, no FFmpeg headers
- [ ] I2 tutorial/intro flow runs without skip overlay (remove gt6_vol_a45 skips)
- [x] C1 pad menu: popup X, enter dealer (~7 s load), Honda car list (A53 live a53c: work/_a53/dealer_list.png,
  dealer_honda_cars.png). Old "dealer hang" = idle attract demo (leavedemo) started before cross was pressed.
- [ ] C2 car detail view stalls after picking FIT RS: flips stop, same chain as S1 (a53c run.log.err 2842..2874)
- [ ] G2 car-name text in dealer list smeared/overbold (work/_a53/dealer_cars_full.png)
- [ ] G3 dealer tiles: grey backing covers only upper-left part of each tile (same frame)
- [ ] D1 attract demo (autodemo race) loads very slowly, window FPS 0.29 (a53a)
- [ ] D2 idle demo starts ~10 s after Home; input during the countdown does not cancel it (a53b, a53i): check
- [ ] S2 boot crash 0xC00000FD, recursive tree walk func_00AE0464 on tid34 (play_a53g_20261126_035132, 1 of 8)
- [ ] S1 stall (pre-menu, car view): SPU img 5 polls label 0x53; cause = ignored ACQUIRE (A54), W4 verify over runs
- [ ] W4 workaround: GCM_SEMA_BLOCK=500-560 (gt6 main.cpp); blocking all ACQUIREs breaks on label 0xFE0
- [ ] W1 workaround: interpreter bodies spliced into gen 037; confirm with a full re-lift (patches/gt6-a51-jt-loop-base.patch)
- [ ] W2 workaround: PPU_ONECORE=1 default (one-core pinning); run without it
- [ ] W3 workaround: GCM_PARK_GRACE_MS=5000 in gt6/src/main.cpp (FIFO self-JUMP resync), see S1
- [ ] L1 live non-headless run, persistent save, real pad input

## Method
Overlay `work/gt6_vol_a32` (scripts/make-vol-overlay.py), env `GT6_VOL_ROOT`; `PPU_ONECORE=1` default; probe.ps1 gives empty hdd1.
Batch tools: scripts/boot-batch.ps1, boot-outcome.py. Never modify work/gt6_vol or gt6_vol_122+.
Menu questions: scripts/play.py (start, press, wait, shot, status, dump [--snap], quit); work/_a53/to_dealer.sh drives
boot->dealer in ~175 s. Car repro: start, sh work/_a53/to_home2.sh, python -I work/_a53/dealer.py (focus detect,
a53j OK). Idle demo starts ~10 s after Home ("Der Demofilm startet in Kuerze"): cross must come before it.

## State

- (Arbeit46) Next crash a46fix: host stack overflow 0xC00000FD in SQLite on a guest ctx fiber (4 MB) -> HOST_STACK 32 MB.
- (Arbeit46) Legacy sqlite step returns rc=1; real code = Vdbe+0x5C, message +0x38. sqlite3CorruptError = BD532C (r3=line).

- (Arbeit46) MAIN MENU REACHED (C6): a46menu GT Mode home "Zuhause", Ver. 1.22, tiles + popup GT003_GET_FIRST_CAR.
  Frame work/_a46/main_menu_home.png; overlay gt6_vol_a45 (skip tutorial + opening), pad X 220..395.

## Next step
A54 (play_a54pt2/a54fix): SPU img 5 waits label 0x53 == 1 then writes 0; walker ignored the ACQUIRE (wait 0),
so releases got lost. With GCM_SEMA_BLOCK=500-560: 0 SPU halt (1 run), 1 acquire timeout at t=194 s, car view
still stops (flip 5416). First next fault: tid30 null reads in C4797C, null call lr C479E8, then park io 1A6A5F0.
Do: disassemble C4797C/C479E8 and its caller (reservation/buffer-full path near C49034?), find who leaves the
object NULL. Repro: play.py start --env GCM_PARKTRACE=1; to_home2.sh; dealer.py (~6 min).

## Refuted / symptom (do not repeat)
"Dealer load hang" (Arbeit50-52, tid30 interpreter, file opens) = attract demo. Post-save movie stall (Arbeit40). Quit flag, savedata fileBuf, sceNp Term, userdb, IsExitGame, Hyp. 1-116, PRIO_START/LOCKSTEP, PRIO_MAP, exit race.
Arbeit22-30 1.00-script/A22_BLOCK task chains (B90, node flush, MMuseum2, PFS pipe): obsolete since 1.22 overlay.
Script VM addresses 9EEA88/9F0748 are 1.00. Never run GTToolsSharp/PDTools.
