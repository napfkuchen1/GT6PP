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

- (Arbeit22) With mmapper fix main now returns from 14900 (inside 13FD0 main seq 1412C,14900,141C8,890A9C,914330,91E430,14794 terminate,14884 shutdown) right after loading arcade/option/gtmode/garage/gtauto.mpackage (54 opens) -> shutdown (join tids, AB03B4 waits). Menu never runs: find why 14900 returns (quit flag/error). tools/trace_enter.py logs fn entries.
- (Arbeit22) MGOM loop 6170AC runs fine (iterates on tid30, state 0). Main exit is legit flow: root task A2F290 body (7A0A54->6171D0 MGOM.start) returns, A2FFCC join returns, A7E1A4 cleans up, 13C7C main returns -> 14794 terminate. Oracle main instead stays silent (blocked). Missing: task steps after MGOM.start (A2EA5C state machine / A5C070/AA55FC next step) must block or continue in oracle.
- (Arbeit22) Next: log A2EA5C task state transitions on main after 617218 (state before/after, return of A2F290 and A2FFCC r3); compare with who should keep main waiting. Also check root task re-arm: AA41FC+0x1A8 return path.
- (Arbeit22) Main task A2F290 ret=0 (state 3 done) -> A2FFCC exits; MGOM.start 6171D0 does NOT block (ack from 616C80 vcall144=619638 init, <1ms, tid30). Forcing ret 2 on tid1 (A22_FORCE2) = fewer opens (22 vs 54): refuted.
- (Arbeit22) Main blocked after MGOM.start (oracle emulation, env patch at call 7A0AC0): no Term, flips run, 49 opens, workers all idle on events (AD8C08/AC1C78/AE2844), tid38-40 ended. Load stalls: nobody enqueues next work. Loader 3rd AutoLoad thread (oracle) missing.
- (Arbeit22) Next: strategy change: diff oracle vs ours thread create/event sequence after MGOM.start (who signals worker events AC1C78/AD8C08 in oracle); or check why tid38-40 end (AF0B94+0xE8).
- (Arbeit22) MILESTONE: PUMP_ITERS=0 + main blocked after MGOM.start (A22_BLOCK, call site 7A0AC0 in ppu_recomp_016): frame 6000 shows 'Sony Computer Entertainment presents' fade (non-black 1%), first real render. probe_a22cap_20261124_171454_1. Next: longer run (frame 14000), see if boot project advances to title/menu.
- (Arbeit22) Presents frame is FROZEN identical from frame 2000 to 14000 (hash same, 2 draw ops/frame). Not time (timebase real), not vblank (handler 47A24 called ~1/flip), tid30 runs per-frame update (ADB780). No loads after DialogProject/ConfirmDialog/ProgressDialog gpb. Next: find what scene waits for (fade/anim state var, or next-project load request); snapshot diff 60s vs 120s of MGOM objects; check A22_BLOCK is promoted to a runtime default (gt6/src) only after menu path verified.
- (Arbeit22) Snapshot diff 60s vs 130s (snap_74375109 vs snap_74601453, PS3_SNAP_AT takes ONE time, run twice): only 31 pages changed = heap churn + PRNG at 17BDD14; no scene var found. tid30 per-frame ADB780 dispatches a single target ADB918 (queue/task pump). Next: walk what ADB918->ADA4C0->AFB6B4 pumps (which task/vtable objects), find the Presents scene object (draw ops 2/frame) and its fade state; try snap_walk from the draw call owner.
- (Arbeit22) Pad CROSS presses at 30/50 s do not advance Presents (visually same, 49 opens): scene not waiting for input.
- (Arbeit22) WD@40s threads with game chains: tid30 ADB780>ADB918>ADA4C0>AFB6B4>AFD93C>ADC1C8 (pump), 8A6C00/8A89C8/8A9194 (wait), 91A56C, 910BD8, AF86E8/AF8794/AF8810 (C4537C = timed waits). Candidates for the Presents wait: 8A6C00 chain, 91A56C.
- (Arbeit22) 8A6C00 = plain condvar idle wait of worker 8A9194 (tid27), not the Presents blocker. Remaining: 91A56C; else find Presents scene object via draw caller.
- (Arbeit22) 91A56C = worker job-loop idle (lock+condvar wait B03BAC), not the Presents blocker. All idle waits ruled out; next: find Presents scene object via draw caller (RSX draw ops 2/frame) and read fade state.
