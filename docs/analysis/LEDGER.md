# GT6PP LEDGER - durable facts (supervisor, 2026-11-23). Only add/correct, never start over.
Purpose: session changes without loss. STATE.md = current step, LEDGER = what is secured. Every line with evidence. Lines <=200 chars.
Only line: game v1.22 + ps3recomp v0.20.0.

## 1. Canon (build/runtime)
- Build: `scripts\build-all.ps1` (decrypt check -> function list -> PPU lift -> post-lift -> clang-cl/Ninja). Result `gt6\build\gt6.exe`. No version switch, no GT6_V122.
- Runtime: `third_party/ps3recomp-v020` (v0.20.0). Lift: `gt6/generated` (EMAIN 1.22, 74935 fn, 41 chunks). SPU: `gt6/src/gen` (16 job images, PM id5, 1 embedded ELF).
- Evidence 2026-11-23: build-all full build ~8 min (16 cores), incremental (stubs.cpp) 4 s; probe smoke: boot.txt exe=gt6\build\gt6.exe, unresolved=0.
- Guest: `work/bin/EMAIN.elf` (1.22, sha256 in scripts/inputs.json, NPDRM-decrypted: `tools/self_decrypt_np.py`, key 9ff234b1..4724 from RPCS3 log line 3478, gt6/data/keys not in repo).
- Oracle RPCS3 (user, same EU disc, game 1.22): log `...\v1.2_beta4_GT6-Launcher-win64\data\rpcs3\log\RPCS3.log` (copy in work/oracle/), data `...\dev_hdd0\game\BCES01893\USRDIR` READ ONLY.
- Port details/table: `docs/analysis/PORT.md`. Address mapping old->new: `tools/map_funcs.py`.
## 2. Open ports (1.22 has no guest hooks yet)
- Missing: script hooks (candidates A67E1C/A67F60/A67DC4 uncertain), boot presents, menu pump, FileDeviceHost flush, (ADCH done via lifter entries), PFS cache fill, ZWAP, boot.adc gates. Frame 4200 black without them. Order: boot-critical first, anchors by byte pattern.
- Runtime fixes apply version-independently (ps3recomp-v020): generation-keyed lwcond, host-font sync, FileDevice flush guard, sys_timer one-shot, sys_mempool, cellMusic, cellFiber WaitFlag parking, SPURS job walker.
## 3. Secured 1.22
- SPU: 16 of 20 known job fps found, WWS PM byte-identical (0 dispatch MISS). memset duff + 6-way switch A2F158 manual entries (tools/add_computed_entries.py).
- Spinner stall on 1.22: 37 threads parked (pc 0xB03BAC lwcond wrapper), no spin, 30 PDIPFS opens, no PDIPFS/59/FI.
- SELF decrypt: EMAIN 1.22 = NPDRM (self_type 8, license 3); rpcs3 --decrypt alone fails.
- Hooks Stream/FileDevice/Host-Open on 1.22 (fuzzy map, match 0.84-0.97) alone: frame 4200 black, no PDIPFS/59 (probe hk122, 2026-11-23).
- 1.22 data via GT6_VOL_ROOT overlay (scripts/make-vol-overlay.py) boots to legal/"SCE presents"; needs /STACK:64M. __cxa_pure_virtual = 0xC68B8C (OPD 0x163C3E0, guarded in main.cpp). Evidence: probe_a32see_20261125_095738_1.

- Probe saves are per run (PS3_GAMEDATA_ROOT, 5c85812); a shared ./gamedata save hides AdjustScreen. Evidence: probe_a37sv_20261125_121629_*.
- (Arbeit38) A35OOM list notify: listener list at 6FFFE9xx corrupted; SPU job 16 KB DMA at ea 6FFFE8F0 overlaps it (SPU_DMA_RANGE, PPU_WVAL=0x6FFFE8F0). Evidence: eu-boot-log Arbeit38.
- (A39) Heap corruption/OOM ROOT CAUSE: HLE job chain pushed a synthetic data3=0 event besides the SPU job's own reply (soc-job, queue 4) -> sgx module sizes 0/shifted -> 16-byte buffer, SPU 16 KB DMA over heap. Fix patches/gt6-a39-jobchain-selfreport.patch; socisynth attr102=0x14860 (a39fix 2/2).
- (A39) With the job chain fix the first-boot flow completes 4/4+: AdjustScreen -> voucher dialog -> SAVE complete (a39g/h, X every 25 s 220..395).
- (A41) Guest file sizes come from the 1.00 GT.VOL TOC: overlay files were truncated (SPECDB 16041984/16602112, adc, DE.rt2) -> nil queries, '(nil).toInt'. Fix eb71225 (stat 0xAADA6C wrapper). CarName.dat still short.
- (A42) SPECDB is SQLite (prepare 0xC063D4, step 0xC065F4, magic check fail label 0xBE9C10); DB0106/menudb reach SQLite still encrypted -> rc=26 -> nil queries. Evidence probe_a42sql, a42pg2.
- (A43) SQLite DBs are opened with a script-supplied key: FileObject+0x9C (AAC2A8); host open override ignores it, so DB bytes stay encrypted. Evidence probe_a43bt/a43nocf, gdis AAA738/AAC2A8.
- Stream read job AAB258 clamps to FileObject+0xC8 (1.00 TOC size); fixed d4e1f9a (port_hooks part5), evidence a48rtv trace.
- (A49) SPU img 5 halt on ea 0x03000530 (label 0x53) = jump-park FIFO resync; GCM_PARK_GRACE_MS=5000. Evidence: probe_a49park/a49fix.
- (A49) Shredded text = depth surface read as texture scaled by declared size, not host copy size. Evidence: probe_a49vh/a49fix.
- (A50) Pad works in GT Mode home (popups, dealer enter): probe_a50pad_*. PAMF stream headers start at 0x88, 0x30 each (patch gt6-a50-pamf-header).
- A53: car detail stall = [FIFODUMP] self-JUMP park io 0x146A08C -> jump-park resync -> SPU img 5 halts after 30 s polling ea 0x03000530 (play_a53c_20261126_033359 run.log.err 2842..2874).
- (A54) Label 0x53 handshake: RSX ACQUIRE 0 at segment start, RELEASE 1 at end; SPU img 5 (job code LS 0x5930) waits 1, writes 0. Walker ignored ACQUIRE -> lost release -> SPU halt. Evidence: play_a54pt2_20261126_041937, work/_a54/spu_halt_ls.bin.
- (A54) PPU wait emitter C3217C: [0x40040100][JUMP][SEMA OFFSET/ACQUIRE]; C3216C writes 0x100 to cancel the wait. Evidence: gdis, [ww] 6146A08C.
- (A54) RSX user commands: one pending slot lost causes (GT6 cause 1 overwritten by 0, 60+ in play_a54ucmd); now a queue; a54ucq: 0 null calls.
- (A54) tid30 null object C4797C = cellGcmSetUserHandler cause 1 with *0x17E7DF4 == 0 (waiter C451F8 gave up after 5 s): symptom of slow/lost delivery.
- (A54) Car view black = D3D12 device removed 0x887A0006 (play_a54dbg run.log 17885); 0x887A0005 PSO fails already in a54fix.
- (A54) Car view device hung (0x887A0006) = upload buffer/target released while the open command list still used it; wait_for_gpu covers submitted work only. Fix d3d_retire, verified play_a54retire_20261126_052113.
- (A54) D3D12_DRED=1 names a hung GPU command (breadcrumbs, copy source VA, page-fault allocations); works without the debug layer.

- A55: car-view/delivery slowness = 56 WWS job modules in the ELF, DMA'd to LS 0x4000 by the PM (image 5), never lifted -> interpreter. Lifted (scripts/lift-spu-wwsjobs.py): FPS 0.9->4.8, delivery ends (play_a55lift_20261126_060612). Header: 4x ila $2, 0x30, text, data, bss.
- A55: SPU_DUMP_OVL=<dir>,0 maps every GET >=256 B to LS >=0x4000 (patches/gt6-a55-spu-ovl-map-dump.patch).
- A56: GT6 reads its exposure mip chain and post surfaces as sub-ranges of one linear RT; exact-address matching gave zeros. Fix patches/gt6-a56-rt-views.patch.
- A56: showroom 3D pass = surface 0x01F00000 1152x648 (car visible there), then NV3089 blit to main 0x602A0000 pitch 4608 (play_a56cap_20261126_064234); host RT is never read back.
- A57: NV3089 sources are local linear RTs (pitch 5120/8192); readback patches/gt6-a57-rt-readback.patch (NV3089_RB=0 off); play_a57cap_20261126_065731.
- A57: NV40 fragment programs use H registers above 47 (6-bit field); patches/gt6-a57-fp-regs64.patch; play_a57cap_20261126_070409.
- A57: NV0039 (subch 1) was unimplemented; GT6 issues small local->local copies near 0x04CE-0x04D1; patches/gt6-a57-nv0039.patch (NV0039_DBG); play_a57cap_20261126_070950.

## 4. Refuted/symptom (do NOT repeat)
- (A54) "A car-view draw/shader loop hangs the GPU": refuted, DRED shows the first copy of the list reading a freed buffer.
- (A56) "Sub-range RT reads alone make the showroom car visible": refuted, screen unchanged (work/_a56/car_views.png); exposure/LUT still 0.
- (A57) "RT readback for NV3089 (plus FP register fix) makes the showroom car visible": refuted, still black (work/_a57/car.png).
- (A57) "Dropped NV0039 copies leave the showroom black": refuted, copies run now, screen unchanged (work/_a57/car.png).
- Pad/dialog chain Hyp. 1-14; exit race Hyp. 83-117; fresh vs persistent db; PRIO_START/LOCKSTEP/RESV_OFF; fiber list/busy loop; snap diff 140 vs 175 s; PDIPFS data missing; RPCS3 --no-gui as oracle.
- Sysmodule load list and fresh savedata (PS3_GAMEDATA_ROOT): no divergence from the oracle.
- A53 REFUTED "dealer load hang" (A50-52): that screen was the attract demo (leavedemo.adc/LeaveDemoRoot loaded, 'Der Demofilm startet'), cross came too late. Dealer loads in ~7 s (live a53c, work/_a53/dealer_list.png).

- A53 REFUTED GCM_SEMA_ACQUIRE=1 as fix for the car-view stall: acquire on label 0xFE0 times out all the time (play_a53e).

## 5. Open core question
- RPCS3 opens `PDIPFS/59/FI` (movie, PDI thread 0x100003b, Pamf/Vdec) after PDIPFS/9/EE/3C; we open 85/H2, 8M/A9, 6W/RR, 75/M8, SG/LW, SC/IC, 8M/0K, 4J/0E and park in lwcond (loader 9qstY).
- Next offline diff: oracle callers (LR) of 59/FI, trigger of the movie decision after EE/3C, now on the 1.22 build against RPCS3 (same version). Port hooks first.
## 6. Work rules
- Before every hyp.: read LEDGER. New finding -> 1 line with evidence. Refuted -> section 4. Run log boot.txt must name `gt6\build\gt6.exe`.

- 1.22: menu pump 616C80 ported (86302b5); packages arcade/option/gtmode/garage/gtauto load, then guest quit (loop 0x146E8 ends when byte 0x1796DC8 != 0, no hooked store sets it; AFDFC0 = title-ID strcmp, not quit) OR null-call loop (AD3DFC copy, NULL element). Evidence: side-session befund_1.22_nullcall.md
- GT5P check (b): GT6 loads script main.adc ('[GT6] script override' in log) + 30 PDIPFS opens -> mount/script load run; GT5P cause P12 does not apply. (a) lwcond sender for loader 9qstY still open (one run with lwcond_signal counter needed).
- 1.22 quit: snap series 6-40 s shows flag 0x1796DC8 always 0; main at 6 s in init wait (task 0x7FFCEE90), from 8 s shutdown -> quit not via loop 146E8; savedata fileBuf (0x901A0000/0x931C0000) no overlap.
- 2026-11-23 version: work/bin/EMAIN.SELF 9209104 B = RPCS3-update EMAIN (1.22), lift is 1.22 (not disc base 8843160 B). Save prefix diff: RPCS3 GT6_1.N vs ours GT6.N (hdd0 old saves 22.11.; format %s.%d @F87934).
- 2026-11-24 Arbeit22: heap fix (512MB mmapper alignment) + GT6_PUMP_ITERS=0 + main blocked after MGOM.start => boot project renders 'SCE presents' (probe_a22cap_20261124_171454_1). Main-exit cause: root task legit finishes; oracle main blocks (unknown why).
- (Arbeit51) 1.22 AC75B0 = PFS pipeline reader THREAD entry (object 0177CE00, tid6), not a flush; old p3 guard killed it at boot -> dealer-load deadlock (LWM-LONG owner 41). Removed. Evidence a51thr/a51dump/a51fix.
- A51: jump tables with the base loaded before a branch into the loop (FE1CAC, 1000B30) were lifted as indirect calls (cases skipped); log sign "unresolved indirect call" to mid-function addresses (patches/gt6-a51-jt-loop-base.patch).

- A52: dealer load hang is not a blocked wait: tid30 keeps executing interpreter code (different lr per sample), no new [fs] opens for >250 s (play_a52c wd_00233..00533, snap_00539).
