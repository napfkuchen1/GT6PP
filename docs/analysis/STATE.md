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

- (Arbeit18) SNAP_AT fine; earlier runs killed by parallel probe.ps1. Single run arb18_snap140 -> then snap_diff vs a15loop.
- (Arbeit18) snapshots work: tid30 only diff (guard -> timed poll loop AD3200..AD323C). Next: who feeds producer 8A88E8 = parked threads' common lr AF0CB4 (x20) / B03BE8 lwcond waiters; xref callers of 8A88E8.
- (Arbeit18) SNAP_AT works (parallel probe killed earlier runs). Snaps guard/base/a15loop: tid1 in finalizer 13FD0 always; 8A7AD0 guard = symptom, drop. Next: why main 14010 returns/A15_LOOP not holding (verify env in build), compare stage returns vs Oracle.
- (Arbeit19) CORRECTION: Arbeit16 'consumer stalled 31<38' was a bad dump (7FFCACA8 not an object). Real obj 7FFCAAB0: 0x1d8/0x240 advance ~62/s, tid30 game loop is in 60 Hz lockstep with tid29 (tick cond). conswait/8A88E8 chain closed.
- (Arbeit19) Next: why per-frame chain 6C7664->798C1C runs only 10-99x though loop runs 1000s of frames (who stops calling 6C7664's parent / which state gates it); verify call count via snapshot diff, not log patch.
- (Arbeit19) KEY: ours main tid1 runs game loop 6170AC INLINE (bt: 13D94->A521CC->A7E6CC->A7E5F4->A7BC50->A30028->task engine A2F700->7A0AC0->6171FC). Oracle: worker 9qstY runs it, main waits. Check A7E5F4/A7BC50 submit-vs-inline decision.
- (Arbeit19) opendiff ours vs Oracle: Oracle never opens PDIPFS/K/*.fdupm/.fdupi or PDIPFS_bdmark (only unlinks, ENOENT); reads installed PDIPFS/9/* from hdd0. Ours: per-file disc->hdd0 dup loop (28 fdup opens by 90 s, 174 fdup files in hdd0), last open K/J4.fdupm.
- (Arbeit19) Next: is ours stuck/ending in the PDIPFS dup (install) loop? Who decides dup vs direct open (PDIPFS_bdmark check, xref callers of the fdupm open path); test run with Oracle PDIPFS/9 tree if obtainable; get_user_memory_size check inconclusive (our runs log no [sys_memory] at all).
