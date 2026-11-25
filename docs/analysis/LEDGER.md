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

## 4. Refuted/symptom (do NOT repeat)
- Pad/dialog chain Hyp. 1-14; exit race Hyp. 83-117; fresh vs persistent db; PRIO_START/LOCKSTEP/RESV_OFF; fiber list/busy loop; snap diff 140 vs 175 s; PDIPFS data missing; RPCS3 --no-gui as oracle.
- Sysmodule load list and fresh savedata (PS3_GAMEDATA_ROOT): no divergence from the oracle.
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
