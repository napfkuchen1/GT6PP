# GT6PP EU - STATE (entry point, keep under ~5 KB)

State: 2026-11-23. Branch `eu-first-build`, main checkout. Disc EU `BCES01893`. Line: only game 1.22 + ps3recomp v0.20.
Rules/pitfalls: `CLAUDE.md`. Facts/canon: `LEDGER.md` (search with grep). Checkpoints C0-C6 + run table: `PROGRESS.md`. Hooks 1.00 vs 1.22: `PORT_HOOKS.md`.
Old history: `ARCHIV/docs-analysis/STATE_full_2026-11-22.md`, `eu-boot-log.md`. Maintenance: one line per finding (<=200 chars), move old lines to eu-boot-log.md.

## Goal
Main menu (C6). Reached so far: C0. ALL 1.22 runs FAIL at C1 (no visible image). AdjustScreen/input/spinner only known from the discarded 1.00 line.

## Method (since 23.11.)
Layer by layer, 1.00 reference `git show 6697a6d:<path>` -> port hooks to 1.22 (tools/port_hooks.py, scripts/post-lift.ps1). Next layer only after evidence (capture/log).
Baseline probe: `scripts\probe.ps1 -Name x -Boot notut -Seconds 90`; never mix `-Boot orig|noadj|notut` in parallel (boot.adc is shared).

## State
- C1 FAIL: capture frame 3500 black (1 draw, 0 nonblack). b5b260 cache fill (p4) ported, no effect, no 59/FI open.
- Binary still carries diagnostics (022/023 generated are clean, diagnostics in work/_bk_*): run `scripts\build-all.ps1` before a baseline.

- MAIN LOOP 146E8: task AFDFC0 = boot check (strcmp BCES01893), legitimate, 0 iterations. Details in eu-boot-log.md.
- GAME LOOP 1.22 = 0x616C80 (1.00: 568800), thread entry 6170AC, tick 68FF84, running (tid1/tid30); details in eu-boot-log.md.

## Next step
(Arbeit10) Term = script/project call PDINetwork.finalize (9AD1DC) in tid1 via 13C44..A2FFCC, details in eu-boot-log.md "Arbeit10". Find the condition before it.
Open hook anchors: PackageNullGuard 5F81B0 (1.22 anchor by signature from work/bin/_t100.elf), H113 A25C64 (no 1.00 code in git -> discard). Then SPURS walker, a3, AdjustScreen REALFLAG, ZWAP.

## Refuted / symptom (do not repeat)
Quit flag 0x1796DC8, savedata fileBuf, sceNp Term, task state 0x28, userdb/initUserDB (never reached), IsExitGame, AD4294 listener, Hyp. 1-116, PRIO_START/LOCKSTEP, exit race.
Script VM addresses 9EEA88/9F0748 are 1.00 (0 calls in 1.22).

## RPCS3 oracle (same EU disc; reaches C6)
- After AutoSave2: open PDIPFS/59/FI (535 MB film), then Pamf/Dmux/Vdec. Our hdd0: PDIPFS 24 MB, no 59/FI. RPCS3 data as hdd0: negative -> data is not the cause.
- Spinner state (old): 37 threads parked, 29 in sys_lwcond_wait (pc 0xA4305C); trigger of the 59/FI request unknown.
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), gt6_gprof (GT6_GPROF=1), PAD_LOG, scripts/live-padlog.ps1, tools/adch_disasm.py. probe kills gt6 via taskkill /T.

- (Arbeit14) a8[4] resolved: ctrl+0xa8 = CellSaveDataStatGet (AF5260/80/A0 = funcStat wrapper, r4=GetStat), [4]=isNewData. =1 with missing dir is correct (same as RPCS3). No bug in the HLE.
- (Arbeit14) Next: SaveDataUtil.load return array [?,success,?] + caller/retry loop (main.adc 69143 ff, adch_disasm) -> which error path leads to PDINetwork.finalize/Term.
- (Arbeit14) Term guard (GT6_NP_NOTERM, sceNp.c): Term = start of shutdown (then IsLoaded NP2, SetInvalidateTile), not a decider. Quit comes after 2 failed loads. NP_TERM_BT yields nothing.
- (Arbeit14) ORACLE FINDING: GAME6 load 1+2 -> funcStat -4 (each ~0.2 s), load 3 SUCCESS: SECUREFILE GT6_1.0..N (16 MB) read = the Oracle has a REAL save. We: no save -> first-boot path -> quit. Next: save fixture (PARAM.SFO+GT6_1.N in gamedata GAME6) or check first-boot path (AutoSave2 BKUP6 instead of quit).
- (Arbeit14) Oracle save (RPCS3 savedata/BCJS37016-GAME6 -> work/_gd_oracle, PS3_GAMEDATA_ROOT) is loaded: load1 -4 like Oracle, load2 result 0 + all GT6.0-5 read. BUT sceNp Term runs IN PARALLEL with the file ops (line 609, before GT6.4) -> save chain = red herring; Term comes from tid1 main() return/finalizer (Arbeit6/10).
- (Arbeit14) Open: Oracle reads GT6_1.N, we read GT6.N (prefix). Next: why does main() 0x14010 return after ~12 s, while Oracle main_thread stays until quit (1:46)? Compare stage returns/wait in main.
- (Arbeit15) After AutoLoad2 the Oracle calls NetStartDialog/Music/Trophy/Entitlement/AutoSave2 in thread 9qstY; we only sceNp2Term. Main loop 146E8 kept open (A15_LOOP): it lies BEFORE AutoLoad, no effect (C1 FAIL). Details in eu-boot-log.md Arbeit15.
- (Arbeit15) Next: who starts 9qstY actions on the Oracle (NetStartDialog callers B494C4/798C70 via CALLTRACE in the Oracle-equivalent task 40393C90 step 21); find the 798C1C state setter.
- (Arbeit16) snap_a8s50 tid30 = in consumer wait 8A7AD0 (stack ret 8A7B08): obj 7FFCACA8 +0x1d8=31 < +0x240+1=38, waits. Producer writer 8A88E8 (std 0x1d8). Details eu-boot-log Arbeit16.
- (Arbeit16) Next: caller/entry of 8A88E8 (which job/thread increments 0x1d8, why stalls at 31); compare Oracle increments via CALLTRACE on 8A88E8.
- (Arbeit17) WORKAROUND 8A7AD0 consumer wait skipped (tools/guard_conswait.py, post-lift; opt-out GT6_NO_CONSWAIT). Probe arb17_conswait notut 320s: guard fires, NO load progress (no PDIPFS/59/FI, Pamf, Vdec, non-black). Same 16 SPU mfc-list STALL img=5 as baseline a15loop.
- (Arbeit17) Next: PS3_SNAP_AT never fires (3 runs). Fix arming (ppu_loader.cpp:3581 lv2_syscall) or use PS3_WD_AT-style trigger, then snap_diff.
