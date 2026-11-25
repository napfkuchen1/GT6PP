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
- (Arbeit20) UNSETTLED: only static `li r3,0x38; bl IsLoaded` site is B40A7C (inside B40A28), so oracle's 1857 polls may come from B40A28 after all (terminate/update role unclear). CALLTRACE_TO cannot see direct bl (arb20_np2: 0 hits, inconclusive). Next: GT6_GPROF call counts for B40A28 in ours, or hook-count via PS3_HLE_TRACE LR of IsLoaded(0x38) (guest caller lr).
- (Arbeit20) arb20_gp: GPROF is sampling only, no B40A28 in top sites (all threads idle at 100 s); no call counts -> use a guest-side counter hook on B40A28 entry instead.
- (Arbeit20) LEAD: oracle does sceNp2Init+sceNpInit+ManagerRegisterCallback (main, 76.08 s) right BEFORE the 3 AutoLoad2 (76.15 s); ours never calls Np2Init (only sceNp Init/Term). Ours calls IsLoaded(0x45) -> HLE returns ERROR_UNKNOWN (slot<0), then IsLoaded(0x38); oracle never logs 0x45. Guest sites li r3,0x45: B4D684/B4D6C4 (func B4D668: bne after IsLoaded -> skips B4D4A8 path), B4DFDC/B4DFEC. B40B4C/B40C4C call B40A28 when NP2 call returns 0x80022307/05. Next: check RPCS3 IsLoaded(0x45) semantics + make our IsLoaded(0x45) return OK (sysmodule table), then probe: does Np2Init appear.
- (Arbeit21) Np2Init verified present in ours (HLE sceNp2Init calls sceNpInit; log '[sceNp2] Init' added in libs/network/sceNpMatching2.c). Oracle Np2Init in thread 9qstY at 76.08 s after UserInfoGetList, then AutoLoad2 in thread PDI; ours same sequence incl. GetList/Init/RegisterCallback/AutoLoad2. Ours AutoLoad2#1 returns NODATA (oracle CBRESULT 0x8002b401 both calls, funcStat -4 twice); ours #2 loads GT6.0-5 (result 0). Guest B4D668 = NP_TUS dtor path (0x45), not init.

## Moved from STATE.md 2026-11-24 (Arbeit22 trim)
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
- (Arbeit21) A4F938 = locked list/flag check + timer (AEFD7C), no worker dispatch; dead end. Look at A8548C/A2EA5C enqueue side instead.
- (Arbeit22) KEY: sync-pump port hack (stubs.cpp:1792, hook 617218) ran processEventLoop 616C80 inline on main = why only tid1 ran the loop and main shut down. GT6_PUMP_ITERS=0: main blocks in AE2844 wait like oracle, no Term in 300 s, opens go past K/CF into 9/*; flips run. Probes a22nopump/a22np_rp.
- (Arbeit22) Next: with pump off, check who should consume mgr+0x48 (worker, hook AD16AC 'never fires'); look for 59/FI/Pamf in a long run; if stuck, find why worker does not get the project request. Make PUMP_ITERS=0 default once confirmed. Tools: tools/trace_evt.py (diagnostic).
- (Arbeit22) Pump off (GT6_PUMP_ITERS=0, rp hdd0, WD@100s): main tid1 blocked AE27AC<-AE2844<-6171D0(hook)<-7A0A54; workers tid26/34 idle in queue loop AD1670 (AD8B30 empty-check, AD8C08 cond wait, AD8A68 pop, callback bctrl AD1764); tid30 pacer->6166A4 in lwmutex_lock 7FF2B7F0. Only 35 file opens, loading stalls ~5E/MG,9/MI/C2.
- (Arbeit22) Next: find who pushes the work item (MGOM.start request) to the AD1670 worker queue (obj+0x80/+0x8C) and whether signal/queue non-empty (missed wake?) ; hook AD8A68/AD8B30 or xref push side; then make PUMP_ITERS=0 default.
- (Arbeit22) MGOM thread: ctor 619198 (called 6C80D0, runs early, alloc ok) calls AD4754 (thread obj AF003C + vcall slot8 start + AD4390) with entry opd 0x1616868 (code 6170AC = loop calling 616C80 until obj+4==1). NO sys_ppu_thread_create with bt via 61920C in 70 s, no thread chain has 6170AC; only 1 pool job run (code F7D514). So MGOM loop thread never starts = real cause; main (6171D0) waits for it. Oracle: pooled AF0B94 worker 9qstY runs it.
- (Arbeit22) Next: gdis AF003C + vcall slot 8 of its result (vtable) -> find why thread start is skipped/deferred (pool/worker job push); log at AD4754 exit + slot8 target; compare AD4390.
- (Arbeit22) CORRECTION: with GT6_PUMP_ITERS=0 the MGOM thread (entry 6170AC, own stack) DOES start and runs 616C80: loads boot.mproject/boot.adc/BootProjectComponent.gpb/PresentsRootSCEE.gpb, game tick [A7] 68FF84 #1/#2 runs (real progress vs pump). Probes a22lp2/a22ts.
- (Arbeit22) New blocker: tid30 [LWM-BLOCK] lwm=0x017E8888 owner=tid1 (main holds it while blocked in AE2844 wait in 6171D0, chain 7A0A54<-A746E8<-A5C070<-AA55FC<-A2F290 inline task). Next: who locks 17E8888 on main (xref/gdis A746E8..A5C070 guard) and why oracle main does not hold it; also if main is the task runner at all.
- (Arbeit22) Pump off: MGOM job 6170AC runs on pooled worker tid34 (AF0B94->AD1670 queue; created via 10BB400 in AF0254), enters 616C80 (loads boot.mproject/adc/Presents gpb, ticks 68FF84 x2) but never logs a return iter, yet tid34 is idle in AD1670 at 50-100 s => 616C80 exits abnormally (setjmp/fiber guard C61F88/C620AC?) or main-side deadlock: tid30 blocked on lwm 17E8888 owner=tid1 (main, inside 6171D0 wait). Next: log 616C80 exit path/setjmp guard hits (C61F88) on tid34 and who owns 17E8888 (PS3_LWMUTEX_TRACE=1).
- (Arbeit22) ROOT of lwm 0x17E8888 hold: it is allocator mutex #1 (table lock C61330/C626F0). Main takes it in C58EC8 (array grow) -> realloc C58E3C->B0CDB4 FAILS -> C58FE8 returns w/o unlock => lock leaked forever, pacer tid30 starves. Same with pump default.
- (Arbeit22) realloc fail cause: malloc (heap 17B4C78) hands out 0x7FFFE000.. (win2 base 0x60000000 + id FFFF) but B09520 ptr-lookup (id=(ptr>>13)&0xFFFF) returns -0xA3 (table valid ids 0..7FFF only). Allocs via sc330 mmapper_allocate_address (256MB@0x10000000-align, 512MB). Check our mmapper addresses.
- (Arbeit22) FIX FOUND: sc330 window2 (512MB) landed at 0x70000000 (sys_vm reserved skip) -> not 512MB aligned. mapper_address now aligns >=512MB windows to size (0x60000000). Result: lwm 17E8888 no longer stuck, 5700 flips, 54 file opens, ProgressDialog gpb. Patch: patches/gt6-mmapper-512m-align.patch.txt (third_party is gitignored).
- (Arbeit22) Next: run default env (GT6_PUMP_ITERS default) + 220s probe with fix; check main menu/frame capture; if pump still hacks main, set PUMP_ITERS=0 default. Do not repeat: heap/lwm 17E8888 chain closed.

## Arbeit32 (2026-11-25) 1.22 data overlay measurements
- Overlay: update 12381 files linked, base 24285 linked, 8306 shadowed; main.adc sha256 1ce3993c...a69b; VER_INFO 20150915-114939.
- Env: GT6_VOL_ROOT=work/gt6_vol_a32;A29_JMP=1, no -Boot. Frame 3000 legal screen, frame 6000/8000 'Sony Computer Entertainment presents'.
- Runs: 094802 pure call at 48 s (1DA43C); 095327 'map/set too long' at 2 s; 095405_1 stall 58 loads; 095405_2 2 purecalls, survived 150 s;
  095738 Presents at 129 s (85 loads); 100013 stall, tid1 chain 6D2EA8<-5F3C88<-78E3F4<-EF2834<-5EFA60 (PS3_WD_AT=60);
  100207 (affinity 5) one stall, one progressing; 100449_1 'map/set too long' at 51 s.
- Presents script: projects/gt6/boot/presents_sequence_common.ad: changeImage(path); Thread::Sleep(sec); SCEE table common/JP/scei 2.0, scee/notice 1.0.
- Other noise: shared_ptr release AD23EC calls garbage vtables on objects at 0x6FFFF5E0..6FFFF640 (tid27/30), r2/r12 garbage.


## STATE trim 2026-11-25
- Binary still carries diagnostics (022/023 generated are clean, diagnostics in work/_bk_*): run `scripts\build-all.ps1` before a baseline.
- MAIN LOOP 146E8: task AFDFC0 = boot check (strcmp BCES01893), legitimate, 0 iterations. Details in eu-boot-log.md.
- GAME LOOP 1.22 = 0x616C80 (1.00: 568800), thread entry 6170AC, tick 68FF84, running (tid1/tid30); details in eu-boot-log.md.
- (Arbeit32) 1.22 data route works: overlay work/gt6_vol_a32 (scripts/make-vol-overlay.py), env GT6_VOL_ROOT, no -Boot, no A22_BLOCK. MMuseum2 NameError gone. Arbeit31 PFS-deadlock line dropped.
- (Arbeit32) 1.22 boot overflowed the 1 MiB host stack (0xC00000FD) -> /STACK:0x4000000. Then legal screen at frame 3000 (probe_a32vol_20261125_093727_1).
- (Arbeit32) Stale 11-22 savedata -> DISKFULL 0x1a (=SQLITE_NOTADB, GameRecord.ad:178, /dev_hdd1 game024.db). Saves moved to work/ARCHIV -> frame 6000 'SCE presents' (probe_a32nosave_..094437_1).
- (Arbeit32) Both early aborts = __cxa_pure_virtual 0xC68B8C (callers 2CD5F4, 1DA43C dtor): teardown race, 48 s abort at PresentsRootSCEE load. Guard gt6_purecall logs + returns 0.
- (Arbeit32) probe.ps1 now gives each run an empty /dev_hdd1 (GT6_HDD1); ctxwatch.py reads own transcript (CLAUDE_CODE_SESSION_ID).
- (Arbeit32) Runs are nondeterministic (same binary/env): Presents frozen (frame 8000), stall at setting.mproject, abort 'map/set<T> too long', purecall (guarded, run survives).
- (Arbeit32) Stall = tid1 loops forever in a script-engine std::map walk (func_006D2EA8/6D2BC0, null node, HOTREAD8 0x21). Same module (6Dxxxx) in 'too long' stack -> container corruption.

## Arbeit33 (2026-11-25) boot race measurements
- PPU_RESV_STORE was a no-op for guest stores (hook only in HLE ppu_memory.h; inline stores bypass). Fixed in patch gt6-a33.
- 100 s runs probe_a33ab*: base 3 map stalls/aborts + 3 aborts/AV; resv 5 stalls, 1 Presents; affinity 1 (whole process) 6/6 Presents at ~5 fps.
- 150 s probe_a33pin* (PPU_ONECORE=1): 3 alive at 150 s, 1 STALLED@85, 2 exit 0xC00000FD (85 s, 151 s); host stack repeats func_00C59350+0x518/0x743.


## STATE trim 2026-11-25
- (Arbeit32) -Affinity 5 (2 CPUs) still stalls. PPU_WWATCH=0x6FFFF610 silent; SPU_DMA_WATCH output unrelated (range check suspect). Next: find the lock around that map (race vs corruption).
- (Arbeit32) PPU_RESV_OFF=1: 4/4 stall or flip freeze (worse than default, 2x2 runs a32resv*) -> atomics/reservation semantics implicated; check them first.
- (Arbeit32) PPU_RESV_STORE=1 (plain stores break reservations), 4 runs a32rs*: 2 reach 96/102 loads + survive 100 s (3 savedata loads = boot restarts, last PresentsRootSCEE), 2 stall.
- (Arbeit33) SOLVED boot race: 2x3 runs each, default 0/6 stable, PPU_RESV_STORE=1 (now covering guest stores) 1/6, 1 host core 6/6 to PresentsRootSCEE.
- (Arbeit33) PPU_ONECORE=1 (default in gt6 main.cpp, patch gt6-a33) pins only guest PPU threads: 6/6 Presents, no map stall, ~35 fps; tools boot-batch.ps1/boot-outcome.py.
- (Arbeit33) New blocker (2 of 6 + 1 stall): 0xC00000FD, endless recursion in allocator tree func_00C59350 (tid14 prio 224) = remaining corruption; test PPU_PRIO_MAP=1.

## Arbeit34 (2026-11-25) abort path + script nil error
- a34cap (frame 5000, pinned): run1 0xC00000FD@121s on tid1 (8146B8>89D4C8>AF55E0>AD4C14>AF0844>C51C38, r31=0 from -0x7818(r2)); run2 legal screen, one '(nil).ColorBegin'.
- TOC=01644F38; stdin/out/err slots 163DFEC.. valid in ELF; .got 163CF38..163EB64. pinp2 crash: same abort path on tid15 (printer label tid=14 is stale).
- '(nil).ColorBegin' present in 16 earlier a32/a33/a34 runs. Guard knob: GT6_GUARD=163d720:163d720.
- Guard dump: CD2ABC <- 9206A8 <- 9230F4 <- 1F6AD4 <- 1FA204 <- 1FA70C <- 1FA968 <- 8AF7F0 <- 2F53E8 <- 89332C <- 892998 <- 8A7B90; r28/r31=6FFFE900/04, r29=3B948DD3-class garbage; first stores hit NULL+0x38.
- a34g/a34g2 (4 runs, guard build): all alive at 140-150 s; one hit: obj=2C begin=0 end=0 lr=CD2B2C r27=619E0000 vec=6FFFE910..6FFFE918.


## STATE trim 2026-11-25
- (Arbeit33) 150 s a33pr (4+4): pin 1 stall@83 / 3 alive; PPU_PRIO_MAP=1 1 AV / 3 alive -> no clear gain, stays off. No 0xC00000FD this batch.
- (Arbeit33) New modes while pinned: 3/8 run 60 fps but stop at SettingProjectComponent.gpb (tid1 monitor wait A4FBE8?); 14/14 pinned runs no map stall.
- (Arbeit33) CORRECTION: C59350 is fflush, not an allocator tree: r3=0 -> recurses on 3 FILE* at r2-0x6F4C/-0x6F48/-0x6F44; any NULL (or r2=0) = endless recursion -> 0xC00000FD.
- (Arbeit34) 0xC00000FD is a symptom: operator new (C51C38/C51D64) returns fail/garbage -> abort C52CD4>C52C5C>fflush(NULL); TOC slot 163D720 reads 0 / FILE* gone = guest .got corrupted (or r2 bad).
- (Arbeit34) KEY script blocker: every Presents-reaching 1.22 run throws '(nil).ColorBegin' (main.adc GameItem.ad l275: SPECDB AVATAR_* row for code missing) right after game024.db open -> boot script dies on legal screen.
- (Arbeit34) ROOT of 0xC00000FD (GT6_GUARD=163d720:163d720, probe_a34grd_..110635_2): AE6388 (zero 8B items from *(obj+8) to *(obj+0xC)-8) gets garbage obj -> wipes NULL page..TOC.
- (Arbeit34) Caller CD2ABC loops vector obj(619E0000)+0x3C55C {begin+4,end+8}, AE6388(*it+0x2C); storage ~6FFFE900 = same area as earlier garbage (6FFFF5E0..): suspect heap aliasing/overlap.


## STATE full copy before Arbeit35 trim (2026-11-25)
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





- (Arbeit34) CONFIRMED (probe_a34g2_..): guard fired, CD2ABC vector 6FFFE910..6FFFE918 holds 2 NULL entries -> AE6388(0x2C) begin=end=0 = wipe; with guard no TOC wipe. 4 guard runs: 0 x C00000FD.
- (Arbeit34) Guard [A34G] lives only in gt6/generated ppu_recomp_023.cpp (clean: work/_bk_a34/ppu_recomp_023_pre.cpp); not yet persisted in post-lift.

- (Arbeit34) CD2ABC: lock 1713700 (920458/920480), CD255C, loop; a34g2 run2 still stalls (hot=19443, flips 2159, last UIKit gpb) -> pinning does not cure all container corruption.

## Next step
(Arbeit32) Fix the boot race/corruption: first compare PPU_RESV_STORE=1 vs default (>=4 runs each); then audit PPU atomics/locks (lifted lwarx/stwcx + ppu_stwcx32 vs plain stores, ldarx, sys_lwmutex/lwcond recursion, static-init guards).
Test: runs a32 env, count stall (hot>0 on 6D2BC0) / "too long" / purecall over >=4 runs; baseline (default) about 3 of 9 reach Presents-or-later without stall/abort.

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
- (Arbeit23) Calltrace 60-100s steady (probe_a23ct_20261124_174454_1, CALLTRACE=400 AFTER=60): tid30 pump only (ADB918>ADA4C0>AFB6B4>AFD93C, B119xx handlers); F7AF20 = global-singleton getter (obj+0x10 byte), config query, not a wait.
- (Arbeit23) tid27 is ACTIVE per frame (not idle): 8933E0>892CA0>831330 / 89332C>892C30>7B501C; 8AF730>7B504C>6C7644/6C8D48>1D81F8 job executor; 8A69B4>8EBC3C/8EB94C, 8FEF8C>8E8204 (obj 170F2E0/170F340). Next: CALLTRACE_FROM=7B504C or R3 filter on 7B504C targets to name the scene task; read its state via snap_walk.
- (Arbeit23) tid27 per-frame: 7B504C calls 6C7644 (->61BB0C) + 6C8D48 on obj 6FF7F550 (vt 15B5668, same addr in snap_74601453 = MGOM main object). Calltrace FROM=7B504C run probe_a23ct2_20261124_174841_1. 61BB0C+0x1B16 -> 69098C (+0x2BEB recursion) = scene/task update. Next: CALLTRACE_FROM=69098C + R3 filter to list scene task objs/targets per frame; find the one with a wait/fade state.
- (Arbeit23) 69098C = recursive node-tree update; 2 sibling nodes 6FF42AB0/6FF43550 (vt 15B54A8, type 0x17, parent MGOM obj 6FF7F550 +0x14) updated per frame by direct bl (no indirect virtuals on them). START/CIRCLE presses (40/60/75 s): opens unchanged (119 same as no-press). Heap addrs stable across runs w/ same env (snap_75656765).
- (Arbeit23) Chain depth limit hit (tid27 job > MGOM obj > node children). Strategy switch: find 1.22 script VM/timer that drives Presents project (1.00 VM 9EEA88/9F0748 = 0 calls); search handler-table dispatch fn (xref --imm) or compare oracle thread creation after MGOM.start.
- (Arbeit23) No thread chain contains A2F290/A2F0AC at 40-100 s: Presents is driven natively by MGOM node tree (69098C), not the task VM. Next: static read 69098C node update (type 0x17 nodes, +0x28 idx, +0x2C float) -> find fade/timer field; or oracle-vs-ours diff of what main does after MGOM.start.
- (Arbeit23) CAUTION: heap addrs only stable w/ identical env; snap_7610/7623 (PS3_SNAP_AT only) have 6FF7F550 all zero -> use snap_75656765 (CALLTRACE env). MGOM obj time 2A0/2A8 advances ~62/s (dt 1/60 ok): time NOT the blocker.
- (Arbeit23) Nodes 6FF42AB0/6FF43550 child containers (+0x30 402F0F90/F30) are EMPTY sentinels (size 0): scene tree has no elements; Presents image likely stale buffer. Root = project/scene never populated (load stall), not fade. Next: find who adds nodes (node add/attach fn; xref writers of node+0x14 parent / map insert) and why no scene project gets created after boot gpb loads.
- (Arbeit23) MGOM init 619198 (tid1) creates 3 nodes via vcall +0x128 (6CA964): root idx0 6FF42000 (children vec 4028FDA0=[n1,n2]), n1 6FF42AB0, n2 6FF43550 (vt 15B54A8, 0x840 B). n1/n2 maps at +0x30 empty sentinels. Next: who inserts items into n1/n2 maps (project/scene attach); WATCH env?
- (Arbeit23) PPU_WWATCH=<ea> + PPU_WWATCH_LEN + PPU_WWATCH_MAX works (prints [ww] writer fn/lr). Heap block 402F0F90 is reused (alloc churn) -> node containers need watch at node-creation time, not post-hoc addresses. Presents-empty-tree theory unverified: draws 2 ops may be stale.
- (Arbeit23) WWATCH on node1+0x30 shows only zeroing by 6071AC (vector stores likely unhooked): inconclusive. Draw (2 ops) elements likely in root node0 6FF42000 (lists at +0x18 4035A390); node0 update path not yet traced (69098C only calls n1,n2).
- (Arbeit23) REFUTED: node+0x1A2 'active' flag is 0 on all 3 MGOM nodes (only set in node ctor 67ED80); forcing 1 (A23_ACT env patch in 6CA964, binary carries it, generated restored): no new opens (119), frame still non-black 1%. Node0 not updated per frame (gate 61BCE8) but activating changes nothing.
- (Arbeit23) Load order (run.log.err): boot.adc, BootProjectComponent.gpb, PresentsRootSCEE.gpb(722K), dialog.mproject/adc + Dialog/Confirm/Progress gpb, then GT6.0-5 data packs, stall. Oracle log has no file-level opens (no compare). Next: what should request the next project after Presents: boot.adc script/next-project trigger; locate via who reads PresentsRootSCEE scene 'finished' callback.
- (Arbeit23) boot.adc strings: boot_functions.ad has waitUntilTrophyInitialized/endInitTrophy/setWaitInterfaceReady/loadEveryWhereForGame/getBackgroundLoadResultFromAllFile -> boot script waits on trophy init + savedata background load. Matches eu-boot-log Arbeit8/9 (oracle 3 AutoLoad2 PDI threads then F044+sceNpTrophyInit; ours 2). Next: make AutoLoad2 return -4,-4,ok (3 calls) via GT6_SAVE env / cellSaveData.c, see if trophy init (10BDD20 chain) then runs and Presents advances.
- (Arbeit23) Save knobs in cellSaveData.c: GT6_SAVE_NODATA (l.1354 returns NODATA instead of compat OK), GT6_SAVE_CBRES (l.978). Try GT6_SAVE_NODATA=1 + A22_BLOCK run, count AutoLoad2 calls vs oracle 3 (-4,-4,ok).
- (Arbeit23) GT6_SAVE_NODATA=1 run: still 2 AutoLoad2 calls (BCJS37016-GAME6), no F044/TrophyInit; knob does not reproduce oracle 3-call sequence. Next: compare which thread issues AutoLoad2 #3 in oracle (PDI thread, script fn AF0B94).
- (Arbeit23) Our save seq: AutoLoad2 #1 funcStat -4, #2 funcStat 0 -> GT6.0/GT6.1 read (16MB each). Oracle: -4,-4,ok. Unknown why oracle needs 2nd -4 (second dir? retry via script). Next: oracle_seq.py on RPCS3 log around AutoLoad2 to see dirs/args per call.
- (Arbeit23) Oracle AutoLoad2 #1 (line 155401): same dir GAME6, fails CBRESULT 0x8002b401 after page faults in RPCS3 HLE (oracle quirk, like our -4). Save seq difference NOT meaningful; drop save-count chain. Next: after load, oracle does LoadModule 0xF044 + trophy init from script thread: find in ours why script (AF0B94 thread) does not proceed after AutoLoad2 ok (thread state at 40s WD).
- (Arbeit24) node state +0x144 (1/2/3 in 69098C) is 0 on MGOM nodes; setter 68B450 (state=1) runs on tid30 for OTHER (scene) objs. MGOM nodes 6FF42AB0/6FF43550 never started: dead end, dropped.
- (Arbeit24) Script natives traced (trace_enter, 250 PDINetwork/NP natives + ctt): with A22_BLOCK tid30 runs getNP,setCommunicationId/Passphrase/Signature,setTicket/CommerceServiceId, NP init (B4ADE0 ok) then NO more PDINetwork/Trophy natives (initializeTrophy 9B20FC never). Unblocked: tid1 getNP -> finalize (Term).
- (Arbeit24) CALLTRACE_LR=A74734 (script native call site) lists every native: after init, tid30 loops per frame on MManager/MUpdateContext/MRenderContext + HObject natives (script menu loop alive, ~430 calls/100 s). Boot script past init; Presents idle in script loop.
- (Arbeit24) WARNING: work/_bk_a22 016 lacks A22_BLOCK; patch re-created (gt6/generated ppu_recomp_016, copy work/_bk_a22/ppu_recomp_016_blockpatched.cpp). Calltrace lines are '[CALL] ->' (not CALLTRACE).
- (Arbeit24) Next: which script task calls initializeTrophy/waitUntilTrophyInitialized: boot_sequence_common.ad via tools/adch_disasm.py (grep initializeTrophy) -> find condition before it; check if the call sits behind network_available/PS3 'isOnline' gate.
- (Arbeit24) KEY: boot_sequence_common.ad = state machine, one SET_STATE-2 yield per state: ...initNetworkObjects(l100) initOrganizer(107) RaceOperator(111) OnlineUtility(117) OnlineSession(121) Lobby(126/128) PDINetwork.initialize(132) beginInitTrophy(135, gated GetUseNPTrophyFlag) initGrim initSpecDB initMenuDB initUserDB. PDINetwork.initialize (9AE5D4) and GetUseNPTrophyFlag (cache 16ED790 =0 in snap) never run => sequence stalls BEFORE l132.
- (Arbeit24) Next: find last reached state: trace natives of l107-128 (MOrganizer init, MRaceOperator, MOnlineUtility/MOnlineSession ctor, enableNetworkEventCallback, Lobby.setOrganizer) via CALLTRACE_LR=A74734 [CALL] list (r3 obj) or tools/adch_disasm dump (/tmp boot.dis: python -I -X utf8 tools/adch_disasm.py work/gt6_vol/projects/gt6/boot/boot.adc); first missing native = stall; check what that native waits on.
- (Arbeit24) FOUND stall state: first-seen script natives order (probe_a24ct4, CALLTRACE_LR=A74734) ends at MGameDataUtil 815ED4/815BDC + MSaveDataUtil 8146B8, polled every frame => boot state machine sits in checkGameData (l80) before initNetworkObjects(l100). Poll natives never report done.
- (Arbeit24) Next: read 815ED4/815BDC/8146B8 (gdis --fn): what they return per frame (r3 result, pending/done/error) + which native fn sets done (async completion flag); log their r3 return via trace patch; compare with oracle (AutoLoad2 3x, then LoadModule F044). Fix completion source -> script advances to initNetworkObjects/PDINetwork.initialize/beginInitTrophy.
- (Arbeit24) 8146B8 = MSaveDataUtil method: vcall obj+0xC getter -> 89D59C(obj,val) -> bool via A74EDC (HBool). Trace 89D59C return + the vcall target to see why false/pending.
- (Arbeit24) loadEveryWhereForGame DONE (tid37 worker reads GT6.0-5, tid38-40 join/exit) but after it NO script native is dispatched at all (ct4 last [CALL] before GT6.5 open); tid30 pump (ADA4C0>ADB918) alive. Script task after l94 (StopWatchUtil.end, then l100 initNetworkObjects) never resumes: find what resumes the script task (state machine tick/yield resume) after loadEveryWhere: who should call task resume; compare oracle.
- (Arbeit25) l94 loadEveryWhereForGame is a SCRIPT fn (main.adc SaveDataUtilGT6.ad l797: SaveDataUtil.load(context,data); SET_STATE 1 = task wait). Task obj 40393B90 (tid30) A2EA5C hook [A25ST]: final transition st=1 ev=1 (AA1A08) then NEVER polled again (A2ED74 callers A305AC/A2F7B4 stop); earlier st=1 ev=2 wake came once from VM native -> A2DD98 (HMonitor-style wake A4FBE8).
- (Arbeit25) Next: 2nd wake never fires: find who should call wake A4FBE8/A2DC48 when SaveDataUtil.load (native 8130AC->812638) finishes (completion cb on tid37); log 812638 args + A4FBE8 callers; compare nil context (l94 passes NIL). Generated 022 carries A25ST/A25PL/A25BT hooks (clean: work/_bk_a22/ppu_recomp_022_clean.cpp).
- (Arbeit25) HMonitor wait (A4FBE8 r3=403A0430 task B90, once) resumes B90; its LAST poll runs via node START path 616EC8>616620>68FDB4(+0x96 flag, one-shot)>68FE0C>683318>A1EAD0>A30578 (683318 <200 calls = one-shot, not per frame). After final SET_STATE 1 (ev=1 AA1A08, line 1393) B90 never polled: normal polls came via node tree 6B7E4C/6B7D0C (69098C); tid30 loop itself alive (AD4294>AF03B4 2163 calls).
- (Arbeit25) Next: B90 re-poll must come from node-tree update; find which node owns B90 (task list +0x2c/+0x38/+0x44 of node, 683318 flush) and why its tree update 69098C skips it (node +0x144 state 0 / +0x1A2 active, see Arbeit23/24). Try: A23_ACT-like force also on node start flag, or run poll of B90 manually each frame (workaround) to reach l100 initNetworkObjects.
- (Arbeit25) REFUTED: A25_POLL (call 683318 every frame from 68FDB4 once +0x96 set) -> B90 still never re-polled (queue lists empty; B90 not parked there). Gen 022/014/017 carry A25ST/A25PL/A25BT/A25WK/A25LD/A25Q/A25_POLL hooks (clean 022: work/_bk_a22/ppu_recomp_022_clean.cpp).
- (Arbeit25) Next: find where SET_STATE-1 task B90 is parked after final yield (task obj 40393B90: read its fields via snap_walk; parent/owner list ptr) and which tree (6DD844 project tree 6B7D0C) should poll it; B90 polled by 6B7E4C before HMonitor wait, so check whether owner node dropped out of the tree after wait.
- (Arbeit25) Skip-load bypass (boot.adc 0x16B43 JUMP_IF_FALSE->TRUE, no GT6.x loads): SAME stall (task B90 polled once after HMonitor wait, then never) => NOT save-load related; generic: after wait-resume no per-frame task poll. Restored boot.adc (bk work/_bk_a22/boot.adc.pre25).
- (Arbeit25) All task polls seen are inside project start 6DD7C8 (one call, tid30; 6DD3C4 loads project, 6B5570 attach project->node vcall 180/184, 6D18F4) or node start flush 683318 (one-shot). Per-frame task poll driver for attached project missing. Next: node update (69098C children n1/n2 empty per Arbeit23) never reaches project tasks: check what 6B5570 attaches into (r4 6FF7B550) and whether per-frame project update (vcall) is invoked; hooks A25AT/A25P2/A25P3 in gen.
- (Arbeit25) 6B7C48 = recursive node update(node,dt): optional vcall 0x15c if flag(+0x58 bit), then children list +0x40 -> child vcall 0x178 (recursion); root caller 6A6908 in 6A68C0 (vtable-only, no direct callers). Task polls (A30578) happen under this tree. Next: find vtable slot/owner of 6A68C0 (xref --imm of its OPD) and whether it runs per frame after project attach.
- (Arbeit25) 6A68C0 OPD (161AA28) sits in vtable slot at 15B3358 (class vt base maybe 15B31E0 if slot 0x178; MGOM vt 15B5668, node vt 15B54A8 are different classes): find that class (xref --imm of vt base / ctor) = the project/scene class whose update must run per frame.
- (Arbeit25) Project/scene class vt 15B31E0 (ctors 6A5C14/6A90A0/6A9628; slot 0x178 update = 6A68C0). snap_83435343 has 5 instances: 6FF38200,6FF38600,6FF39400,6FF86E00,6FF87800 (snap_walk obj; check +0x28 state/+0x40 node/+0x58 flags; which one holds boot task B90 and is it in MGOM node child list).
- (Arbeit25) 5 vt-15B31E0 instances in snap_83435343: +0x40 = self+0x7C (sentinel, empty child lists), +0x28 = 0x10/0x13/0/0x63/0 -> these are leaf scenes, not B90 owner; B90 owner project still unidentified (find32 40393B90 holders 40365FD4/40389EFC/403BA6A8/403C9230 = list nodes; 403C9228 list head vt 15D9A70).
- (Arbeit25) B90 owner chain: list head 403C9228 (vt 15D9A70) <- +0x14 of 403DB190 (vt 15DA110, +0 = owner 6FF86E00) = project (vt 15B31E0, +0x28 state 0x63, +0x14=0x62E). Next: read project 6FF86E00 update (6A68C0) gate: state 0x63 meaning, who calls its slot-0x178 per frame (parent child list of MGOM node).
- (Arbeit25) 6A68C0 (project update) has NO internal gate: 6A65D8, then 6A58D8, then 6B7C44(root node +0x1D0) tree update. So the missing piece is its caller (parent vcall 0x178 per frame): find parents of project 6FF86E00 (find32 holders) and why they stop calling.
- (Arbeit25) find32 6FF86E00 holders: 402F5E9C, 402F6FF8, 402FADD0/AE08/AE40/AE78/AEB0/AEE8 (many = project registry/array entries, 0x38 stride). Next: obj 402FADC0 (registry entry) + find who iterates the registry per frame calling slot 0x178.
- (Arbeit26) 6A68C0 (project update) is called ONCE per project, from load fn 6DD3C4 (indirect, tid30), never per frame (CALLTRACE_TO). 6DD7C8 project load is called only from MGOM node start 616DD4 (+6DDA78).
- (Arbeit26) REFUTED: forcing 6A68C0 for all tid30 projects every ADB780 tick (A26_UPD hook, gen 014/023 restored from work/_bk_a26): B90 still not polled after final st=1. Parked task needs a wake, not a tree walk.
- (Arbeit26) Load done signal = 8A4510 (tid37): sets obj+0xA90C=1, AE2908 signal event obj+0xA910. Reader 89AC1C (isLoading thunk 89D400, script native) is NEVER called; natives 8146B8/815ED4/815BDC/8130AC run once each.
- (Arbeit26) Next: who should resume B90 after load: find the waiter of event obj+0xA910 (AE2908 signal) and the wake fns A2DCBC/A2DEB0/A2E1F8 (A2DCBC fired once from script native lr A7492C before load). Compare with the HMonitor wait in script.
- (Arbeit26) REFUTED: direct A2ED74(B90 40393B90) per tid30 tick (A26_TP): task goes st=3 (ended) at once, no new natives; A2ED74 is not a plain poll (A2EA5C ev=3 inside). Gen 014/023 restored (work/_bk_a26); binary still carries A26 hooks, gen 022/017 carry A22EN hooks.
- (Arbeit26) Polls are event-driven, not per frame: only ~170 A25PL in whole run; B90 poll at 1443 comes right AFTER tid37 load end (completion DOES trigger one flush), resumes script (st2->0->1), then script yields again and nothing more. After that tid30 pump calls only infra (B119xx, F7AF20 cfg, AE73BC, AFC128).
- (Arbeit26) A2EA5C(task,newstate) = task state machine (0 new,1 run,2 wait,3 end). Task map: hash map (vt 15D72E0 at 403869A0, key = project 6FF86E00, nodes 403DE0C0/403DE060) holds project->task wrapper; owner/updater of that map NOT found (only held by stale block 403D2484).
- (Arbeit26) Next: after resume at 1445 script yields at its NEXT wait without natives: dump what script code runs between l94 resume and next yield (boot.adc disasm after loadEveryWhereForGame at l94; trace VM opcodes or compare with oracle); or find the yield type (st=1 SET_STATE 1) and who re-ticks it.
- (Arbeit26) KEY: per-frame task driver = loop in 6B7D0C/6B7E4C: do { A2F860(task) (true iff A2F290 ret==2) ; AD2998 quit check ; 88F4F0 frame wait } while true. Hook A26RUN: B90 last A2F290 ret=2 st=2 (wait) then NO more calls -> loop thread stuck in/after 88F4F0 or AD2998 exits it.
- (Arbeit26) Next: log after A2F860 in 6B7E48 loop: AD2998 result + entry/exit of 88F4F0 (thread id, blocks where: bctrl 88F520/88F560, AEFEC4, AD3BD8); WD stack of the loop thread at 40 s. Gen 022 restored (work/_bk_a26/ppu_recomp_022_pre.cpp); binary has A26RUN hook.
- (Arbeit27) REFUTED: loop 6B7D0C/A2F860 is tid1 only, exits at once (ret 0); not B90's driver. B90 (tid30) polled via A2F860<-737C60 (vcall 0x120 at 68710C inside fn 686C58), ~200 polls in ONE 13 ms burst at ~1.1 s (ret=2 wait), then never.
- (Arbeit27) B90 wait = timed wait in A4F938 (deadline now+1.75e6 us, clock AEFD7C ok). Burst = 686C58 iterates ~137 nodes (66C600 ret 0 each) then returns. Next: who calls 686C58 (hook A27G in gen 014) and why only once.
- (Arbeit27) 68FF84 = one-shot node START (guard node+0x96; called from 616C08 loop over MGOM children +0x1D4), not a tick. ~100 starts of the 3 nodes then no more B90 polls.
- (Arbeit27) KEY: MGOM loop 616C80 (tid30, caller 617100) BUSY-SPINS ~30k iter/s (2.1M in 60 s), no frame wait in the loop. Possible missing vsync/time gate vs oracle; polls happen only in the first ~100 iters.
- (Arbeit27) Hooks A27L/T/W/C/D/E/F/G/H/I in gen 014/013/015/022 (clean: work/_bk_a26/*_a27pre.cpp, 013 *_a27clean). Run: probe.ps1 -Boot notut -Env A22_BLOCK=1. Next: why +0x96 stays 0 ~100 iters (setter 68FDB4) and what 616C80 should wait on per iter.
- (Arbeit27) 616C80 flags +0x4c(stage A)/+0x4d(stage B, project load 6DD7C8) both 1 after ~138 iters (w4c=0101xxxx); 6170AC loop = 616C80 + sys_ppu_thread_yield (AF0230), spins 30 kHz. Per-iter work: +0x4d -> 6D968C(proj) at 616FA0; +0x4c -> vcall at 616FFC; 6CEA7C+AD2998 (quit) at 616F14. Hook these.
- (Arbeit27) KEY: workaround A27_POLL=1 (gen 013, 6170AC loop tid30: A2F860(B90) every 16 ms while st 1/2; task ptr from gen 022 A2F290 wrapper g_a27_task): B90 runs ~7 polls (ret=1), 4 natives (A6C8A4,809D40,A6C8A4,A6C8A4; hook A27N in gen 022 at A74734, needs A27_ALLN=1), then ret=0 = task ENDS. No new loads/PDINetwork natives. So script after l94 ends early (error/exit?), not just un-polled.
- (Arbeit27) Next: name natives 809D40/A6C8A4 (registration code; adch_disasm of boot.adc after l94), find why VM returns instead of reaching l100 initNetworkObjects (native result false/err -> script abort?). Compare A2F290 exit path (ret 0 vs state 3).
- (Arbeit27) Decode: A2F860 ret = A2F290 ret decoded (A2F290: 0 run-again, 2 wait(timed list A4F938), 3 ended via A2ED74=set state 3+flush). Forced polls: poll1 -> 4 natives (StopWatch end/log), polls 2-7 A2F290=0 no natives, then 3 (script returned). boot.adc l94-l102: StopWatchUtil.end, log(l100), SET_STATE 2, initNetworkObjects(type) -> expected natives never seen. Next: VM op trace in A2F0AC exec loop (ops after SET_STATE 2) to see why script returns.

- (Arbeit28) A2F0AC/A2F290 frames: B90 VM steps run on tid1 only before the wait; A30578 = task destroy (A2ED74 terminate + clear lists), polled via node flush. A4FBE8(sched,task,secs)=timed sleep (deadline list +0x14), A4F938 only caller A2F340 checks it.
- (Arbeit28) KEY: B90 (40393B90) strong refcount +4 drops to 0 (release A1EAD0 lr=A7BC84 in script-runtime epilogue, tid30), object freed+address reused; timed-list wref rc=0 so A4F938 never expires entry; A27_POLL polls a FREED task (ret=1 bogus). Next: find who releases B90 at A7BC84 (fn start unknown, gdis --fn fails) and why last ref drops before script ends (missing ref holder?).
- (Arbeit28) Hooks A28_OP (gen022: A2F0AC step log, A4F938 list log A28L/A28T) + A28_NOFLUSH (A30578 skip at st 1/2: no effect, B90 freed anyway). Gen 022 clean copy: work/_bk_a26/ppu_recomp_022_a28pre.cpp.
- (Arbeit28) CORRECTION: also in baseline (no POLL) B90 strong rc 1->0 at ~1.1 s: B90 = task created by A7BA60 (run-script-call: A30B8C allocs 0x80 task into local shared ptr, A2FFCC runs it, A2F290 ret 1/3 exits loop, A7BC84 releases local handle). Nothing else takes a strong ref -> B90 freed while st=2 (timed wait); A27_POLL polled a freed obj.
- (Arbeit28) Next: who should keep B90 alive in oracle: 0x38 obj (A9BEC0 ctor, holder r1+0x78 via A1EBBC) built next to the task in A7BA60, or A2DAA8(task,sched) link in A4FBE8 (r4=task; check if it takes a strong ref/adds to list +0x18). Static first: gdis A9BEC0, A2DAA8; then ww on rc +4 for who SHOULD inc after A2FFCC returns. A2FFCC exit rule: A2F290 ret 3 or 1 -> return, ret 2 -> A8604C sleep+loop, 0 loop.
- (Arbeit28) REFUTED pin: A28_PIN (keep B90 rc>=1 after A2FFCC in A7BA60) -> wref rc stays 1 but sequence same: node-start flush A30578 (A2ED74 terminate, st2 ev3) kills the sleeping task, restart finds empty frames. So flush at node start hits B90 while it sleeps: oracle must flush BEFORE B90 starts or not include it. Next: who adds B90 to the list flushed by 683318/A1EAD0 (task list +0x50/54/58 of node), compare order node-start vs script start.
- (Arbeit28) Dispose stack (A28_LR=1 A28S): A30578 <- A1EB2C(release) <- 683400 (flush 683318, release of temp-list entries after F1AA3C/F1A5D4/F19D4C moved node vectors +0x38/+0x44/+0x2c) <- 68FE0C <- 616650 <- 616ECC <- 6171FC <- 7A0AC0 (MGOM.start, tid1). NOFLUSH+PIN(+100)+POLL(>=4s): wref rc still 0, polls ret=1, no wake; B90 freed by other path. Next: read F1AA3C (erase/move semantics, rc inc?) or oracle compare.
- (Arbeit28) F1AA3C/F1A5D4/F19D4C = list remove_if-style (param r4 flag byte stb 0x1a8; lbz obj+0x20 test, move node to temp via 6C3ED0). Hook A28_NOREM/A28M (gen035): only 4 flagged objs seen, none B90 -> B90 enters temp list via the non-flag branch (r4 mode?). Next: gdis F1AA3C branches after 0xF1AB40 (what r4 selects) and who passes r4 in 683318 (r4=r31 ptr, not flag).
- (Arbeit28) Node start 68FDB4: 68FC3C,677198,6749DC then flush 683318 which swaps list head (6833C0-6833CC) and releases the OLD list entries (6833FC). B90 is in the old list at that time. Next: what 68FC3C/677198/6749DC put in the new list (B90 missing?) -> compare with oracle order; gdis those 3.
- (Arbeit29) Static: 68FC3C=rbtree erase, 677198/6749DC=list clear (node start CLEARS, builds nothing); 683318 = remove_if(F1AA3C/F1A5D4/F19D4C: move entries whose obj+0x20!=0 into temp list) then release temp. B90 not flagged => flush not the primary killer.
- (Arbeit29) A7BA60 (script call): task in local shared ptr r1+0x7c, A2FFCC(out,task) loops A2F290: ret2=A8604C sleep+loop (blocks caller, keeps task alive on stack), ret 0/1/3 return -> releases local ref. Oracle likely stays in A2FFCC sleep on ret 2; ours returns early. Next: log A2FFCC exit ret (A2F290 r3) + task +0x28 for B90 call.
- (Arbeit29) A29_LOOP (A2FFCC loop log, probe_a29loop): tid1 A2FFCC never sees ret 2/sleep; 40393B90 ends ret=0 st=3 at once on tid1 (heap reuse? 40393C10 ret=1 x15). Boot script task is NOT started through tid1 A2FFCC wait path -> run via tid30 scheduler. Gen 022 restored (work/_bk_a29/ppu_recomp_022_pre.cpp); binary carries A29_LOOP.
- (Arbeit29) REFUTED A29_KEEPALL (keep all flagged objs in 683318 remove_if): B90 same fate; flagged objs 402FA7xx unrelated. Task ptr identity by address unreliable (alloc reuse: 40393B90/C10/C90 reused many times on tid1).
- (Arbeit29) KEY: 616C80 stage-A: A8548C+C61F88 = SETJMP(try). r3==0 -> per-node tick 68FF84 (unstarted nodes, +0x96==0, runs 686C58 load state machine, polls tasks). r3!=0 (LONGJMP/throw caught) -> 616EB0 cleanup + 616620 -> 68FDB4 NODE START (flush 683318 kills sleeping B90). So node start is triggered by a longjmp. Next: find who longjmps (throw) into 616C80 try; is it legit (load-done) or spurious (our setjmp/longjmp impl, or error in tid30)?
- (Arbeit29) KEY: node start (flush kills sleeping boot task) is triggered by a C++-style THROW caught by try/setjmp at 616E60 (guest throw A856A0->longjmp C620AC; A29_JMP env logs [A29T]/[A29J]). First throw lr=A217B0 (assert/err fn) stk AA4A60<AA4C30<AA43A4<A2F130(A2F0AC VM loop)<A2F700<A86168<66E6BC<690058(node tick)<616EA0 on tid1. Script VM op AA4A60 raises error exception => script dies. Next: read AA4A60 (which check throws via A217AC), compare with oracle.
- (Arbeit29) Thrown script errors (A216F4 hook [A29E], same with -Boot orig): (1) "undefined module variable 'pdiext::MMuseum2'" m_code_frame.cpp l73, (2) "nil object cannot be used in '(nil).setPatchFunction'" l48. 'Museum' string absent from ELF -> MMuseum2 is script-defined (adc). Exception propagates: A2F290 try catch -> A2D848(task,exc) true => rethrow A2F73C => 616C80 catch => node start flush. Next: read A2D848 (script-level catch/handler lookup) + who defines MMuseum2 in oracle.
- (Arbeit29) A2D848(task,exc) returns 1 (rethrow) when no script catch frame; so error propagates in ours; oracle log has no script-error text (inconclusive). boot.adc has alias table (News2/Museum2/Tv2 -> pdiext::MNews2/MMuseum2/MTv2) but ELF native pdiext list (MBbs2,MNews2,MTv2,..) has NO MMuseum2. Next: who resolves module var (m_code_frame l73, caller AA4A60 via AA4C30/AA43A4): is lookup table built by native registrar from ELF list (missing MMuseum2 => our data/ELF mismatch?) or by script modules loaded later (ordering)?
- (Arbeit29) ROOT CAUSE CANDIDATE: our served scripts/projects are 1.00 disc tree (work/gt6_vol, pfs override plaintext) but ELF is 1.22. 1.22 ELF pdiext list has 14 modules; 1.00 ELF has 21 incl. MMuseum2 (removed in 1.22). 1.00 boot.adc references pdiext::MMuseum2 -> NameError throw -> node start flush -> boot task dies. Fix direction: serve 1.22 scripts (PDIPFS overlay in work/gt6_hdd0_rp via real PFS read: GT6_PFS_OVERRIDE=0 -Hdd0Src <abs path>) instead of 1.00 plaintext.
- (Arbeit29) GT6_PFS_OVERRIDE=0 + -Hdd0Src <abs>\work\gt6_hdd0_rp: real PFS read stalls after 17 opens (no draws, 240 s) -> cannot use real PDIPFS reads. Need 1.22 plaintext scripts: decrypt PDIPFS overlay entries for boot.adc/main.adc (key map GT6_PFS_KEYMAP, tools/gt6_pfs_*.py, stubs.cpp ~l190-420) and serve them from gt6_vol instead of 1.00 files; verify with A29_JMP (no [A29E] MMuseum2 error).
- (Arbeit29) 1.22 plaintext scripts: blocked. work/gt6_pfs_keymap.tsv absent (made from GTToolsSharp TOC listing; repo forbids AI running it, scripts/extract-gtvol.ps1). GT6_1.N are 36-303 B pointers; update data = PDIPFS/K (encrypted). Needs human: run GTToolsSharp on 1.22 update volume -> boot.adc/main.adc into work/gt6_vol (backup first).

- (Arbeit30) GTToolsSharp NOT run: its authors forbid AI use (eu-bces01893-compat.md l69, extract-gtvol.ps1). Do not run it; only the human disc owner may. Real route: guest's own PFS code.
- (Arbeit30) Guest PFS works for 1.22: GT6_PFS_OVERRIDE=0 -Hdd0Src <abs>\work\gt6_hdd0_rp reads/decrypts TOC + uncompressed files (fonts, gt6sys.sgd). No [A29E] reached yet (scripts not loaded).
- (Arbeit30) GT6_VOL_ROOT=work/gt6_vol_a30 (VER_INFO + junction font) = override serves only fonts, rest via guest PFS. Past fonts, stalls at first compressed file sound_gt/library/GT6.lib (PDIPFS/9/WX/DX).
- (Arbeit30) KEY: deadlock in compressed-stream pipe P=0177CE00: tid1 AAC4C4 waits; tid9 AC78F4 (push input) waits event P+1BF8; tid5 inflate AC7A4C->AC79C4 waits P+1B98; AC74FC (signals 1B98, waits 1B68) never called.
- (Arbeit30) Next: find AC74FC caller chain (wrapper tail-calls at AC75C0; vtable) = who should provide output buffer (tid1 or tid9, "loadHeaderOnly"); check lwcond HLE order (sysPrxForUser.c l733) / Windows spurious wake: AE27AC does not recheck flag 0x29.
- (Arbeit30) AC75B0 (sets P+0x1c28=1, tail-call AC74FC) is vtable-only; snapshot has 1c28=1 (also set by thread AC7CE8 at AC7D7C). Hooks: tools/trace_enter.py (A22EN, binary carries them; gen 023 restored, bk work/_bk_a30).


## Arbeit35 (2026-11-25) guard persisted, ColorBegin bypass, AdjustScreen/AutoSave reached
- Overlay: make-vol-overlay.py gt6_vol_a32 gt6_vol_a32 gt6_vol_a35, then tools/patch_adc_colorbegin.py (line 277 reads -> INT_CONST 0 + NOP).
- Runs: a35cb (2) AdjustScreenRoot loaded both; frame 6000 dialog with OK button (glyphs clipped). a35pad (230 s): AdjustScreen frame, German text.
- a35pad2 (2): both AV at 85 s writing shared PDIPFS/K/CQ.fdup* (crash handler log_host_fault faulted too, no host trace).
- a35pad3 (2): one run X@220 s -> AutoSave2/AutoSave GAME6 -> SAVE complete, then black frame 15000, no further opens.
- a35wd (2, PS3_WD_AT=262,285): run1 heap deadlock tid1/tid30 (locks 17B4BD8/17B4C08); run2 STALLED@156 s.
- B0921C(time): stores time at 17B4C70; B1A0F4 (lock all heaps) only if delta < 100000 us. B04CD8 locks BD8, walks heaps +0x44, B04CB0(heap)->B08728.

## Arbeit36 (2026-11-25) allocation failure source, heap lock guard, setting-project stall
- a36oom (2, PS3_WD_AT=240,285): run1 STALLED@73s (read fault 0xFFFF0000 after PDIPFS/K/SD, HOTREAD lr=6D2C6C); run2 SettingProject stall. 0 OOM.
- Static: heap AB-BA = B04CD8 (lock 17B4BD8, per heap 17B4C08 via B08728) vs operator-new failure path B0CCAC->B08498 (holds C08)->B0921C->B04CD8.
  tools/guard_heaplock.py: B04CD8 takes C08 first (1 ms timeout, else skip, [A36HL]). Runs a36hl/a36pm: no regression seen, guard never contended.
- a36hl_2: [A35OOM] 40x caller=00AE74D0 heap=017B4C78 r4=0x10 r5=099F6844. B0C524(heap,align,size): align 16, size ~161 MB. AE73BC is the retry-until-success
  operator new loop (entries AE752C/AE7540/AE7554). Then AV guest_fn 00B5E450 on tid3 at flips 163. Hook now prints tid + 8 return addresses.
- SettingProject stall (a36oom_2 WD): tid1 chain A2FFCC..68FF84->66E6AC->A86118->A2F290..->A0498C->88F2B4 (wait while status==-1, 1 ms), both samples.
  After tid31 task post (A27T lr=01062478) tid1 (not tid30) took the next task in most stalled runs; good runs mostly tid30 (correlation only).
- a36pm (2, PPU_PRIO_MAP=1): both reach 300 s at ~52 fps, no AdjustScreenRoot (one with tid30 taking the task: polls forever). PRIO_MAP does not fix it.
- a36ch (2, no WD): run1 silent stall at SettingProject (0 OOM). run2: [A35OOM] 12x tid30 heap=017B4C78 align=0x10 size=0xC chain AE74D0 AD3F30 AD42D0
  6166C0 7B5248 892C20 8933A4 892988 (6166A4: AD4294(obj+0x2B0) = small node alloc); [A36HL] skipped 7 walks (tid1 and tid30), flips continue to 300 s.
  So the main heap is exhausted or its free list is corrupt: even 12 bytes fail. a36hl_2 asked 161 MB (garbage size).
- Heap query wrappers on 017B4C78 (candidates for free-size logging): B0A3B4 (caller 9FE274), B0A6AC (9FE1EC, 9FE2E4); B0BC70 many callers.

## Arbeit37 (2026-11-25) shared savedata found, post-save
- Shared ./gamedata/dev_hdd0 savedata (written 11:32 by probe_a35pad3_..112834_2) was loaded by all 14 later runs: no AdjustScreen.
  probe.ps1 now sets PS3_GAMEDATA_ROOT=<rundir>/gamedata (-SaveSrc seeds it). Old save: work/ARCHIV/savedata_a35pad3_20261125_1132.
- a37sv (2 runs, fresh save, frame-6000 early kill at ~178 s): both AdjustScreenRoot at some point (monitor). Run 2: AutoSave2 +
  SAVE complete with NO pad press (script keys start at 180 s), then flips continue, no LoadModule/new screen, capture black.
- a37sv run 1: stays at SettingProjectComponent (legal screen at frame 6000); 12x [A35OOM] tid30 heap 017B4C78 align 0x10 size 0xC
  right after the SettingProject load (chain AE74D0 AD3F30 AD42D0 6166C0 7B5248 892C20).
- a37ps (2, WD 270,310, frame 13500): run1 STALLED@95s after AdjustScreenRoot with 12x A35OOM; run2 SAVE complete, no loads after icon
  files (last: credit images, tutorial.xml, GameParameterUtilImpl.adc before save), X at 200-240 s ignored, black frame; ended before WD.
- a37wd (2, WD 225,240): run1 (stall, 5 OOM) tid30 AE73BC<AD3DFC+0x134<AD4294<6166A4<7B51B8<892BF8; tid1 AE27AC<AE2844<6171D0<7A0A54.
  run2 (saved) tid30 AD4294+0x78/+0xB0<1FA968<7B51B8; tid1 same 6171D0 wait; tid31 AE27AC<106264C<AF0B94.
- AD4294: if AEFEC4()==0: AD3DFC copies list to temp (12-byte nodes via AE7554), vcall+0x14 per item, frees nodes (B0BC70).


## Arbeit38 (2026-11-25) heap-exhausting list notify: cause = corrupted listener list, suspect SPU 16 KB DMA
- Hooks (env GT6_A38LIST, gen 023 AD3DFC/AD4390; backups work/_bk_a38, orig + hook1..3 scripts): list *(this+0x2B0) holds 1 listener.
  Bad runs: first->next = 0 or garbage -> copy loop AD3DFC never reaches the sentinel -> endless 12-byte allocs -> [A35OOM]. Confirmed.
- Node/sentinel at 6FFFE930..6FFFE96F are overwritten by foreign data: 32 B "7C00../7E00.." (call 1), or pixel-like 0x10..0x13 bytes plus
  [A34G] AE6388 skip + NULL+0x18 write (after 262k good calls). Same region as the Arbeit34 vector 6FFFE9xx.
- SPU_DMA_RANGE=6FFFE920-6FFFE980: SPURS job DMAs ea=6FFFE8F0 size=16384 (GET cmd 0x40 and PUT cmd 0x20, ~200/s, 3.2 MB/s).
- PPU_WVAL=0x6FFFE8F0: pointer returned by allocator CC52B8 (call at CB3BB4 in CB3320, tid1), stored obj+0x84 (017E9854), per frame copied by
  CB931C to 600A82D4 (job descriptor area 600A8280). Requested size = align16(CB0768(obj80,r26,0,0x104) result) * *(obj+0x20) + 0x10.
  Neighbours 6FFFE900/920/930 are live objects, so the block looks far smaller than 16 KB (size not yet logged).
- a38list/a38ww/a38du/a38sp: bad in about 1 of 6-10 runs; good run a38list_1 reached SAVE complete and stayed black (frame 13500).
- Not SPU-audio-port: runtime port buffers are at VM_AUDIO_BASE 0x58000000.

## Arbeit39 (2026-11-25) list corruption root cause and fix
- a39sz: CB3BB4 alloc size = align16(attr102(socisynth))*groups+0x10 = 0x10 (attr102=0) -> block 6FFFE8F0; SPU job GET/PUT 16 KB there (read-modify-write over live heap).
- a39ev/a39rx: attributes are returned in data3 of the SPU's own event (src FFFFFFFF53505501); cellSpurs.c jc_signal_done added a second data3=0 event per job. Values 0 / 0x400 depended on arrival order.
- Fix (runtime): chain whose job self-reports gets no synthetic completion (GT6_JC_SYNTH=1 restores). a39fix 2/2: attr102=14860 attr104=B4D0, socedmix 8A20/2000, buffers 600B4000/600CA000.
- Hooks: GT6_A39SZ (gen 028 CB3BB4/CB3CF0/receive, backup work/_bk_a39), GT6_A39EV (cellSpurs.c).

- (Arbeit39 cont.) a39f/g/h/s (2 runs each): pad X 220..395 s -> AdjustScreen -> voucher dialog -> AutoSave2 -> SAVE complete; black afterwards,
  flips continue (a39h 11016/6685 after save). RSX_CAP=start:count:stride used for frames. probe.ps1 caps -Parallel at 2.
- snap_walk bt (snapshots work/snap_a39black_{1,2}): tid1 7A0AC0>617218 (MGOM.start wait), MGOM obj 6FF36000 state 3, 616C80 ticking on tid30.
  A27T task 403D1910 ret=2 until 397 s, state 3 after save; no 737C60 polls afterwards; A29 throw hooks silent.
- LoadModule PAMF/DMUX logged right before SAVE (a39s_1 run.log 54827/54828); no cellPamf/Vdec call and no .pam open logged afterwards.
- boot.adc flow via tools/adch_disasm.py (needs python -X utf8): boot_sequence_gt6.ad lines 46-93, MovieRoot.ad play_movie lines 82-108.

## Arbeit40 (2026-11-25) post-save black screen = intro tutorial race
- a40skip (2, overlay work/gt6_vol_a40, tools/patch_adc_skipopening.py): MovieRoot skipped, still black after SAVE. Movie is not the blocker.
- Script trace GT6_A40VM=<sec> (tools/a40_vm_hook.inc, gen 023 AA41FC dispatch: ctx r10=record, r8=task, handler table 0x15DA1F8, byte0=ADCH opcode,
  low 24 bits=line; backup work/_bk_a40; current binary carries it). Matcher scripts/adc_trace_match.py. Runs probe_a40vm_20261125_141405_{1,2}.
- Trace: voucher dialog open 247 s..398 s; then display_sequence ends, start_project_gt6 runs lines 108-117 at 398.4-398.8 s: ReadFile
  tutorial.xml, create_player, GameParameterUtil.executeEvent (intro tutorial race). Race code saves (SaveDataUtil _save ->
  createSaveDataEveryWhere), last script record 399.679 s, then no script instruction at all. "SAVE complete" is that save.
- a40tut (2, overlay work/gt6_vol_a40t, tools/patch_adc_skiptutorial.py, ins 28 -> JUMP_IF_TRUE 84): NO black screen. Present/credit dialogs
  render (German, 1.000.000 / 100.000 credits), then GT logo loading screen to 460 s (probe_a40tut_20261125_142341_{1,2}, sheet.png).
  Script errors on tid1 in GTModeRoot: "nil object cannot be used in '(nil).toInt'" ([A29E] line=48, GTModeRoot::GroupData, near
  SELECT ModelName, Logo, Name ... query).


## STATE trim 2026-11-25
- (Arbeit32) Fixes: /STACK:64M; purecall guard (C68B8C logs, returns 0); stale 11-22 savedata moved to ARCHIV (caused DISKFULL).
- (Arbeit33) Boot race solved by pinning guest PPU threads to 1 host core (PPU_ONECORE=1): 6/6 reach PresentsRootSCEE.
- (Arbeit34) 0xC00000FD = fflush(NULL) symptom; root: AE6388 (from CD2ABC, vector 6FFFE910 with 2 NULL entries) wipes NULL page..TOC.
- (Arbeit35) AE6388 guard persisted (tools/guard_ringzero.py in post-lift). ColorBegin bypass: tools/patch_adc_colorbegin.py, overlay work/gt6_vol_a35.
- (Arbeit35) MILESTONE (probe_a35pad_..112132_2, pad3_..112834_2): AdjustScreen renders (German); X at 220 s -> AutoSave2 -> SAVE complete.

## Arbeit41 (2026-11-25) truncated files: guest sizes came from the 1.00 volume TOC
- (nil).toInt site: gtmode.adc getGTModeFirstCarPP l376 (SELECT PP FROM GENERIC_CAR WHERE ID=?) returned nil.
- GT6_PFS_TRACE=1 (probe_a41db_20261125_143428_1): DB0106.dat read n=16041984 of 16602112; also rtext/common/DE.rt2 383244/580744,
  CarName 97984/103008, fonts, sound lib. SPECDB truncated explains this and the older (nil).ColorBegin.
- Size source: guest stat 0xAADA6C (host open 0xAB080C, FileObject+0xB8 struct, size +0x10, filled from guest TOC).
  Fix eb71225: wrapper + gt6_pfs_stat_fix reports overlay size (probe_a41fix_20261125_144112_1: boot.adc, dialog.adc, setting.adc,
  ui_kit.adc, DE.rt2, DB0106.dat sizes corrected; DB read now 16602112). CarName.dat still read with 97984 (other size path, open).


## STATE trim 2026-11-25
- (Arbeit35) Shared PDIPFS junction: parallel runs both wrote K/CQ.fdup* -> 2x AV at 85 s. probe.ps1 now copies PDIPFS per run (CQ moved to ARCHIV).
- (Arbeit35) After SAVE complete: black frame, no further opens/loads for 60 s (frame 15000, 1 draw op). Oracle opens PDIPFS/59/FI (film) here.

## Arbeit42 (2026-11-25) SPECDB reaches SQLite undecrypted
- probe_a42full: toInt 16x, still gtmode.adc getGTModeFirstCarPP l376; 17 frames captured after probe.ps1 fix.
- probe_a42sql (GT6_A42SQL=1, env-gated hooks in gen 026, bk work/_bk_a42, binary carries them): all SPECDB prepares rc=26, step rc=21.
- probe_a42pg2: page1 at 0xBE9C10 for DB0106/menudb = raw file header 0E 94 7D BF.
- probe_a42dev: host-file device vt 0x15DB8E8, read 0xAAF694 (filter stream+0x48 vtbl+0x10, else raw vtbl+0x9C = 0xABE5A4).
- REFUTED: deferring to the +0x48 filter: all filtered streams -> boot stalls at fonts (a42dec); DB only (a42dec3): DB0106 has no filter.
  Patch kept in work/ARCHIV/a42_filter_patch (not applied). Size write at FileObject+0xC8 irrelevant (0 at open).


## STATE trim 2026-11-25
- (Arbeit35) New (a35wd run1, PS3_WD_AT): heap AB-BA deadlock at ~200 s, AdjustScreen never loads. tid1 operator new B0CCAC: alloc B0C524
- (Arbeit35) a35wd run2: flip stall at 156 s, purecall storm lr=2CD5F4 + linear read faults 0x100x0000 upward (runaway walk).

## Arbeit43 (2026-11-25) SPECDB key path
- probe_a43bt (GT6_A43BT=1): full DB0106 read comes from the p4 cache-fill hook inside xOpen C1FE74 (lr C20374), after AE6C34.
- probe_a43nocf (GT6_NO_CACHEFILL=1): page1 all zeros (VMPageFile pager B07748 relies on page faults), 70x rc=26. Hook stays needed.
- Static: 9ED798 bc8e6c stores key {1,str,len} -> xOpen -> 109DC08 -> AAA738 -> AAC2A8: FileObject+0x90..0x98, ptr at +0x9C.
  Position keystream identical in DB0105/DB0106 (first bytes 0E947DBF). Reader of +0x9C at AAF74C. Not yet decrypted.


## STATE trim 2026-11-25
- (Arbeit35) a35oom (2 runs, hook [A35OOM] in gen 024 B0CCAC, bk work/_bk_a35, binary carries it): 0 OOM, both stop at
- (Arbeit36) OOM cause seen (a36hl_2): operator new retry loop AE73BC (callers via AE752C/40/54) asks ~161 MB (size 099F6844 =
- (Arbeit37) "AdjustScreen 0/14" was no code regression: pad run pad3_2 saved to shared ./gamedata (11:32); later boots had a save.

## Arbeit44 (2026-11-25) keyed database decrypt
- AAF74C is a vtable slot call, not a reader of FileObject+0x9C. Device vtable 015DB8E8: open ABED90, read ABE5A4,
  vt+D4 ABCFA0 (cipher setup, ctx = [file+0x60], +4 key), vt+D8 ABD3D0 (volume XOR, then AC874C(key,state,buf,n,off,filt)).
- GT6_A44GUEST experiment: guest path decrypts but reads the 1.00 volume (K/RE). Fix: run AC874C on host bytes.
- a44key: DB0106 page 1 ok, queries succeed on other handles; a44dump: both dumps integrity_check ok.
- a44ver2: buffer 81AE0000 unchanged 120 s; a44xr6: no xRead with off != 0 and no xRead error on DB0106, yet rc=11.


## STATE trim 2026-11-25
- (Arbeit37) a37wd (WD 225/240): tid30 sits in list notify AD4294 (called 6166A4, list obj+0x2B0; also A7F074). Stalled run: inside
- (Arbeit38/39) FIXED: heap corruption/OOM. HLE job chain added a data3=0 completion beside the SPU job's reply; sgx sizes came back

## Arbeit45 (2026-11-25) database sizes, GT Mode load
- a45sz: xFileSize C1F848 (-> C1F65C -> AAAD1C -> vt+B8 ABD328) returned 16041984 for DB0106 (served 16602112). Fix f8ef048.
- a45fix2: no rc=11, no toInt. grim007: xOpen buf=1 (null-read in C5A510) from hook part4 clobbering cr; fix b219eca.
- a45full: after credit dialogs opening movie tv_10006 .pam -> black. a45op (gt6_vol_a45): GT Mode loading, rc=26 gone.
- a45gm/a45snap: 31k flips headless, gtmode.adc/gtmode_pack/mproject reloaded 38x; snap work/snap_a45gm_540: tid1 in 617218.
- a45vm (GT6_A40VM=400): cycle 494411-494788 ms runs GTModeRoot/GTTopRoot/TopNews/CarDealerRoot, ends at l376 after SELECT PP.


## STATE trim 2026-11-25
- (Arbeit39) WITH FIX 4/4 (a39g/h, pad X every 25 s 220..395): language select -> AdjustScreen -> dialog -> AutoSave2 -> SAVE complete.
- (Arbeit39) After save: black 4/4 for 100-190 s. a39s snapshots work/snap_a39black_{1,2}: tid1 in MGOM.start wait (6171D0, obj 6FF36000),
- (Arbeit39) Static boot flow (boot_sequence_gt6.ad in boot.adc): AdjustScreen -> applySaveData -> voucher dialog -> BackupSave ->
- (Arbeit40) Post-save black = intro tutorial race (start_project_gt6 -> executeEvent), VM stops at 399.7 s after its save; movie skip no help.
- (Arbeit40) MILESTONE: overlay work/gt6_vol_a40t (tools/patch_adc_skiptutorial.py) 2/2: credit dialogs, then GT Mode loading screen (GT logo)
- (Arbeit41) FIXED eb71225: guest stat took sizes from the 1.00 TOC -> overlay files truncated (SPECDB, adc, DE.rt2). Run a41full: 26298 flips


## Arbeit46 (2026-11-25) GT Mode reload loop
- a46err: failing car queries have Vdbe rc=11 "database disk image is malformed"; a46buf: cached DB buffer unchanged (0 diff pages).
- a46c/a46f: corrupt from lockBtree BE9B40 (hdr pages 16213, pager dbSize 15666); xFileSize alternated 16602112 / 16041984.
- Cause: gt6_pfs_fstat_fix needed the PFS slot (16 slots LRU). Fix faa32e5: size table per FileObject.
- a46fix: no corrupt, gtmode files loaded once; exit 0xC00000FD at 538 s (fiber host stack 4 MB, xRead under SQLite step).
- a46stk: stack fix, no crash in 560 s, GT Mode home visible. a46menu (no X after 395): home menu "Zuhause" captured.


## STATE trim 2026-11-25
- (Arbeit42) ROOT of (nil).toInt: SPECDB (specdb/GT6/DB0106.dat) prepare returns SQLite rc=26 NOTADB; page 1 handed to SQLite is the
- (Arbeit43) DB key found: script open passes key string; aac2a8 stores {1,str,len} at FileObject+0x90, ptr +0x9C. Host open override
- (Arbeit44) FIXED keyed open: host bytes now pass guest key layer 0xAC874C (Salsa20, state [FileObject+0x60]+0x1C;


## STATE trim 2026-11-25
- (Arbeit45) FIXED f8ef048: xFileSize C1F848 -> stream stat ABD328 gave 1.00 TOC size (16041984 vs 16602112); hook
- (Arbeit45) FIXED b219eca: port cache-fill hook clobbered cr7 -> grim007.db buffer freed, ptr=1 -> rc=26. Gone.
- (Arbeit45) Overlay work/gt6_vol_a45 (a40t + skipopening): readable credit dialogs -> GT Mode loading. Opening .pam (535 MB)
- (Arbeit45) Debug prints [A2x] in gen 013/014/015/022 gated by GT6_A27 (backup work/_bk_a45/a27); GT6_PFS_TRACE slows load.
- (Arbeit46) FIXED faa32e5: GT Mode reload loop = car DB SQLITE_CORRUPT in lockBtree (dbSize 15666 < header 16213):


## Arbeit47 (2026-11-25) M1 inventory, T1 raw message ID
- GT003_GET_FIRST_CAR0: scripts/gt6/main.adc TutorialUtil.message -> main::manager.translate("Tutorial", key).
- 1.22 rtext/common/DE.rt2 (RT05, 177 categories) has "Tutorial" (292 entries) at 0x7F3C4; 1.00 file (RT04) is 383244 bytes.
- a47rt/a47rt2: read request n=383244 pos 0/580744. First open of DE.rt2 gets [statfix] 383244->580744; the second does not.
- a47rt3/a47rt6/a47rt7: second FileObject+0xCC = 383244 at read, 0 at host_open_commit; stat out struct holds no old size.
- a47fix2-4: wrapper on info getter AAC240 (forces size words +0x10/+0x18) never called before the read -> not the path.
- Static: AAE57C 'std r27,0xc8(file)' (r27 = arg r4 of AAE51C, caller A01A4C); AAAB40 'std r3,0xc8(r30)' after read call.
- A01A1C..A01A4C: size = virtual(obj vt+0x48), passed to AAE51C. a47size: wrapper on AAE51C (work/_a47/opensize_hook.patch)
  printed nothing before the stop: either never called or r3 is not a C string. Reverted.

## STATE trim Arbeit47
  fails -> B08498 holds lock 17B4C08 -> B0921C -> B1A0F4/B04CD8 wants 17B4BD8; tid30 per-frame AE73BC -> B04CD8 holds BD8, wants C08.
  SettingProjectComponent.gpb, ~37 fps (older mode, Arbeit33). OOM cause still unmeasured. Repeat batch until the deadlock hits.

  garbage; B0C524 args are align,size) -> endless retry. Hook now prints call chain. Deadlock guard tools/guard_heaplock.py (post-lift).
  Fix: probe.ps1 sets PS3_GAMEDATA_ROOT per run (-SaveSrc seeds it); that save is in work/ARCHIV/savedata_a35pad3_20261125_1132. Verified a37sv + a37ps: 4/4 AdjustScreen.

  copy AD3DFC -> new AE73BC (alloc retry); saved run: AD4294 walk/free, tid1 waits 6171D0 -> AE27AC. Saved+black: no loads, X no effect.

  0/shifted -> 16-byte buffer, SPU 16 KB DMA over heap. patches/gt6-a39-jobchain-selfreport.patch (0498bee), a39fix 2/2 sizes stable.

## Arbeit48 (2026-11-25) truncated reads fixed, pad focus gate
- Cause: stream read job AAB258 clamps length to FileObject+0xC8 (u64, 1.00 TOC size) at AAB280. Fix d4e1f9a:
  gt6_pfs_size_fix before the load (port_hooks.py part5). a48rtv trace: DE.rt2 383244 -> 580744, hostov n=580744.
- Overlay files now mapped (no 64 MB cap), 512 slots (evicted stream fell back to the 1.00 volume).
- a48menu2 (560 s): home menu loads all piece/gt6/home/*.img (never loaded before), tutorial dialog gpb, attract demo
  d024/d015, ends on GT loading screen (course c052). User pressed physical pad buttons during a run.
- a48menu and a48menu3: "[spu-dma] img=5 pc=0x07C44: 256 identical transfers to ea=0x03000530 -- halting the SPU"
  (STALLED @214 s / @335 s; 2 of 3 runs). Guard fires after SPU_DMA_REPEAT_SECS=30 s of polling; flips stop with it.
- cellPad XInput: inactive window reads neutral pad (patches/gt6-a48-pad-focus.patch, PAD_BACKGROUND=1 off).

## Arbeit49 (2026-11-26) SPU stall and shredded text
- S1 cause: halted runs (a48menu, a48menu3) = the only 2 of 19 runs with "[cellGcmSys] FIFO resync (jump-park)".
  Walker waited 50 ms on a self-JUMP park, skipped to put; label 0x53 (ea 0x03000530) that SPU img 5 polls was
  not released. Fix: gt6 main.cpp defaults GCM_PARK_GRACE_MS=5000. a49park (env, 2x 402 s): 0 resync, 0 halt.
- T2: static dialog, 3 guest buffers; vertex hashes equal on consecutive frames (RSX_CAP_VHASH=1), 1 of 3 clean.
  Correlation 10/10: clean = DS-as-texture 0x01500000 declared 1536x1408, shredded = declared 1440x1080 while the
  host copy stays 1536x1408 (UV scale 1/declared). GCM_SEMA_ACQUIRE=1 no effect (a49sema).
  Fix: rsx_d3d12_backend.c RT pre-pass scales unnormalized DS-copy units by host size
  (patches/gt6-a49-ds-texscale.patch).
- a49menu (2x 540 s, default park grace, same pad): GT Mode home at flip ~23000 both runs, 0 resync/halt; popup real
  text (T1). Frame work/_a49/menu_home_a49.png: only dealer tile lit, three stacked notification banners.

## Arbeit50 (2026-11-26) pad in menu, movie path
- a50pad (2x 720 s, X 560/580/600, right/left, X 650, circle 685): popups advance with X, X on dealer tile starts the
  dealer loading screen; loading still shown at 720 s (~100 s+). Frames work/_a50/sheet_pad*.png.
- cellPamf HLE read a wrong header layout (0 streams); rewritten (patches/gt6-a50-pamf-header.patch).
- cellDmux v020 is a stub (no PES parsing); cellVdec needs PS3RECOMP_FFMPEG_RUNTIME + FFmpeg headers.
