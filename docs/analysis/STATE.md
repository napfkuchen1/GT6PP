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
- (Arbeit19) CORRECTION: PDIPFS/9 + fdup gap already known (Arbeit11): default hdd0 lacks 9/ tree; use -Hdd0Src work\gt6_hdd0_rp. With rp data main still creates all threads inline (13D94->A521CC script run).
- (Arbeit19) tid30 9qstY = frame pacer loop 8A7C6C/8A7B90 (not a task worker). GPROF rp run: after ~10 s all threads idle, tid1 gone. Script run in 13C44/13D94 ends ~12 s, then finalize. Next: script-native sequence ours vs Oracle.
- (Arbeit20) AUDIT: default hdd0 PDIPFS 25 MB/234 files (no 9/, no PATCHSEQUENCE/UPDATENODEINFO/FIXEDELF114/replay); rp = 14 GB/17026 files (9/ = 12 GB, 13363 files). rp is the complete installed 1.22 data; saves GT6_1.N (oracle) vs GT6.N (ours, name built by guest %s.%d).
- (Arbeit20) probe arb20_nopfs (rp, GT6_PFS_OVERRIDE=0, lang en-gb): only 16 opens, stops after K/2F, no 59/FI -> override off is WORSE (guest PFS decrypt path), keep override on. Data hypothesis closed again.
- (Arbeit20) Save prefix GT6 vs GT6_1: no literal in EMAIN.elf (fmt "%s.%d" x3 @0x11a9660/96e2/9f72; LEDGER '@F87934' was wrong) nor plaintext in gt6_vol -> prefix comes from decrypted PDIPFS/script data. Even with rp data (has GT6_1.N) ours opens GT6.N: first data-driven divergence, find source.
- (Arbeit21) CORRECTION: Np2Init DOES run in ours (HLE sceNp2Init -> sceNpInit; new log '[sceNp2] Init' line before '[sceNp] Init', same slot as oracle). IsLoaded(0x45) is NP_TUS in a dtor path (B4D668), not an init gate. Np2 lead CLOSED.
- (Arbeit21) MNetworkPlatform.initialize = native 9BB1DC (script-called); NP2 mgr method B4ADE0 not hit by CALLTRACE_TO. Oracle AutoLoad2 -> -4 twice (CBRESULT 0x8002b401); ours 1st returns NODATA, 2nd loads GT6.0-5 (result 0): savedata return code differs.
- (Arbeit21) Neutering PDINetwork.finalize 9AD1DC (A21_NOFIN) changes nothing: Term still runs via B4AD4C<-B4B114<-A081B4<-9AD598<-A1EA64<-102BE4C<-A7BF50 = whole-app teardown (task engine A7BF50 ends). Finalize guard is not the quit cause; ask why A7BF50 run ends.
- (Arbeit21) Full term chain: B4AD4C<-B4B114<-A081B4<-9AD598<-A1EA64<-102BE4C<-A7BF50<-A1EAD0<-14900<-13FD0(shutdown)<-1096C<-1024C. Main body 14010 = stage list each followed by AD2998 check; shutdown 13FD0 follows when a stage returns. Save result reader AF5164/AF5318 (obj+0xb0) are accessors for script natives. Next: which 14010 stage returns first (log stage entry/exit via CALLTRACE_FROM or snapshot) and its exit reason.
- (Arbeit21) 14010 stages ALL return in order (A21STG probe): 13DE4 holds script run (log l.279-413), 146E8 returns at once (AFDFC0 boot check passes: +0x31 title strcmp match), rest fast. Not a quit: script/task-engine run in 13DE4 ends early. Next: why A7BC50 task engine (A2F700) ends ~12 s.
- (Arbeit21) CORRECTION: 14010 stage list ALL return in order (probe A21STG); main exits via shutdown 13FD0 right after 1414C. Stale APPLOOP hooks were in the old exe (obj of 026): fixed by touch+rebuild.
- (Arbeit21) AFDFC0 boot check: block@0x179ECF0 +0x30=1,+0x31=1 (title BCES01893 == obj+0x194) legit -> 146E8 returns at once. BFF0A0 (1414C) = app main: callbacks default (id4 setter BFD924 only called by BFD8F4 defaults; no-op 109AD14) = by design.
- (Arbeit21) Oracle main_thread: after ZYWAP(75.77s) creates -SBXs, opens K/CF + 9/56/PW, rsx_iomap(75.98s), then silent (no syscalls) until exit. Ours: stages end in ms, shutdown. Oracle blocks somewhere in/after 1414C or inside 13FD0 (A7BF50 engine?). Unknown.
- (Arbeit21) KEY: thread names deterministic; oracle: Z-9m6,Z-9mI,Z-9YS,PDI* created by worker 9qstY; ours: same names created by tid1 (create-bt via PS3_THREAD_BT: 13D94->A521CC->A7E6CC->A7E5F4->A7BC50->A30028 poll A2F290(task) -> A2F700 engine -> 6171FC). Only tid1 calls the A2FFCC wait loop; poll states 1(15x)/0(5x).
- (Arbeit21) Meaning: ours main pumps tasks itself in A2F290; oracle main silent 30 s (lwcond wait) while 9qstY runs 6171FC. Next: what in A2F290/A2F700 lets a worker (not main) take the game-loop task; check +0x28/+0x64 task fields and who (tid) enters A2F700.
- (Arbeit21) A2F290 = cooperative task poll: runs task body via A2F0AC (type switch + vcall) after setjmp C61F88==0 (fiber/coroutine tasks on caller stack). In ours tid1 polls and runs game-loop task inline. Find why in oracle main polls but blocks (lwcond) / worker 9qstY owns it: check A2F290 claim fields (+0x28 state, +0x64 owner) and A2EA5C/A4F938.
- (Arbeit21) Only tid1 ever runs task bodies (A2F0AC via A2F290; A21RUN), no worker ever; 300 ms sleep before main's poll did NOT let a worker claim -> not a race. Main ends in shutdown 14884->AAE0F0->AB03B4->AC7AF4->AC7418->AE2844->lwcond wait (waits workers), workers idle in AE2844 wait (AD4924<-AF0B94). Next: how task is queued to worker vs inline (A2EA5C, A4F938, A8548C; config/flag deciding multithread mode).
