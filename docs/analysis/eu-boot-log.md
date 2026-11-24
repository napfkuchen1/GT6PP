# EU disc (BCES01893): first build and headless boot

Setup and result of building GT6PP from a clean clone and running it against a
user-owned EU disc dump. Complements `eu-bces01893-compat.md` (static checks)
and `repro-gaps.md` (what was missing to get here).

## Build

- ps3recomp `v0.18.0` + `patches/ps3recomp-gt6-runtime.patch`, LLVM-MinGW from
  `scripts/build-gt6.ps1`. Two things about that patch: the file is UTF-16 and
  has to be converted to UTF-8 first, and its `rsx_d3d12_backend.{c,h}` hunks do
  not match `v0.18.0` (excluded with `git apply --exclude`; the headless run
  does not use that backend). It already contains the `ps3recomp-mingw-seh`
  hunks, so the two must not both be applied. A first build with only the
  MinGW patch is described under "First attempt" below.
- `functions_corrected.json` regenerated with `tools/find_functions.py` and
  `tools/boundary_audit.py` (70,823 functions), then `scripts/relift-gt6.ps1`.
  All post-lift patches applied; `add_boot_presents_hooks` needed the
  per-function fix from this branch.
- Embedded SPU ELFs: `extract_spu_images.py` + `build_spu_workloads.py`
  (same four offsets as the docs, `spu_workloads.c` came out identical).
- 15 SPU job images: cut out of the decrypted `EMAIN.elf` by fingerprint (see
  `repro-gaps.md`), then `scripts/lift-spu-jobs.ps1` (6,562 functions).
- `scripts/build-gt6.ps1` links `gt6/build/gt6.exe`.

## Run

`PS3_VERBOSE=1`, `PS3_HEADLESS=1`, `scripts/run-gt6.ps1 -Seconds 90`, disc tree
with `PS3_GAME/` from the EU disc and `USRDIR/GT.VOL` as a hardlink to the
copied volume. The first table is from the first attempt (v0.18.0 + MinGW
patch only), which ran about 6 seconds; see below for the second build.

| Observation | Value |
|---|---|
| Title id read from `PARAM.SFO` | `BCES01893` |
| `BootCheck` | `type=1, titleId='BCES01893'` |
| `GT.VOL` opened via `/dev_bdvd/PS3_GAME/USRDIR/GT.VOL` | yes |
| Update-overlay lookups | `/dev_hdd0/game/BCES01893/USRDIR/PDIPFS/K/{4D,E9}` opened |
| `cellSpursInitialize` | "PDI", 5 SPUs |
| WWS workloads added | `Wws_Job` / `ElemSetRenderHP`, `ElemSetRender`, `ElemSetUpdate`, `ElemSetGeneral`, ... |
| `[spurs-job] dispatch HIT` | 56 |
| SPU dispatch misses / `NOT LIFTED` | 0 |
| Distinct job images hit | 6 (`1B6BDAC375C5438D`, `ABD49FC58F53F368`, `C1E79DAD1A299848`, `CB9BD0241BB0DE67`, `F523F26F69764538`, `FDFFAAC1BCD5352E`) |
| `unresolved indirect call` lines | 181 (same kind as in `CONTINUE-HERE.md`) |
| Display | headless, no RSX backend; nothing was rendered |

<!-- shortened 2026-11-23: middle part see ARCHIV/docs-analysis/eu-boot-log_full_2026-11-23.md -->

## 2026-11-22 - Hyp. 28 (job list at the cancel branch)
[C28] in func_00987A28 @loc_00987E54 (patch patches/gt6-h28-cancelzweig.patch). All cancels: obj=r23=r25=r28 (40007A10/40007C90), obj+0x28=1, obj+0x30=0, g(0x15DE27C)=0, r22=obj+0x6c, begin(obj+0x70)==end(obj+0x74) -> vector empty, capacity begin+0x28 (heap with old strings). Wait loop (0x987E34..0x987E50) only waits on a non-empty vector. Next step: find the filler of the vector.

## 2026-11-22 - Baseline switch + Hyp. 29/30
boot.adc set to nodlg_noadjust (copy work/ARCHIV/boot.adc.nodlg_noadjust; previous full patch in work/ARCHIV/boot.adc.patched_full_*). 3 runs 320 s: tutorial race loads (race.adc, race_tutorial, Template.gpb, only sgb 0449), frame 5000 GT logo loading screen, no sound loop; STACKSCAN main thread identical to Hyp. 24 -> same task-wait cause. Hyp. 29: 987A28 calls vtable+0xdc of the executor (obj+0x34), which pushes 1 job into obj+0x70/74 (v74=v70+4); dispatch 98787C -> poll 9EEA88 (executor obj+0x68); job result 0/1 never 2, vector empty afterwards -> cancel. Hyp. 30: poll sets o24=0 (task state 3) / 2 (state 2) / otherwise runs the job (from 0x9EEB04). Patch: patches/gt6-h29-h30-joblog.patch.

## 2026-11-22 - Hyp. 31 (job poll 9EEA88 per object)
[P31] before/after handler bctrl 0x9EEC3C in func_009EEA88 (script: patches/gt6-h31-polllog.py.txt, Python insert script, no diff because of CRLF). 2 runs valid. Poll is script VM: ip=[exec+0x1c] rises +4/opcode, handler table 0x1487660. Tasks 40007A10/40007C90/40007990 execute opcodes (incl. 0B,26,25,1D,32,33,0C,03,39,05,24,1C), o24 stays 5 -> VM runs normally. Only o24 change: opcode 0x37 (handler 9ED204, = script return/end) sets task+0x24 = 1 (at 40007C90, ip 40295538/40295590/40387BF0). Result 1 instead of 2 -> done event never, cancel. 40007A10/40007990 never reach 0x37 within the 60 limit.

## 2026-11-22 - Hyp. 32 (opcode 0x37 status value)
Static: handler 9ED204 (script return): script instructions are 8 bytes (w0=op<<24|operand, w1=argument). Handler reads w1=[ip+4]; values 1..3 -> pop result value from VM stack into promise task+0x20 (979290), then task+0x24 = w1; otherwise task+0x24 = w1 directly. Dynamic [P32] (patches/gt6-h32-op37log*.py.txt): op37 at 40007990 always has w1=0 (80 hits, 2 runs); at 40007C90 w1 was 1 (Hyp. 31). Jump table 0x1419550 (switch on obj+0x24 in 98787C): 0->987914 (98604C step, then loop), 1->98792C (985FE0 test + 98604C), 2,3->987A08 (RETURN result = done/fail), 4,5->9878B8 (repeat poll). So: return status 0/1 = "step done, fetch next job" (98604C), only 2/3 ends the task. The task waits for a further job/step; the vector (obj+0x70..0x74) becomes empty after the one job -> cancel.

## 2026-11-22 - Hyp. 33 (98604C / 985FE0 / job stack)
Static: vector obj+0x70(begin)/0x74(end) is a **stack of job objects** (4-byte pointers). 985FE0(obj) = peek: top=[end-4], calls top.vtable+8 (status). 98604C(obj) = pop: calls top.vtable+0xc and +4, end -= 4 (only if >6 bytes... size check). 9860D4 wrapper: while status!=2 {pop; empty -> return 1}; status==2 -> pop + obj+0x68.vtable+0x18(arg) -> return 0 (success). Dynamic [P33] (patches/gt6-h33-peeklog.py.txt, 2 runs x 62 hits): top job always has vtable 0x14875B0 (contains 0x9EEA88 = poll at +0x14, i.e. job object = VM/executor class), vtable+8 -> 0x8A1BE8 = `li r3,0; blr` (stub), status always 0, never 2. Stack depths: 40007990 5 entries, 40007A10/40007C90 1. Thus the wrapper path can never report success; done must come via obj+0x24=2/3 (script return opcode with w1=2/3, or another handler).

## 2026-11-22 - Hyp. 34 (handlers that set task+0x24)
Static scan of handler table 0x1487660 (patches/gt6-h34-scan.py.txt): direct setters only 0x37 (return, o24=w1), 0x1F/0x28 (o24=3, abort), 0x1B (o24=w1), 0x06/0x0F/0x2C/0x3E (o24=5 via 9F095C). Dynamic [P34]/(patches/gt6-h34*-*.py.txt, 2 runs): o24=2 IS reached (opcode 0x37 with w1=2, 21x at 40007C90, 1x 40007C10, ip 403B22F0..403B2858) -> 2 is return from a nested call, not task end. The dominant state is o24=4 via opcode 0x06 (handler 9F0748, 251x 40007C90, ip 403A6628 alone 120x): 0x06 = sub-call/child job: submits child via executor vtable+0xdc (args from VM stack), child future at [sp+0x78]; if child+0x24==1 -> sets o24=5 (continue), else o24 stays 4 (dispatch case 4: repeat poll, ip stays at opcode, child is re-checked/re-submitted on every poll). So the script hangs in 0x06 on a child whose +0x24 never becomes 1. Main-menu blocker = child job (target unknown).

## 2026-11-22 - Hyp. 35 (child job at opcode 0x06)
[P35] in func_009F0748 (patches/gt6-h35*-submitlog.py.txt; variant b filters task 40007C90). Opcode 0x06 = **call native function** via callee object (r3) with callee.vtable+0xdc: targets 9B0918 (vt 01483EC8, result immediately st=1 -> o24=5) and 9B89D8 (vt 01484968; wrapper, delegates to object [callee+0x14] vtable+0x54, args r4=result slot sp+0x78, r5=w1, r6=arguments) as well as 9A0178 (vt 014851B0, st=1). The result object [sp+0x78] is the task itself (child=40007C90); st=[task+0x24] after the call. **st=4 (pending, repeat poll) only occurs with 9B89D8 calls** (callee 4037EC28, 4049AE20/AE80/AF28/AF10, 403AD8E0, ...), 9B0918 calls return st=1. The hang ip 403A6628 from Hyp. 34 lay outside the 120-entry log (cap exhausted too early). Target object [callee+0x14] and its vtable+0x54 method still unknown.

## 2026-11-22 - Hyp. 36 (snapshot tool PS3_SNAP_AT)
Patch patches/gt6-snap-at.patch (ppu_loader.cpp thread + runtime/diag/ps3_snapshot.c): after N s all committed VM regions (reg_<ea>.bin, regions.txt, ~1 GB), thread regs/stacks, sync tables. Run snap2 (work/snap_run2, 200 s, notut) valid.
Finding: threads 2-40 in lwcond_wait/syscalls (130/141/107), main thread in cellFiberPpuWaitFlag. Mutex: 10 active, all owner 0. Sem: 8 with value=0 (max 1024), no waiters. evq5 (key 0x23A0 = cellAudio notify) cap4 count4 without receiver (probably symptom, cf. Hyp. 19/20).
Wrapper search (find32 0x01484968): 111 objects, 110 with vtable 0x1487348 -> slot 0x54 = 0x9E5FC0: bind trampoline, calls 0x9880BC(*arg4, this+0x14, [this+0x14]+0x34 ...) -> [x+0xC].vtable+0x28. Target function still open.

## Hyp. 37 - snapshot snap_run2 (200 s, notut): script task and target of the pending call
- Poll 0x9EEA88 belongs to 12 task nodes (vt 0x14875B0, poll +0x14); state object (vt 0x14811E8) +0x24 status, +0x28 state. Active task 400DB544 (parent 400C7F88), state 40007990 status 5.
- Bytecode: task+0x1c = ip (array of record pointers), record byte0 = opcode, handler table 0x1487660+24*opc+0x10. Last record before yield: opc 0x06 (arg 0x9A), then 0x36 (015DE7D8).
- Opcode 0x06 (0x9F0748): stack task+0x20 (base[0], top +0x1c) pop 2 -> callee 4037A844 (vt 0x1483EC8, +0xdc=0x9B0918), argument object 400E97F0 = string "gtmode".
- 0x9B0918 -> obj2 4009EFE8 (vt 0x1485B50) +0x54 = 0x9C625C -> +0x58 = 0x9C6184 -> functor obj2+0x14 = OPD 014CD330 = 0x6C54DC = MGOM.start.
- Manager 7FF01FC4: +0x48 = 1 (pending), +0x50 = "gtmode" -> request is never consumed. See boot-presents-fix.md 2.3.

## Hyp. 38 (offline, snap_run2): why the consumer does not run
- Main thread (tid 1) stands in menu_start_project: stack 0x568CCC/6C54CC/6C558C, wait chain A21D50 -> A21CBC -> A4305C (cond wait).
- Workers tid 28/35/43: lr=00A121F0 -> return from A187CC (lwcond wait in worker loop 0xA12170). Tick hook sits at loc_00A121AC (loop start) and fires only after a wakeup.
- No thread with 0x568658 on the stack; pump request hook (func_00568C94 entry) ok, but the tick is never driven.
- A21E04 (signal) -> A21D8C: if waiter flag +0x28 is set -> A42FFC (signal), otherwise +0x29=1 (pending). Pre-signal is kept.

## Hyp. 39 (probe_sync39_20261122_220806_1, notut, 220 s)
- Sync pump before 568CC8: "boot" (state 1->3->4->done, `sync pump done state=0` L7829), then "gtmode": project load gtmode.mproject, states 1,3,4,3,4...
- gtmode: `sync pump done state=4` (L29752) after 4000 iterations; state_after=3 3729x, =4 3538x, flag4C=1 load4D=1 -> sequence is ticked, never finishes (+0x91).
- Patches: gt6/src/stubs.cpp gt6_menu_project_sync_pump; tools/apply_gt6_post_lift.py add_menu_sync_pump (backup work/_bk_h39/ppu_recomp_012.cpp).

## Hyp. 40 (snap_h40, PS3_SNAP_AT=100 in the sync-pump build)
- Consumer 0x568658: state 3->4 CAS, ticks manager+0x1d4[0..2] via 5C406C, sets state back to 3 as long as +0x91==0; all done -> state 5.
- 5C406C: per tick handler[+0x88] from table 145D0D4 (5C1B3C,5BD718,5A8218,5B80DC,5B97A0,5A5BB0), +0x88++; ends when A13644()=1 (byte 0x164AB90 under mutex 164AB50) -> +0x90=1 -> 5C3EC4.
- Snapshot: objects 7FF0B000/7FF0B800/7FEAC000: +0x88=0, +0x8C=5/5/A, +0x90/91=0; 0x164AB90=0.

## Hyp. 41 (2026-11-22): done flag of the sequence objects
- Offline (snap_h40): only setter of +0x90 in the sequence code = 5A3AC0 (func 5A3AAC), callers: 5680FC (consumer exit 0x56886C/0x5E6D78) and 5A7A10 (generic weak-ref wrapper, called from 5AB428 with >20 callers). No handler sets it itself.
- A13644 reads byte 0x164AB90 = object 164AB80 (vt 146FA48) +0x10 under mutex 0x164AB50. Getter vt+0x8 = 3C0E84 (lbz 0x10(r3)), setter vt+0xC = C3FE14 (stb r4,0x10(r3)); no direct bl callers -> only indirect.
- Probe probe_flag41_20261122_222528_1 (GT6_FORCE_LOADFLAG=1, sync pump i==20 writes 0x164AB90=1): pump state -> 0, boot continues (cellMusicInitialize2, open game024.db). Then NULL deref in A21D50/A21CBC (return path 568CC8, waiter manager+0x18) -> exit chain code=0xFFFFFFFF.
- Interference worker hook vs. main pump: not measured separately (hook never fires per Hyp. 38).

## Hyp. 42 (2026-11-22): return path after sync pump, nature of flag 0x164AB90
- A21D50 (bl at 568CC8) after pump: r3=mgr+0x18 correct, but after A42DE8 (lock) r29=0 -> A21CBC reads NULL+0x29. Lock/HLE (ppu_sysprx lwmutex, gcm_pump) does NOT clobber r29 (diagnostic brackets probe_flag42d..i).
- Cause: DRAIN_TRAMPOLINE after the lock call executes a g_trampoline_fn left by the sync pump (cross-fragment fallthrough from func_00568658), which zeroes r3/r29.
- Fix: gt6_menu_project_tick drains g_trampoline_fn directly after func_00568658 (stubs.cpp). probe_flag42j: A21D50 after lock r29=7FEAC018, boot continues.
- Afterwards exit chain code=-1 lr 7F9588 = func_007F9520 (ppu_recomp_018): if byte +0x95E==0 and A13644()!=0 -> +0x95E=1, time (A2F308) to +0x960; later (now-stamp > 0x97FDF) -> func_00F9A080(-1) = exit.
- Conclusion: 0x164AB90 = quit/abort request with grace timer, NOT "project done". The sequence objects terminate on quit; GT6_FORCE_LOADFLAG remains a pure diagnostic tool (it causes shutdown).
- Real done setter for +0x91 still unknown -> Hyp. 43.

## Hyp. 43
5C3EC4 (finalizer) sets +0x91=1; callers: 5C406C (only when +0x90 set by A13644/quit) and shutdown 5FBAF0. Loop 568800 = main game loop, ends only on quit. Hang = no menu rendering in the tick, not a missing done.

## Hyp. 44 (game loop, pump unbounded)
- GT6_PUMP_ITERS=2000000: >15600 iterations, state 3/4, ~2193 flips/320 s, frame_00 = legal + logo + spinner (probe_pump44b). No menu frame.
- Back trace track opens (009F8E40, probe_bt44): 009F7204<-009F73D0<-009F7420<-009F79D8<-008C70C8/008C1540 (11/40); 009F418C<-009BB16C<-005F3FE8<-005FA4D0<-005FA730<-568784 (consumer).
- Cause of the endless loop still open.

## Hyp. 45 (part)
- probe_bt44: 3754 soc-job chains, 4062 GT.VOL opens, 5213 IsLoaded(NPN); snapshot: main thread lr=568CB4 (in sync pump), objects 7FEAC000/7FF0B000/7FF0B800 +0x88=0. Once job 3 rc=-1. Cause open.

## Archive from STATE.md (Hyp. 109-116, moved 2026-11-23 by supervisor)
- Hyp. 109-111: static chain wipe: 7D083C (wrapper, singleton 0x159FD890) > 7CD628 > 88B878 > bl A25C64 (1 caller each, 7D083C without direct one). CALLTRACE_TO on 7D083C/7CD628/88B878/88B8E0: 0 hits (exit runs h110 4/4 with CALLTRACE=200, 88B8E0 is a bl site).
- Hyp. 112: GSTACK in exit run (run.log.err, h110): worker tid32 "9qstY" (A304D0>7FB1F0>7FB090>7DF57C>7DFF44>7DF7DC>802004>1AE7CC>1AE5E4>1AE074>1AAC8C>7D083C>7CD628>88B878>A25C64). Unfiltered calltrace: no exit (Heisenbug).
- 1AAC8C = cleanup task (obj+0x1F30: 7D0904,7D0DE8,7D0FC0,7D083C,7D08DC), only caller 1AE1E8 in 1AE074. Question: why does cleanup run on X-press, singleton vector 71E4455C has NULL element.
- Hyp. 113: A25C64 = fill [begin,end-8] with 0 (vector elem+0x2C: begin@+8, end@+0xC). Empty begin=end=0 -> end-8 wraps (unsigned) -> fill 0..FFFFFFF8 = wipe.
  Elem object unconstructed/zeroed (race). Loop log: normal runs 2 elements ok (7FFEE090/E0D8); 2nd exit type: first NULL write from CAC2D4 (1AE074+0x488), not A25C64 -> general race.
- Workaround: guard in func_00A25C64 (generated 023): end<8 -> return. Backups work/_bk_h113/. h114/h115 (10 runs): 0 exits, guard fires ~30% (elem pointer garbage/NULL).
- Hyp. 115: guard survivor frame 9000 (4x) = GT logo + spinner. fs accesses end early (no IO wait). 2/4: A2FAD0 ring-list walk with NULL node = busy loop (3.7M null writes).
- Finding: teardown tasks (1AE074: +0x178 1AAC8C, +0x508 7CFDD0>88B928) run on singleton/lists that are used and zeroed in parallel = use-after-free race. Cause open.
- Hyp. 116: TLS TID cache (A3046C) yields unique ids per r13 (1,2,5,9..34) -> TID duplicate refuted. 1AAC8C/1AAD14 run EVERY frame (no wait/teardown trigger) = normal.

## Spinner state watchdog + calltrace (2026-11-23, probe wd2/ct, orig+X@100, build-v020)
- WD at 200/320 s identical: ~20 workers in sys_lwcond_wait (lr A4309C), tid1/2/3/5 lr only. EVQSTAT: q4 pushed=205k, q5 64k (pending=3), q7 64k, q1 17k, q9 21k; no waiter jam.
- NEW: `[null-write] wrote32 0 to NULL+0x40 by guest-fn A2FAD0` 4.55 M x in 340 s (~13k/s), plus 2x NULL+0x18 by 88B450 at boot. A2FAD0 = "wake all" (vtable slot 7 fiber thread class): loop over list nodes, stw 0,0x40(node->+8). Element pointer NULL -> fiber list has NULL entries (related to Hyp. 83 NULL element).
- CALLTRACE_TO=A2FAD0: caller lr=567DA4 = func_00567D74+0x2A4, tid=32 (fiber run thread), r3=0x7FFBE280 r31=0x7FFD8E88. 567D74 has one direct caller (6D5230); rest via vtable.

### Fiber list busy loop (2026-11-23, probes nwt/wk/ww2, build-v020 + diag)
- null-write tick: ~78M NULL+0x40 writes/s from tid32 in A2FAD0, constant 180+ s (nwt) -> loop runs practically all the time, not 13k calls/s with a short loop.
- [WK] diag in loop: obj=7FFBE280 cnt=1, hdr(obj+0xC)=7FFFEDC0, hdr.next=0 -> r9=0, null page reads 0, cmpw never equal -> endless loop (PS3 would crash).
- With PPU_WWATCH (inline stores off, timing differs): sentinel EDC0 initialized cleanly (A2F638, tid1), node EDD0 via A2FC54, NO busy loop. Snapshot runs: sentinel EDB0 sane, tid32 in lwcond_wait.
- Conclusion: busy loop = alloc/race-dependent extra error (sentinel zeroed in some runs); spinner hangs in the clean regime too -> NOT the cause of the loading phase.

## STATE archive (2026-11-23, moved from STATE.md)
## Done / refuted (one-liners)
- Pad/dialog chain (Hyp. 1-14): all without effect, obsolete through workaround (15). RPCS3 `--no-gui` as oracle dead (shader precompile).
- Plan B pad replay: PAD_LOG=<path> (patches/gt6-v020-padlog.patch, build-v020 rebuilt, tested) + scripts/live-padlog.ps1: user plays live, log -> PAD_SCRIPT replay.
- SDK update ps3recomp v0.19 -> v0.20.0 (clone third_party/ps3recomp-v020, local patches merged, build gt6\build-v020): baseline noadj 220 s/frame 4200 identical (GT logo + spinner), progress same; flips ~3x fewer (pacing). Backend comparison Vulkan vs D3D12 open (PS3RECOMP_RSX_VULKAN + rsx_vulkan_backend_init).

- probe.ps1: -FreezeSec, -Seconds 0, END line, hdd0 copy/run (-Parallel ok). PadScript press tokens only (0x0 forbidden).
- Hyp. 78-80: REALFLAG (WaitFlagEx) = DEFAULT, dialog renders correctly. noadj+REALFLAG: exit ~52 s (race, Hyp. 81/82/86 pinned = deterministic).
- Hyp. 83: exit = A25C64 (vector.clear) from 88B8E0, NULL element in pointer vector 71E4455C -> zeroes 14E4000..FFFFFFF0. Hyp. 84-89: buffer/new/lock not the cause (Heisenbug).
- Hyp. 92: orig + PAD X (80-140 s) -> frame 9000 = GT logo + spinner. AdjustScreen passes.
- Hyp. 109-116 (details in eu-boot-log.md "Archive"): wipe = A25C64 fill end-8 wrap, caller worker cleanup 1AAC8C; guard (A25C64 end<8 return) stops exit, spinner stays -> wipe is NOT the cause of the loading phase.

## SUPERVISOR FINDINGS (2026-11-23, review Hyp. 1-116 against ps3recomp v0.20 + third_party/GT5P)
1. Chain Hyp. 83-117 (35 hyp.) hunts the exit race = symptom. Guard survivors show: even without exit, logo+spinner stays. STOP the race hunt.
2. UNTESTED, cheap, one batch each (-Parallel 4): `PS3_PRIO_START=1` (lv2 priority start, SYSCALLS.md; race class "thread runs before init"), `PPU_RESV_OFF=1` A/B (stwcx reservation), `SPU_LOCKSTEP_QUANTUM`.
3. Probe != live: user sees the menu live after a test race. Probe uses a FRESH userdb per run (GT6_HDD0 copy without db), boot.adc patches, <=320 s. Spinner may = first-start setup (DB/save build-up), really takes >10 min. Test: live run with user's persistent db + 15 min, frame captures 4200/9000/20000/40000.
4. GT5P sister port (same PDI engine, third_party/GT5P/docs/progress.md): roots were runtime writers into game heap (VM_HLE_INJECT_BASE, GT6 ok = 0x03000000) and HLE stub with wrong arg count (cellDiscGame wrote into OPD table). -> audit HLE stubs that write into guest pointers (PPU_WWATCH on victim address, writer attribution 'host' vs 'guest-fn').
5. Measure with `PS3_VERBOSE=0` (probe.ps1 sets it): logging serializes threads = Heisenbug cause (GT5P README).

RESULTS 2026-11-23 (probe.ps1 -KeepDb, RSX_CAP=start:count:stride via -Env, build-v020):
- Finding 3 REFUTED: persistent db (-KeepDb), orig+X@100 s, 900 s/100k flips: frame 4200 AdjustScreen, 7200..19200 stable GT logo + spinner. Fresh db is not the cause.
- Finding 2 NEGATIVE: PRIO_START=1 / SPU_LOCKSTEP(Q1000) / control: frame 4200 identical (AdjustScreen, 28.4% black). PPU_RESV_OFF=1 worse: only 6555 flips/430 s, NP2 IsLoaded loop.
- Finding 4 audit (static, open): suspicion M-H cellSysutilGetBgmPlaybackStatus (cellSysutil.c ~507, memset 0x28 vs SDK struct), M sys_process_get_paramsfo memset 256, cellSync barrier/rwm host layout. cellFs/SaveData not audited.
- Spinner state (wd2/ct): waiters all idle, no event jams. NEW: wake-all A2FAD0 ~13k/s from tid32 (func_00567D74+0x2A4), fiber list nodes with NULL element (NULL+0x40 writes, 4.5 M). Details eu-boot-log.md.

- Fiber list A/B (snap 200 s, REALFLAG 0 vs 1): object 7FFBE280 count=1, node payload not NULL, structure identical -> NULL+0x40 does NOT come from this list; REALFLAG without effect.
- Fiber busy loop: A2FAD0 runs 78M NULL writes/s, sentinel obj+0xC has next=0 (only in some runs, alloc/race); snapshot/WWATCH runs clean, spinner there too -> not the cause.

Audit #1/#2 (BgmPlaybackStatus/paramsfo against SDK), then RPCS3 comparison: which syscalls/files are missing in our run after AdjustScreen.

## PDIPFS oracle test (2026-11-23, probe pdi)
- fsv (PS3_VERBOSE=1, 140 s, normal hdd0): 118 PDIPFS opens ok, 0 failed, no access to PDIPFS/59.
- pdi: hdd0 = copy of RPCS3 USRDIR (14 GB, 17.5k files, work/gt6_hdd0_rp; originals untouched), -KeepDb, orig, 300 s, X@100 s: 18.8k flips, 3.1 M null writes, 9.7k NPN IsLoaded, no open PDIPFS/59, no Pamf/Dmux/Vdec hit in err log. Identical to standard spinner.
- Region: CORRECTION: RPCS3 uses the same EU disc BCES01893 (BCJS37016 = internal savedata name); GT6_1.N vs GT6.N = update states of the data. RPCS3 log = 1:1 oracle. Spinner state independent of PDIPFS content -> install/data hypothesis discarded.

## Guest PC sampler + RPCS3 comparison (2026-11-23, probe gprof)
- Sampler: gt6/src/gt6_gprof.cpp (GT6_GPROF=1, GT6_GPROF_SEC=n), samples ctx.cia + prof_pc (last syscall callsite) every 5 ms. cia is always entry (0x14E0898) for threads, only prof_pc is useful.
- Run work/probe_gprof_20261123_121842_1 (build-v020, orig, 220 s): steady state 37 threads each 2.7%: 29 pc=0xA4305C (sys_lwcond_wait wrapper), MpAnk F543AC, pnZ 27465C, prsIy A4F6E4, lgFF A61B80, SpuEvH A564EC. No spin.
- Conclusion: deadlock wait, not busy loop. Loader 9qstY (tid 32) stands in lwcond_wait; in the RPCS3 log from line 157234 the same thread continues (LoadModule 0x2a/0x2d, PDI thread 0x100003a/b, worker stat 59/FI).
- RPCS3 ZBm9Y IsLoaded(0x38) poll (1857x) also runs there until session end: no difference to ours.
- VERSION: RPCS3 USRDIR EMAIN.SELF 9209104 B / EBOOT.BIN 165712 B / data GT6_1.N (patched, update). Our base work/bin: EMAIN 8843160 B / EBOOT 72920 B / GT6.N. So the oracle is the update state, not the disc base.
- Open: determine lwcond address + signaler of tid 32; check whether base EMAIN knows the 59/FI request.

## STATE archive 2026-11-23 (1.22 estimate)
- ESTIMATE recomp patch EMAIN 1.22 (RPCS3 EMAIN.SELF 9209104 B; FIXEDELF114 = 1.14, 9059040 B), NOT started, user decides:
  1) SELF->ELF: gt6/scripts/decrypt_self.py needs pycryptodome (missing) + keys/RAP; ELF then in work/patchelf/. Effort ~1-2 h, risk keys.
  2) Lift + gen (relift-gt6/gen-functions-gt6, ~1 h compute) and rebuild ~2 min; re-port all address patches/guards (H113 A25C64, boot.adc gates): 0.5-1 day. Total ~1-2 days.



## STATE archive 2026-11-23 (1.22 port steps)
- 1.22 recomp step 1 DONE: work/bin122/EMAIN.elf (23787792 B) via tools/self_decrypt_np.py, key from RPCS3 log; 1.00 self-test identical. Next: diff 1.00/1.22, lift in generated122.
- 1.22 lift+build: gt6-122/generated (74914 funcs, code-end 0x10B8154), build-v122 links (GT6_V122 guard stubs.cpp), ctor 0x1183C/lr 0x11880, setjmp C61F88/longjmp C620AC patched. Probe v122b running.
- 1.22 build-v122: memset/switch entries + setjmp guards (scripts/post-lift-122.ps1) -> 0 unresolved, 0 setjmp overflow, ~9480 flips/150 s; frame 4200 black (hooks missing).

## STATE archive 2026-11-23 (from STATE.md Done)
- 1.22 SPU lift: 16 job images (fp scan tools/find_spu_jobs_122.py), PM id5 (byte-identical, 0x14DAA80), 1 embedded ELF -> gt6/src/gen122 + gt6-122/generated/spu_lifted. 0 dispatch MISS, ~11400 flips/180 s.
- Spinner question 1.22 (VERBOSE fs, orig+noadj 200-220 s): 30 PDIPFS opens, NO PDIPFS/59/FI, no Pamf. Update EMAIN alone does not solve the spinner.
- Oracle diff (oracle_seq.py, PS3_HLE_TRACE_ARM): sysmodule sequence + fresh savedata = NO divergence. PDIPFS/9 opens = oracle up to EE/3C, then oracle 59/FI, we 85/H2... divergence AFTER EE/3C.
- Hooks 1.22 ported (tools/port_hooks.py: stream r/s/t, 3 FileDevice guards, host open AB080C). Probe hk122 noadj 220 s: unresolved=0, frame 4200 black 100%, no PDIPFS/59. Script hooks/menu pump missing.
- rp122 (RPCS3 hdd0, noadj 220 s): no 59/FI. Open diff: oracle opens 9/PR/MF (worker MkZA-) after 8G/RB, we 8Y/Y0 (oracle never); 26 oracle opens before EE/3C missing, EE/3C never reached.
- Hyp. nullist/freeloop (2026-11-23): dispatcher list 0x7FFBE100 (snap_292013437) ok (1 node). Spin = FREE loop AD4334-AD4350 (copy list next=0, lr=AD4344, 41131 HOTREAD). Guard dispatch (tools/guard_notify.py) + free loop (tools/guard_free.py) removed spin, guest quit ~30 s stays (flips=107). Spin = symptom.
- Hyp. rv (probe_rv_20261123_183926_1, tools/log_ret.py): A7E044 (path join, A86A10=is-abs-path) ret 1, A7E6BC ret 1, A52140 ret r29&0xff=1; 13D94 discards r3. Run method returns NORMALLY (no error path), then 13FFC term -> 90DC1C shutdown wait.
- A52140 (caller 6B7A9C) = app run: A7E6BC hands task 0x7FFCEE90/job 0x7FFCEE70 to tid30 and waits (A30028). Job = 7B5208->6166A4: AD4294(obj+0x2b0) then vt slot 0x154 -> 6C6BC8 -> obj+0x9d8 vslot 0xC. With guard the job ends early -> main goes down.
- Hyp. job9d8 (2026-11-23): obj 7FEEC000+0x9d8 = 0 (snap 6 s); in class vt 15B5668 (ctor 6C7E04) single writer 6C7E7C = 0 -> vt slot 0x154 (6C6BC8) is a no-op. Job 0x7FFCEE70 = only AD4294 notify + no-op, ends normally.
- Listener in disp 7FFBE100 = thread object "processEventLoop" (0x701F80F0, vt 15DCF60, slot 0x14 = AF03B4: State@+4==3?). Wait A30028 polls A2F290 (task state 0/1/3 = done, 2 = yield). Task done = normal path.
- Hyp. submit (2026-11-23): job 0x7FFCEE70 (vt 15C3888) is created via reflection factory (ctor 7A05D8, class registration 7A0900 with OPD 0x1624380, methods initialize/finalize) -> script VM task, no direct submit caller.
- run.log (probe_hletr_20261123_184856_1): AutoLoad2 #1 funcStat -4, #2 ok; GT6.0-5 = 305/23057/9005/1183/36/36 B; "LOAD complete" -> IMMEDIATELY "[sceNp] Term()" (line 776/780) = start of terminate. NpTerm caller + evaluation of the AutoLoad2 result in the guest never analyzed so far.
- UNRESOLVED NIDs 0x0DFBADFA (after cellKbGetConfiguration, init) and 0x90460081 (shutdown) -> CELL_OK faked; assignment open.
- Hyp. npterm: Np init (718) -> term (780) = wrapper AF9780 (called from 11A94; sysmodule load, net init, sceNpInit, 10BC740 op, sceNpTerm, net fin). Harmless, no exit trigger. Exit sequence (mouse/kb end) follows ~30 flips later.

## Hyp. nodata (2026-11-23)
cellSaveData.c: env GT6_SAVE_NODATA=1 returns NODATA instead of compat OK. Orig save: GAME6 -4 (new=0), 2nd call 0 -> LOAD complete -> MapEa 0x72400000 -> sceNp Term. Fresh gamedata: GAME6/BKUP6 -4, no AutoSave2, same term sequence. work/cross_run.log (older build) continued after BKUP6 (LoadModule 0xF044, trophy) - divergence unexplained.

## Hyp. loop135 (2026-11-23)
- tid30 loop func_008A7C6C polls byte 0x016CC8D0 (vtable 0xD9A788); set to 1 by 8A92C8, cleared to 0 by func_008A6EDC called from func_0088F1BC (tid1, global finalize 0x1496C via 0x14884) before ppu_thread_join(30). Loop is not self-ending; main requests shutdown.
- PPU_WWATCH is hex, tag [ww]; probe 'ww' worked (earlier grep 'watch' was wrong).
- Open: why tid1 enters 0x14884 (main return) ~135 ticks after gtauto load.
- loop135b: tid1 after gtauto load ~5000 indirect calls = shared_ptr release (A1EAD0/A1EA64) + dtor 76B7B4; last call before teardown is a dtor. main.adc strings: IsExitGame, execShutdown, shutdown_module, abortDiskFull, MINIMUM_HDD_SPACE. No cellFsGetFreeSize call in run; cellGame free=40GiB-256KiB; no sys_tty output; no [quit] sysutil request from us.
- exitgame: IsExitGame native reg at 0x828514 (name str 0x11A1278), impl AD2998 (lock B03998, getter 449384 on obj 0x1796DB8). Only writes to 0x1796DC8: init 0 by F7B0D4. Other task state machine writes not seen (WWATCH MAX 80, 10 hits).

## Hyp. scriptflow (2026-11-23)
boot_adc.txt: processPatch only if MNetworkInterface.isUp && LoginUtil.isOnline (with us NP OFFLINE) -> patch/ExecGame quit excluded. display_sequence_gt6: presents -> LanguageSelectRoot -> AdjustScreenRoot -> applySaveData -> showVoucherMessages -> doBackupSave -> MovieRoot (skipOpening = !user_profile.option.opening_after_autoload) -> start_project_gt6 (GameParameterUtil.executeEvent, tutorial.xml). Probe opens: only boot/dialog gpb + mpackages, no game_parameter/tutorial.xml, no PDIPFS/59 -> script never reaches movie/start_project. Script log() produces no tty output (retail). CALLTRACE (first N, tid1) shows only dtor cascades.

## Hyp. userdb/VMtrace (2026-11-23)
- initUserDB never reached (no open userdb0101.dat in run.log/.err). Quit directly after LOAD complete GAME6 (GT6.0-5 read: 305/23057/9005/1183/36/36 B), then NP2 IsLoaded + sysutil UnregisterCallback, teardown.
- Path static: SaveDataUtil.load(AUTO) -> openProgressDialog (ProgressDialog.open: DialogFrame.appear, func(args)) -> _load -> sutil.load native (bindCheck) -> _autoLoadGameCallback.
- CALLTRACE_FROM=9EEA88/9F0748 (AFTER 3/22): 0 calls; addresses from 1.00 era. Probes vmA-vmE in work/.

- 2026-11-23 Arbeit6: quit only masked. WD@60 s tid1 in AC7418+0x54 (event wait AE27AC, obj+0x1ad8) via 13FD0 finalizer. GT6_SKIP_FDWAIT test (AC746C) -> teardown 98 flips. MAINSTAGE log: all 9 stages from 0x14010 run, AD2998=0. BFF0A0 returns immediately (malloc10 ok, C1F4C8=0). WD@12 s tid1 already in finalizer.

## Arbeit6 MAIN-LOOP 146E8 / AFDFC0 (moved from STATE.md)
- MAIN LOOP (Arbeit6): main stage 146E8 runs while(!AD2778()); AD2778 = all tasks in list 0x17F8F3C (nodes via AD2750) vtbl[2]!=0. Task class vtbl 0x15DD3E0 (ctor AFE0A4, new in 124F4), [2]=AFDFC0: loop {AFE38C snapshot of struct 0x179ED20: byte0&&byte1 -> return 1 (=done, main leaves loop)}. byte0=1 via AFE200 (from AFE2A0 when AF32FC==1), byte1 via AFE1C8 = (C6390C(x)==0) when [obj+0x34]==1, reset AFE328/AF47A4. Hypothesis: byte0/byte1 set to 1 here too early (wrong HLE return value C6390C/AF32FC?) -> main loop ends. MEASURED: AF32FC returns string ptr 0x179A1E8, AFE200 starts, TASKWAIT #0 st0=1 st1=1 immediately (2 calls). C6390C=strcmp: byte1=(strcmp(AF32FC(), obj+0x48)==0), byte2 analogous. MEASURED STRCMP: a=b='BCES01893' (title ID, AF32FC=cellGame BootCheck struct 0x179A1E8, [0]==1=DG). Task = boot check, legitimately fulfilled. Only node in list 0x17F8F3C (AD2750 has only 1 caller) -> loop ends on HW too?! OPEN: what keeps main alive on HW after 146E8 (stages 141E8/91E464/1414C afterwards; 10338->1096C: AD2998==0 -> 13FD0 finalizer). Check whether 1096C path differs when AD2998!=0 (IsExitGame); possibly call tree of 13FD0/14884 + who fills the loop in 146E8 (cb @0x16CD0C0-0x2F40 / -0x2f3c).

## Arbeit7 game-loop finding (from STATE.md)
- GAME LOOP 1.22 FOUND (Arbeit7, probe_a7loop_20261123_232443_1): counterpart to 1.00 568800 = 0x616C80 (loop 616E6C: 3 objects r28+0x1d4, tick 68FF84, done byte +0x96 instead of +0x91; thread entry 6170AC, loop {616C80 until [obj+4]==1}). Setjmp cluster 616D14..616FF0 = 1.00 5686CC..568978. RUNNING: tid1 calls 616C80 once (boot.mproject), then tid30 via 6170AC several times, 68FF84 ticks. Premise 'loop never starts' WRONG; state = 1.00 state (legal/logo, IMMEDIATE draws, 1 draw, C1 FAIL). main() returns legitimately, game runs in tid30. Next blocker like 1.00: loader jobs in tick handler 4 (job list, vtbl+0x120==3) never finish / SPURS soc-job completion -> no 59/FI open.

## Arbeit7 wait analysis (from STATE.md)
- Arbeit7 wait analysis (snap_a7): tid30 waits in loop 8A7AD0 (consumer) until counter [obj+0x1d8] > [obj+0x240]+1; counter ++ only in 8A88E8 (producer tid29), which BEFORE that does C45408(1) = cond timedwait (sys 0x6b, timeout 0x989680=10 s) on object 0x17E7FD8 (flag 0x17E7A2E!=1 selects 7fb8, C45408 always uses 7fd8). Only signalers 7fd8/7fb8: C47A24/C47A00 = atexit handler (OPD 0x163BF30). -> tid29 is timer sleep or exit gate; no missing signaler proven. HLE sys_cond timeout conversion checked (ok). AF870C=WaitOne(C45408(1)) in AF region. Chain ~9 hyp. -> change of strategy.

## Arbeit7 (moved from STATE.md)
- Arbeit7 snapshot work/snap_a7 (probe_a7snap_20261123_232734_1, SNAP_AT=70, frame 3500: black 100%, C1 FAIL measured): 68FF84 has 9 callers (incl. 16924/16FD0 = worker loop 'while([r29+0x11]) tick(*(singleton+0x1d4))', 17DAF0, 616E9C). Tick handler 1.22 table 0x15B242C: 68E35C,6907C0,6722FC,683A64,686C58(=job list),66E6AC. 616C80 object 7FEEE000: +0x48=0, +0x4c/4d=1, +0x1d4..0x1dc=0 -> 616E6C loop has NO objects (no tick from there). tid30 (ran 616C80) stands in snapshot in lwcond_wait lr B03BE8 (stack 920498,8A7B08,892988,AF0C2C = task pool worker), 15 threads lwcond_wait.
- Arbeit7 runs a7base/a7nowait (100 s each, frame 3500): producer tid29 calls 8A88DC ~6360x/100 s (=63 Hz, wait is woken normally, frame pacing OK). Wait skipped: no difference (32 IMMEDIATE draws, 139 fs opens, 5x 616C80, black). Pacing/counter 1d8 NOT the blocker. Details counter/atexit: eu-boot-log.md.

## Moved from STATE.md (Arbeit9, 2026-11-24)
- Arbeit8: AutoLoad2 IS reached (prompt assumption wrong): GAME6 -4, then ok/BKUP6 -4; gamedata/ in repo root (PS3_GAMEDATA_ROOT) has old saves GT6.N (1.00 format). Return CBRESULT instead of NODATA (GT6_SAVE_CBRES=1): no effect.
- Arbeit8 oracle (RPCS3 log line 155401): GAME6 AutoLoad2 3x (each new thread 'PDI', -4,-4, 3rd ok with GT6_1.N 16 MB), then LoadModule 0xF044 + sceNpTrophyInit; AutoSave2 BKUP6 +4 s. Ours: right after load immediately sceNp Term (no 0xF044/trophy), no retry. Snapshots work/snap_a8s50/a8s100: worker active 50 s, 100 s all lwcond_wait, tid1 in shutdown (lwmutex_destroy).
- Arbeit8 trophy chain: sceNpTrophyInit stub 10BDD20 <- B36E4C (fn B36E00 TrophyMgr init) <- B36F80 <- B379E0 (fn B37980, 0 direct callers) resp. B377BC (fn B376E4) <- B359F0 (fn B359CC, 0 callers). Both roots only indirect (vtable/task). Oracle main_thread: stages run, 146E8 loop ends there legitimately too (Arbeit6); main lives on there in 13FD0 finalizer wait, game in threads.
sceNpTerm caller = AF9870 (only one, fn ~AF9780: NP routine calls 10BC740 NID E6C8F3F9, then Term, unload sysmodule 0x16/0). Oracle: sceNpInit 76.08 s -> AutoLoad2 76.15 s, Term only at 106 s (exit). Ours: init -> load -> Term immediately. AF9870 sits behind strtol-like AF9448 + unload 0x16/0 = process teardown (main return, known quit mask), NOT an NP condition. Oracle: main_thread lives until 106 s. Question: what keeps main alive in the oracle (wait after stage BFF0A0/save load?) -> oracle log main_thread calls 76-106 s (lines 155344-162073, filter main_thread only) vs our tid1 end; no further NP/save deep dive.

## Arbeit9 (2026-11-24) trophy/F044 chain = script path
- Oracle: 9qstY (script thread, func AF0B94) does LoadModule 0x32, NpInit(B4AE34/70), 3x AutoLoad2 (PDI threads), then LoadModule 0xF044 (LR 10BB070) and trophy init (thread OEyq). No sceNpTerm in 9qstY.
- boot_sequence_common.ad lines 254-269 (boot.adc, tools/adch_disasm.py -X utf8): if network_available { Login.setEulaCurrentVersion; LoginUtil.sync; checkSaveDataBind(); if LoginUtil.isOnline() {Login.checkNpEula(true)} }. checkNpEula = MNpEula (class via 9D0458/9D06C4, ctor 9D0400->9CFBD0->AF8E34->AF3498 loads F044).
- Script method checkNpEula = native 0x1954C (ClassInfo heap 0x40020A2C). CALLTRACE_TO 9D0458, 9D0580, AF8E34, 1954C, 9AE5D4: 0 hits each (60 s, control: format ok, indirect calls recognized; 68FF84 only direct).
- isOnline (OPD 162D888?/9AFCE4) = byte [obj+0x6850] (A09D34); setter A0893C (stb 1) <- A0A110 <- 9AE5D4 (native method OPD 0x162D7A0 'initialize'? PDINetwork class, registration 9ADD90 string 0x11B5758). isDummy = const false (9B0098). Setter 0x6850=0 in A088DC (shutdown).
- Hypothesis: with us PDINetwork method 9AE5D4 (init/online) is never called -> isOnline=false -> checkNpEula skipped. Oracle: online (RPCS3 NP status).
- Arbeit9: CALLTRACE_TO 9B0098 isDummy / 9AFCE4 isOnline: 0 hits -> script never reaches boot_sequence_common line 102 (or direct call).

## Arbeit10 (2026-11-24) NP-term caller proven
- New knob NP_TERM_BT=1 (third_party/.../libs/network/sceNp.c, ydkj_host_bt). Run work/probe_a10_npbt_*: term chain (inside->outside) B4AD4C <- A088DC <- 9AD1DC (= native PDINetwork.finalize, OPD 0x162D710, string 0x11B5768) <- A746E8 <- A7479C <- A5C070 <- AA55FC <- AA41FC <- A2F0EC <- A2FFCC <- A7BA60 (run fn, calls A2FFCC at A7BC4C) <- A7E6BC <- A52140 <- 13C44 (main stage) <- 1096C <- 1024C. Synchronous in main thread (tid1), no foreign thread.
- So: script/project execution calls PDINetwork.finalize shortly after AutoLoad (gtauto.mpackage is loaded right before). boot.adc contains NO 'finalize' (full dump 11371 lines). Handler 1198C = vtable slot 0 (OPD 0x15E1E78) in exit list 0x17EFB6C, only called by 109E0 walker after main return -> NOT the term path here.
- Oracle: 3 PDI threads for AutoLoad (#50,#51,#53), we 2 (tid38 -4, tid40 ok); then oracle vyENO(3008)+OEyq(trophy). Oracle main_thread sleeps 76->106 s. Ours: thread sequence identical up to tid40, then end (Term).
- Open: which script/native caller in A5C070/A746E8 forces finalize (condition before it). CALLTRACE_TO 1198C = 0 hits.
- Arbeit10 draw path (probe_a10_draw_*, 90 s, frame 3500): only 30 RSX DRAW_ARRAYS prim=10 count=4 (fullscreen quad) ALL directly after loading dialog.mproject (~frame 3000 log lines 793-943), then 0 draws. Flips continue from game thread (SetPrepareFlip tid27 LR C44524 1837/30s, FlipImmediate tid29 LR C444D0) -> game flips empty frames. Explanation: application shutdown (finalize) before scene build-up. Capture: 1 draw, black.
- Arbeit10: no script in boot/gtauto/dialog/other .adc calls PDINetwork.finalize (grep pre-check over all adc with both words: 0 hits; gtauto 'finalize' = SceneFace). Term chain A7BA60 -> A2FFCC (loop A30020..A3007C calls A2F290 per step) -> A2F0EC is C++ application termination, not a script call. Oracle file names (PDIPFS hash) not comparable with ours (different hash), order comparison only by count: oracle 305 PDIPFS opens, we 35. 8A7AA0 = bounded queue push with cond wait (tid30 parked there for 100 s?) unproven, object address not derivable from stack.
- Next step: read A2F290 (step fn of the A2FFCC loop) + abort condition at A30038/A3004C; who sets 'done' -> finalize.
- Arbeit10 oracle main: main_thread logs NOTHING after 76 s (sys_rsx_context_iomap, line 155268) until 106 s (exit request: IsLoaded, Term, process_exit) -> oracle main BLOCKED (never returns). With us the term chain (project unload/PDINetwork.finalize) runs synchronously in tid1 without host quit (no REQUEST_EXITGAME in log). A2FFCC = wait/step loop (A2F290 returns 0/1/2/3; 2=retry, 3/0/1 = end) -> project run ends with us, not with oracle. Hypothesis: boot project ends/unloads (finalize of all root objects) because boot script runs through early; oracle stays in the script (net/NP/trophy path) and waits. No script calls finalize explicitly.

## Arbeit11 (2026-11-24) A2F290 status path
- A2F290 = step of a task/script interpreter (return = [obj+0x24] after A2F0AC state machine; jump table 0x1569DEC). A2FFCC loop: ret 2 -> yield (A1F8C4/A8604C) + repeat; 0/1/3 -> leave. [obj+0x28]==3 (A2F4E0) if field != global 0x1729948 -> ret 0.
- Run probe_a11_a2f290: only 5 objects (40007990,40007A10,4036B610,40393B90,40393C10), all +24=4 +28=1; ret 0/1 (21x), NEVER 2. So the oracle main waits (ret 2 resp. blocked there), we end.
- Run probe_a11_vcall2: vcall [obj+0x68] slot 0x14 (targets AA140C,B11990,A62F8C,106C974,..) ret always 0; not discriminating. probe_a11_assert: A217EC (assert/log) 0 hits -> no script error abort.
- Oracle main_thread: last action before block = sys_rsx_context_iomap (line 155268); worker 9qstY reads PDIPFS/9/*/* (line 155860ff.) further. Main presumably waits for worker load, with us the step returns immediately.
- Next (change of strategy): snapshot walk obj 40393C10/40007990 (+0x24/+0x28/+0x34/+0x6c vector) ours vs expectation; or workaround: force A2F290 return 1/0 -> 2 (guard) and check whether loads/draws continue.
- Arbeit11 Hyp4 probe_a11_force2 (A2F290 ret at call site A30028 -> 2 forced, env A11_FORCE2; patch state work/_bk_a11/ppu_recomp_022_force2.cpp): NO sceNp Term, tid1 yields in loop like oracle main, flips run (7677/120 s), but still black (capture 3500 non-black 0%), no 59/FI. => teardown is a consequence, not the cause; blocker lies in worker/load path (oracle 3 AutoLoad threads, we 2).
- Arbeit11 Hyp5-6 (knob A11_FORCE2=N at call site A30028, state work/_bk_a11/ppu_recomp_022_force2n.cpp; from call N ret->2): force from 1 = load stops after 34 opens (only K/*). n=3..17: 82 opens, n=20: 98, n=21: 139 opens + sceNp Term. Without force: 139 opens + Term.
  => calls 1-19 load up to 82 opens, call 20 brings +41 opens (GT6.N/tmp_*_work), call 21 ITSELF (not its return value) executes Term (chain A2F290+0x470 -> A2F0AC -> AA41FC -> A5C070 (virtual, 0 direct callers, r4-r6 = method/args?) -> A746E8 -> 9AD1DC finalize).
  Force-2 from 1 is unusable as baseline (blocks before the loads); oracle blocks after the loads (>= call 20).
- Arbeit11 Hyp7 (probe_a11_step/_nat, patch work/_bk_a11/ppu_recomp_022_nat.cpp): steps 1-20 = ONE object 40393C10 (vptr 015D39B0, ctx +68=40373FAC); step 21 = NEW object 40393C90 (same vptr, ctx 403731E4) -> new script thread/task. It runs script natives (A746E8 = native call trampoline, target = [[this+0x14]]) and in sequence calls 9AD090 (->A0AEE0), 9AD0B8 (->A08850), 9AD1DC (finalize) = PDINetwork singleton wrapper (OPD 0x162D6D0/D6D8/D710), then ends. Name table 0x11B5640..: setNetworkSystem, initialize, finalize, initializeNp...; OPD->name assignment open (no static pointer to OPD).
  Reading: task #2 (40393C90) runs with us through to the network shutdown block; oracle blocks before that in a native of the task. Candidates before: A3691C, A363C4, A56EFC, 8130AC, 809D40, A4887C (names open).
- Arbeit11 Hyp8-9: native return values steps 15-21 (probe_a11_ret): ctr after call not target -> unusable, no deviation derivable. probe_a11_skipfin (finalize 9AD1DC skipped, env A11_SKIPFIN): term comes anyway (opens 139, no 59/FI). NP_TERM_BT: chain B4AD4C<-B4B114<-A081B4<-9AD598 (PDINetwork native)<-A1EA64<-102BE4C<-A7BF50<-A1EAD0<-14900<-13FD0 = main() return finalizer. => project loop ends normally (step 21 = end), shutdown path irrespective of caller; term is consequence of loop end. Fix location = why project/task ends instead of waiting (script condition, not finalize).
- Arbeit11 DATA DIFF (scripts/opendiff.py <run-dir> [oracle.log]; 1st call): default hdd0: our K/-index opens read no PDIPFS/9/* data (hdd0 has no 9/ tree) -> with `-Hdd0Src work\gt6_hdd0_rp` (RPCS3 data, junctions) we follow the oracle nearly 1:1 (K/4D, 9/H4/MS, K/R2, ..., 5E/MG, 9/MQ/EK..9/7N/XG).
  Deviation 1: system language. Ours "system language 4 (host)" = DE -> 9/8Y/Y0 instead of oracle 9/PR/MF (English UK). With `PS3_LANG=en-gb` (=18) identical. (Default run takes the language from the host -> maybe PS3_LANG=en-gb as standard in probe.ps1.)
  Deviation 2 (benign): 9/56/PW (boot.mproject) missing: "pfs override" serves plaintext from host.
  Deviation 3 (FIRST real one): after 9/7N/XG the oracle opens (PDI thread, ~76 s) /dev_hdd1/pditsm/pagefile.sys (unlink+create, VMPageFile, fn B07748, caller via 0107Dxxx natives B07EC8/B08A14/B08EA8), then tmp_save_work.dat (path /dev_hdd1/, ours /dev_hdd1/cache/BCES01893/), grim2/grim007.db 2x, 9/S0/BE, GT6_1.0-5 (ours GT6.0-5), then 9/UP/KS,DS/XC,WA/2N... With us: B07748 NEVER reached (probe probe_a11_vmpf), no pagefile/grim007; after GT6.5 only 9/TA/SR,RV/VG,MS/1Y,9J/VK,6M/BG then Term.

## Moved from STATE.md (Arbeit11 trim)
- (Arbeit11) A2F290 returns 0/1 with us (never 2); vcall/assert probes without finding. Next: guard A2F290 ret->2 (workaround) or snapshot walk obj 40393C10. Details eu-boot-log.md Arbeit11.
- (Arbeit11) Guard A2F290 ret->2: Term gone, tid1 blocks like oracle, but still black/no 59/FI. Teardown only a consequence. Next: find the third AutoLoad thread (oracle #53): who creates it, why not with us.
- (Arbeit11) Term comes from step call #21 of the A2FFCC loop (not from return value); force ret 2 from #20 holds tid1, but only 98 opens, no 59/FI. Next: log A5C070 entry (r4-r6 + string) at call 21: which method calls finalize.
- (Arbeit11) step 21 = new task object 40393C90, calls natives 9AD090,9AD0B8,finalize(9AD1DC) in sequence. Next: name the natives before it (A3691C,A363C4,A56EFC,8130AC,809D40,A4887C) by registration code, which must block (oracle).
- (Arbeit11) finalize skip changes nothing: term comes via main-return finalizer (13FD0). Symptom chain 9 hyp. -> STOP. Next change of strategy: identify script of task 40393C90 via adch_disasm (task name from obj+0x68 / script loader log) and compare its wait/condition natives against the oracle.
(Arbeit9) Trophy/F044 = script path: boot_sequence_common.ad lines 254-269 calls Login.checkNpEula only if LoginUtil.isOnline() (= byte [PDINetwork+0x6850], setter A0893C <- A0A110 <- native 9AE5D4). CALLTRACE_TO 9AE5D4/1954C/9D0458/AF8E34: 0 hits. Details eu-boot-log.md "Arbeit9".
Next: (1) who calls 9AE5D4 in the script (method name via OPD 0x162D7A0, string 0x11B5758) and where in the .adc (grep adch_disasm dump); (2) why never with us: condition before it (MNetworkInterface.isUp? NP status). If isUp/NP status: check HLE sceNpManagerGetStatus/sceNetCtl against ONLINE-equivalent (oracle log), 1 run.
- Arbeit11 SAVE DIVERGENCE: oracle 76.15-76.57 s: 3x AutoLoad2 GAME6 (each funcStat -4 -> 0x8002b401), in between unlink/create /dev_hdd1/tmp_{save,db,garage}_work.dat, then sysmodule 0xF044 (LR 10BB070) + sceNpTrophyInit/CreateContext (thread OEyq). VMPageFile = consequence of page faults (MpAnk), not a trigger.
  Ours (empty savedata via PS3_GAMEDATA_ROOT=work/_gd_empty, en-gb, rp-hdd0): AutoLoad2 GAME6 -4, then BKUP6 -4, then Term; never F044/TrophyInit. Old save gamedata/ (22.11.) gave 2nd load result 0 (files GT6.0-5).
  Negative: GT6_SAVE_CBRES=1 (return 0x8002b401 instead of NODATA) -> unchanged BKUP6; PS3_SYSCACHE_PLAIN=1 (new knob cellSysutil.c: getCachePath=/dev_hdd1 like oracle) -> unchanged. Sysmodule sequence oracle: ...0x32, 0xF044, 0x5,0x24,...; ours ends after 0x32.
  Open: who selects GAME6 vs BKUP6 (request object worker AF0B94, fields +0x90/+0x94/+0x9c, creator AF0A44 generic thread creator). Dir name assembled by format (no string in ELF).
- Arbeit11 further negatives (all with en-gb, rp-hdd0, empty savedata): PS3_MEM_AVAIL_REAL=1 (new knob ppu_loader.cpp case 352: total 0xD500000, avail=total-sys_memory_allocate-mmapper; oracle values 0xd2d0000->0x8cd0000) -> unchanged (GAME6,BKUP6,Term). Knobs PS3_SYSCACHE_PLAIN/PS3_MEM_AVAIL_REAL live in third_party (gitignored) -> re-set from this line on rebuild.
  Oracle mounts SysCache as /dev_hdd1 (VFS remap to caches/BCES01893_*), AF50B8/AF5194/AF51B8/AF51D4 (save wrappers) are NEVER called with us -> AutoLoad2 comes via another path (thread request object, dirName inline +0x70, result +0xB0, worker AF0B94/AF5704).

## Arbeit12 (2026-11-24) AutoLoad2 request static + 3 probes (probe_a12_cb/def/cbres)
- AutoLoad2 stub 0x10C0BF0 has ONE caller: AF5704 (request execute method, flag r4 -> AutoSave2 10C0790/AutoLoad2 10C0BF0, result -> obj+0xB0, dirName inline obj+0x70). AF5674/AF5738 = siblings (list/fixed). Request objects 0xB8 large (7fd78000, 7fd780b8), vtable call, no direct xref.
- funcStat OPD 1637970 -> AF5260 -> AF51F0 (parks cbResult/get/set in mgr, state 0x6c=5). Game side 89BA3C (stat handler): get->isNewData!=0 -> 89B9E0(result=-4) -> AF5060 wakes. Oracle identical (-4), no difference in callback.
- 80F710 (result -> script code mapping 0x8002BE05->3, BE04->2, 0->0, 1->1, else 4) + 80FCAC/AF4EF8 (list path) is NEVER called with us: BKUP6/GAME6 come via another request path (AF5xxx class ctor AF5334..AF5C50).
- GT6_SAVE_CBRES=1 and default: identical GAME6,BKUP6,Term. Conclusion: return/callback not causal; choice GAME6 vs retry lies in the caller of the request class (script/native), oracle 3x GAME6 in between only pagefile.sys recreate.
- Generated 017/023 restored (backups work/_bk_a12/*_clean.cpp, probe patch work/_bk_a12/patch*.py).
- Arbeit12 probe a12_ctor: request object (0xB8) is freshly built per save op: ctor AF5528 (vptr 015DD1D8) from 89D07C (mgr init 89Cxxx/89D0xx, alloc c51c38), dirName setter AF5334 (lr AF5650, r4=0x16379A0, r5=0x40), execute AF5674 via AF0C2C (worker AF0B94 calls functor obj+0x20). GAME6 and BKUP6 = 2 separate mgr objects (7fd78000, 7fd780b8) => 2 init calls 89D07C, so the caller of the 89Cxxx init decides (script native/save controller), not return/callback.
- Dead end: 0x8256xx (AF5A14/AF596C, status strings none/update/maintenance/cancel/error, vptr 015DD1F0) is an NP/update status native, NOT save retry.
- Open: caller of the 89D07C function (xref --call on function start ~89CFxx) + caller chain; where dirName (GAME/BKUP format 0x11a...) is chosen; oracle calls the same 3x -> probably loop with retry counter in the save controller.

## STATE handover Arbeit14 (2026-11-24)
- VERSION DIVERGENCE RESOLVED (Arbeit7): work/bin/EMAIN.SELF = 9209104 B = RPCS3 EMAIN (1.22, ELF 23787792 B); old 8843160 B line was 1.00. Remaining diff: save prefix: RPCS3 opens USRDIR/GT6_1.N (16 MB, create), we GT6.N (small old files in work/gt6_hdd0, 22.11.). Format '%s.%d' at F87934; prefix source open. Prefix 'GT6' comes from data lookup (0x85360: key search 0x10e6310/18/20 in config tree, no fixed format string); cellSaveData HLE never called with us (0 log), RPCS3 calls AutoLoad2 (SECUREFILE GT6_1.0, page fault in fn).
- (Arbeit11) DATA DIFF: with -Hdd0Src work\gt6_hdd0_rp + PS3_LANG=en-gb we follow oracle opens up to 9/7N/XG. First real deviation: oracle then opens /dev_hdd1/pditsm/pagefile.sys (VMPageFile B07748, never with us) + grim2/grim007.db + GT6_1.N. Next: callers of the 0107Dxxx natives -> who creates VMPageFile/grim DB (script path), condition. scripts/opendiff.py.
- (Arbeit11) VMPageFile = page-fault consequence (MpAnk handles fault in AutoLoad2 buffer), not a trigger. Oracle: 3x AutoLoad2 GAME6 all -4 (NODATA), then sysmodule 0xF044. Our gamedata/ (22.11.) had old GAME6 -> 2nd load result 0. With PS3_GAMEDATA_ROOT=work/_gd_empty: -4, Term nevertheless after 9/6M/BG.
- (Arbeit12) AutoLoad2 only via request execute AF5704 (obj+0x70 dir, +0xB0 result); funcStat/-4/return identical to oracle, CBRES irrelevant. Retry-vs-BKUP6 lies in the request creator (AF5334-AF5C50 ctors, vtable). Next: vtable ptr of the request class (xref --field 0 / snap) -> creator.
- (Arbeit12) GAME6/BKUP6 = 2 fresh mgr objects (ctor AF5528 from 89D07C, dir setter AF5334). Decider = caller of the mgr init function around 89CF10-89D07C. 0x8256xx = NP update status, not relevant.

## Arbeit12/13 STATE lines
- (Arbeit13) GAME6/BKUP6 = 2 calls of the script native 0x89D59C (lr 8147A0, caller 814700-8147E8 name arg from table stride 0x60) -> 89D4C8 -> AF55E0, return = bool (89BBC0: 1 if ctrl.a8[4]==0 else 0). With us a8[4]=1 -> return 0 -> script tries BKUP6. Next: setter of a8[4] (89B9E0 stw 1,4(r4), reader/clearer), oracle value 0?
- (Arbeit13) Workaround 89BBC0 return=1: AutoLoad2 GAME6 2x (no BKUP6, like oracle retry), then sceNp Term (oracle: 3rd GAME6 + sysmodule F044). Cause a8[4]=1 open; term condition after retry open.

## Arbeit14 handover
- (Arbeit14) Batch GT6_SAVE_ISNEW0 (new knob cellSaveData.c): g6 -> 2x GAME6 cb=-3 then Term; all -> 1x; base -> GAME6+BKUP6 then Term. Term independent of isNewData. Oracle: 3x GAME6 (3 PDI threads) then AutoSave2 BKUP6, no Term.
- (Arbeit14) Save chain (Arb.11-14) >10 hyp. ended. Next: Term trigger outside save (caller of sceNpTerm thread / script retry counter) or workaround Term (guard) -> next blocker.
- (Arbeit14) network_available (boot_sequence_common.ad) = (type in gt6/academy/demo), only false if PDINetwork.isDummy -> with us true. Not the cause. LoginUtil.checkSaveDataBind does NOT load (only online_id comparison).
- (Arbeit14) Batch PS3_NET_ONLINE=1+PSNR_SERVER (NpStatus ONLINE): no F044/trophy, Term as before. Oracle calls NetCtlGetInfo/NetStartDialog + sockets after GAME6; we never. Loads come from scripts/gt6/SaveDataUtil.ad (_autoLoad/load, main.adc 0x69055; GAME6 data 6DED0 in boot.adc line 254).

## Arbeit15 (2026-11-24) NetCtl dialog / main loop
- HLE trace (PS3_HLE_TRACE=30000, NID->name via oracle import list, script in scratchpad): after AutoLoad2 (GT6.5) the oracle in thread 9qstY calls NetCtlNetStartDialogLoadAsync/UnloadAsync, cellMusicInitialize2, sceNpTrophy*, EntitlementById, AudioOutConfigure, sockets, AutoSave2 BKUP6. Us: only SpursJobGuardNotify, pad/kb, then sceNpManagerUnregisterCallback + sceNp2Term (shutdown).
- NetStartDialog callers: 798C1C (state machine obj 0x16EC2E0, state 1 -> LoadAsync, 3 -> Unload; called from 6C7664 per tick, only ~10-99 calls in boot phase, state always 0 -> forcing to 1 never triggered), B494C4 (0 CALLTRACE hits), AF9350 (per iteration of main loop 146E8, caller 0x1474C).
- Main loop 146E8 FORCED (AD2778 -> 0, env A15_LOOP): main stays in loop, AF9350 calls NetStartDialog load/unload (ran), BUT only 4 fs opens, no sceNp2Init/AutoLoad -> loop 146E8 lies BEFORE the AutoLoad stage; permanent loop prevents following stages. C1 FAIL (0% non-black). => loop end with us legitimate, quit trigger NOT here. Patches: work/_bk_a15/*.a15.cpp (generated restored).
- Oracle NetStartDialog (77 s, thread 9qstY) = after AutoLoad in worker thread, not from 146E8; caller thread/function there still open (candidates AF93B8/B49524/798C70; 798C1C state setter unknown: BSS, no imm/field hit).
- Arbeit15 thread comparison: oracle thread 9qstY (func AF0B94 = task pool worker, prio 2176, stack 0x10000, created by main_thread at 75.7 s) == our tid30 "9qstY" (same names/prio/stack in both, names deterministic). Oracle runs NetStartDialog/Music/Trophy/Sockets in it = job that main submits and waits for (main silence 76-106 s). With us: tid30 parks as worker in lwcond_wait (no job) and main runs through. Next: job submit in main (after sys_rsx_context_iomap) in the oracle run = which task submit/wait call in tid1 after AutoLoad; with us find submit function via CALLTRACE (AF0C2C/920498 worker side, search submit side) and check whether submit happens but wait is missing.


## STATE trim 2026-11-24
- Quit ONLY MASKED (Arbeit6): p3 guard parks tid1 in shutdown (AC7418 event wait AC746C, WD@60 s). Skip of the wait -> teardown at ~98 flips. Game threads continue running.

## Arbeit16 (2026-11-24) tid30 snapshot walk (work/snap_a8s50, offline, no new run)
- tid30 "9qstY" parked in lwcond wait (lr 00B03BE8 = shared idle wait of pool workers). Stack return 008A7B08 = inside consumer wait 8A7AD0 (ld 0x240 producer count, ld 0x1d8 done count, loop 8A7AF4..8A7B0C: wait while obj[0x240]+1 > obj[0x1d8]).
- Consumer object = stack ptr 7FFCACA8: +0x1d8 = 0x1F (31), +0x240 = 0x25 (37) -> waits for 6 more increments of 0x1d8.
- Only writer of 0x1d8 in the 8A region: 008A88E8 `std r9, 0x1d8(r30)` (producer candidate, = tid29 side per NEXT_SESSION_PROMPT). xref.py --field needs hex without range; --in format is decimal/0x-int only.
- 01644F38 (earlier candidate) is NOT the consumer object (+0x240 = ptr).
- Not yet: who calls 8A88E8 (function entry), and whether the Oracle run increments 0x1d8 at all in the same job.
- Producer function = 008A8890 (stdu r1,-0xa0; only caller 008A89C4 `b 0x8a8890`, loop inside same fn). Gate: lbz obj+0x1d0 (==0 -> skip to 8A89A0). Body: ld obj+0x1d8 +1 -> std (8A88E8), then calls 0xC45408 / 0xB03998 / 0x8A85A0 / 0xB038EC.
- Handshake object (r3 of 8A7AD0/8A8890): consumer sets +0x1d1 (stb, 8A7B00) before lwcond wait, producer gates on +0x1d0. Flags are set in the same object.
- Open: who writes +0x1d0 and +0x240 on the job object (writers via xref --field in decimal ranges only: xref --field 0x240 --rw w without --in). Next: find the job object creator (main/tid1 side) that sets 0x240 and submits.


## STATE trim 2026-11-24
- main()=0x14010: all stages run, IsExitGame(AD2998)=0 always. BFF0A0 (stage 1414C) is only the init launcher (malloc ok, C1F4C8=alloc 0x6000, BFF578=setup stub), returns r3=0 IMMEDIATELY (~line 460 in the log, before MenuClassDefine loads). tid1 is already in the shutdown wait at WD@12s (13FD0 finalizer) -> main() returns <12 s, game keeps running in tid3/workers.

## Arbeit17 (2026-11-24) consumer-wait workaround
- Guard tools/guard_conswait.py on 8A7AD0 loc_008A7AF4 (skip lwcond wait -> loc_008A7B4C). Build ok (exit 0).
- Probe work/probe_arb17_conswait_20261124_114217_1 (notut, 320 s): guard hit 3x (log cap). No PDIPFS/59/FI, Pamf, Vdec, non-black. SetPrepareFlip 1987 (baseline a15loop 6384 -> different length/state).
- SPU mfc-list STALL img=5 elem 0x01550 x16 in both runs = not new; not the blocker.
- Conclusion: the 8A7AD0 wait is not the loading blocker. Workaround insufficient alone.
- (Arbeit17) PS3_SNAP_AT=140/175 (guard probe, 200-220 s, 3 runs): NO [SNAP] line, no snap_* dir. Snapshot thread armed in lv2_syscall (ppu_loader.cpp:3581) never starts here. Snapshot diff blocked until fixed (check arming path / env pass-through).
- (Arbeit18) PS3_SNAP_AT non-trigger CAUSE: the 3 snap runs were parallel probe.ps1 (taskkill killed each other at 42-73 s < 140 s). Arming code OK. Re-run single: arb18_snap140.
- (Arbeit18) snap diff guard vs base @140s (work/snap_a18_{base,guard}): ONLY tid30 differs: base lwcond_wait(8A7AD0), guard running cia 16377C0 lr AD323C (stopwatch/time-get 0xAEFD7C->sys time stub); other 39 threads identical (parked: 130/141/107 syscalls, lwcond 1,2,5,17-19). Guard just moves tid30 into a timed poll; producer 8A88E8 still absent.
- (Arbeit18) Sibling check 3: guard run PS3_SCTRACE=1 120 s (327 MB log): all lv2 syscalls ret 0 except sc130 ETIMEDOUT x1706; NO memory alloc failure. 8A8890 producer gated by obj+0x1d0 byte (cleared by 8A6EDC finalize in tid1 = known quit chain, boot-log l.220).
- (Arbeit18) Snap@100-140 s (guard, base, A15_LOOP=1): tid1 ALWAYS in finalizer chain 13FD0->148A0->AAE108->AB0430->AC7B14->AC746C->AE2870 (event/lwcond join). So tid30 wait 8A7AD0 + guard = shutdown symptom; guard approach dead. Core Q unchanged: why main 14010 returns (A15_LOOP=1 does not hold it in this build).


## STATE trim 2026-11-24
- C1 FAIL: capture frame 3500 black (1 draw, 0 nonblack). b5b260 cache fill (p4) ported, no effect, no 59/FI open.
- (Arbeit18) Main stages 14010: loop 146E8 exit = task struct 0x179ED20 byte0&byte1 both 1 in snapshots (done, legit); stages after loop (965460, 91E464, BFF0A0 gfx/config init w/ early-outs +0xc8, BFDFF4) are init only. No static lead left for 'why main returns'; GT5P heap-overrun hint (glyph count 31x20, HEAPPAD) has no GT6 knob.

## Arbeit19 (2026-11-24) correction of the Arbeit16 consumer-wait finding
- Arbeit16 dumped 7FFCACA8 (timer data1 of tid30; snapshot shows an arithmetic-fill pattern, NOT an object): "0x1d8=31 < 0x240+1=38" was an artifact. Real consumer object is r27 of 8A7AD0 = 7FFCAAB0 (from tid30 callee-saved regs in B03BAC frame).
- Real obj 7FFCAAB0: +0x1d8 = 0xC2E (snap 50 s) -> 0x185E (snap 100 s) = ~62/s, +0x240 = same value. tid30 consumer and tid29 producer (8A8890, waits tick cond 17E7FD8 via C45408, tick signaler C458E8 from OPD 163BF28/30) run in 60 Hz LOCKSTEP. NOT stalled. conswait guard (Arbeit17) was pointless.
- Timers: id=2 (gFKsE loop 8A921C) starts+fires every ~15 ms (PS3_TIMER_LOG=1, new env-gated log in sys_timer.c). Timer id=3 (tid30, d1=7FFCACA8 d2=0x880) never started: its starter 8A70A8 is only called from loop 8A921C after 8A89C8 -> tid30 sits inside the per-frame consumer wait in that loop, i.e. game loop runs normally.
- Consequence: 9qstY/tid30 = the game main loop, alive at 60 Hz. Oracle runs AutoLoad->NetStart/Music/Trophy from its per-frame vcall; ours never leaves the early state (798C1C state machine obj 0x16EC2E0 state 0). Next: why per-frame callback chain (6C7664 -> 798C1C) is called only 10-99 times (Arbeit15) while loop runs thousands of frames.
- (Arbeit19) NEW env knobs (runtime, off by default): PS3_TIMER_LOG=1 (sys_timer start/fire), PS3_THREAD_BT=1 (guest backchain at each sys_ppu_thread_create; log line also has creator=<tid> clr=). Probe arb19_bt2.
- (Arbeit19) KEY: ours, tid1 (main) runs the GAME LOOP INLINE and creates the load threads: PDI#1/#2 creator=tid1, bt tid1: main 10250/104BC/109C4 -> 13D94 -> A521CC -> A7E6CC -> A7E5F4 -> A7BC50 -> A30028 -> A2F700..A74734 (task engine) -> 7A0BB8 -> 7A0AC0 -> 6171FC (in thread entry 6170AC) -> game loop 616C80/616EA0 -> tick 68FF84 -> 690058 -> 66E6BC -> A86168 -> A2F700 -> create. Oracle: PDI#1-3 creator = 9qstY (pool worker AF0B94), main_thread silent while waiting. => in ours the task (6170AC game loop) runs inline on main instead of on pool worker 9qstY. Decider = A7BC50/A7E5F4/A7E6CC (submit vs run-inline).

## Arbeit14-17 STATE lines (moved by Arbeit19 trim)
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
- (Arbeit20) Saves renamed to GT6_1.N in PS3_GAMEDATA_ROOT (work/_gd_g61): 2nd AutoLoad2 funcStat -3 (broken) instead of 0 -> game's own name check expects GT6.N in our run; prefix source still unknown. 89C8C0 "%s.%d" = chunk/progress loader (divwu*100 -> +0x98), NOT save names.
- (Arbeit20) F044 chain retraced: AF8E34 (task ctor, arg 0xF044) <- 9CFBD0 <- 9D0400 <- 9D0580 = MNpEula; script path guarded by isOnline (Arbeit9/14 closed). Oracle ZBm9Y polls IsLoaded(0x38) every 16 ms after load; ours calls it once. Not followed up.
- (Arbeit20) Lead: oracle calls IsLoaded(0x38) 1857x (per frame, from B40A28 family = NP2 manager; callers B3571C,B40B4C,B40C4C,B4175 0); ours once. Check which caller in ours runs (CALLTRACE_TO B40A28) and whether B40A28 is terminate vs update; static first.
- (Arbeit20) CORRECTION to lead: B40A28 = NP2 manager terminate (called via wrapper B35700 and B41750 after failed init, -0x1e); NOT the per-frame poller. Oracle's 1857 IsLoaded(0x38) calls come from another caller (computed r3, not li 0x38): find via LR in a CALLTRACE/HLE trace, not static li-scan.
