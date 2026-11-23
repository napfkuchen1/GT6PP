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

<!-- gekuerzt 2026-11-23: Mitte siehe ARCHIV/docs-analysis/eu-boot-log_full_2026-11-23.md -->

## 2026-11-22 - Hyp. 28 (Job-Liste am Cancel-Zweig)
[C28] in func_00987A28 @loc_00987E54 (Patch patches/gt6-h28-cancelzweig.patch). Alle Cancels: obj=r23=r25=r28 (40007A10/40007C90), obj+0x28=1, obj+0x30=0, g(0x15DE27C)=0, r22=obj+0x6c, begin(obj+0x70)==end(obj+0x74) -> Vektor leer, Kapazitaet begin+0x28 (Heap mit Alt-Strings). Wait-Schleife (0x987E34..0x987E50) wartet nur bei nicht-leerem Vektor. Naechster Schritt: Befueller des Vektors finden.

## 2026-11-22 - Baseline-Wechsel + Hyp. 29/30
boot.adc auf nodlg_noadjust (Kopie work/ARCHIV/boot.adc.nodlg_noadjust; vorheriger Vollpatch in work/ARCHIV/boot.adc.patched_full_*). 3 Laeufe 320 s: Tutorial-Rennen laedt (race.adc, race_tutorial, Template.gpb, nur sgb 0449), Frame 5000 GT-Logo-Ladebildschirm, keine Sound-Schleife; STACKSCAN-Hauptthread identisch zu Hyp. 24 -> gleiche Task-Wait-Ursache. Hyp. 29: 987A28 ruft vtable+0xdc des Executors (obj+0x34), der 1 Job in obj+0x70/74 pusht (v74=v70+4); Dispatch 98787C -> Poll 9EEA88 (Executor obj+0x68); Job-Ergebnis 0/1 nie 2, Vektor danach leer -> Cancel. Hyp. 30: Poll setzt o24=0 (Task-State 3) / 2 (State 2) / sonst fuehrt Job aus (ab 0x9EEB04). Patch: patches/gt6-h29-h30-joblog.patch.

## 2026-11-22 - Hyp. 31 (Job-Poll 9EEA88 pro Objekt)
[P31] vor/nach Handler-bctrl 0x9EEC3C in func_009EEA88 (Skript: patches/gt6-h31-polllog.py.txt, Python-Insert-Skript, kein Diff wegen CRLF). 2 Laeufe valid. Poll ist Script-VM: ip=[exec+0x1c] steigt +4/Opcode, Handler-Tabelle 0x1487660. Tasks 40007A10/40007C90/40007990 fuehren Opcodes aus (u.a. 0B,26,25,1D,32,33,0C,03,39,05,24,1C), o24 bleibt 5 -> VM laeuft normal. Einzige o24-Aenderung: Opcode 0x37 (Handler 9ED204, = Script-Return/Ende) setzt task+0x24 = 1 (bei 40007C90, ip 40295538/40295590/40387BF0). Ergebnis 1 statt 2 -> Done-Event nie, Cancel. 40007A10/40007990 erreichen im 60er-Limit kein 0x37.

## 2026-11-22 - Hyp. 32 (Opcode 0x37 Status-Wert)
Statisch: Handler 9ED204 (Script-Return): Skript-Instruktionen sind 8 Byte (w0=op<<24|operand, w1=Argument). Handler liest w1=[ip+4]; Werte 1..3 -> pop Ergebniswert vom VM-Stack in Promise task+0x20 (979290), dann task+0x24 = w1; sonst task+0x24 = w1 direkt. Dynamisch [P32] (patches/gt6-h32-op37log*.py.txt): op37 bei 40007990 hat immer w1=0 (80 Treffer, 2 Laeufe); bei 40007C90 war w1=1 (Hyp. 31). Jump-Tabelle 0x1419550 (Switch auf obj+0x24 in 98787C): 0->987914 (98604C Schritt, dann Schleife), 1->98792C (985FE0-Test + 98604C), 2,3->987A08 (RETURN Ergebnis = Done/Fail), 4,5->9878B8 (Poll wiederholen). Also: Return-Status 0/1 = "Schritt fertig, naechsten Job holen" (98604C), nur 2/3 beendet den Task. Der Task wartet auf weiteren Job/Schritt; Vektor (obj+0x70..0x74) wird nach dem einen Job leer -> Cancel.

## 2026-11-22 - Hyp. 33 (98604C / 985FE0 / Job-Stack)
Statisch: Vektor obj+0x70(begin)/0x74(end) ist ein **Stack von Job-Objekten** (4-Byte-Zeiger). 985FE0(obj) = peek: top=[end-4], ruft top.vtable+8 (Status). 98604C(obj) = pop: top.vtable+0xc und +4 aufrufen, end -= 4 (nur wenn >6 Bytes... Groessenpruefung). 9860D4-Wrapper: while status!=2 {pop; leer -> return 1}; status==2 -> pop + obj+0x68.vtable+0x18(arg) -> return 0 (Erfolg). Dynamisch [P33] (patches/gt6-h33-peeklog.py.txt, 2 Laeufe x 62 Treffer): top-Job hat immer vtable 0x14875B0 (enthaelt 0x9EEA88 = Poll an +0x14, d.h. Job-Objekt = VM/Executor-Klasse), vtable+8 -> 0x8A1BE8 = `li r3,0; blr` (Stub), Status immer 0, nie 2. Stack-Tiefen: 40007990 5 Eintraege, 40007A10/40007C90 1. Damit kann der Wrapper-Pfad nie Erfolg melden; Done muss ueber obj+0x24=2/3 (Script-Return-Opcode mit w1=2/3, oder anderer Handler) kommen.

## 2026-11-22 - Hyp. 34 (Handler die task+0x24 setzen)
Statischer Scan der Handler-Tabelle 0x1487660 (patches/gt6-h34-scan.py.txt): direkte Setter nur 0x37 (Return, o24=w1), 0x1F/0x28 (o24=3, Abbruch), 0x1B (o24=w1), 0x06/0x0F/0x2C/0x3E (o24=5 via 9F095C). Dynamisch [P34]/(patches/gt6-h34*-*.py.txt, 2 Laeufe): o24=2 WIRD erreicht (Opcode 0x37 mit w1=2, 21x bei 40007C90, 1x 40007C10, ip 403B22F0..403B2858) -> 2 ist Return aus verschachteltem Aufruf, nicht Task-Ende. Der dominante Zustand ist o24=4 durch Opcode 0x06 (Handler 9F0748, 251x 40007C90, ip 403A6628 allein 120x): 0x06 = Sub-Aufruf/Child-Job: submittet Child via Executor-vtable+0xdc (Args vom VM-Stack), Child-Future bei [sp+0x78]; ist child+0x24==1 -> setzt o24=5 (weiterlaufen), sonst bleibt o24=4 (Dispatch-Fall 4: Poll wiederholen, ip bleibt am Opcode, Child wird bei jedem Poll neu geprueft/submittet). Script haengt also in 0x06 an Child, dessen +0x24 nie 1 wird. Hauptmenue-Blocker = Child-Job (Ziel unbekannt).

## 2026-11-22 - Hyp. 35 (Child-Job bei Opcode 0x06)
[P35] in func_009F0748 (patches/gt6-h35*-submitlog.py.txt; Variante b filtert task 40007C90). Opcode 0x06 = **native Funktion aufrufen** ueber callee-Objekt (r3) mit callee.vtable+0xdc: Ziele 9B0918 (vt 01483EC8, Ergebnis sofort st=1 -> o24=5) und 9B89D8 (vt 01484968; Wrapper, delegiert an Objekt [callee+0x14] vtable+0x54, args r4=Result-Slot sp+0x78, r5=w1, r6=Argumente) sowie 9A0178 (vt 014851B0, st=1). Das Ergebnis-Objekt [sp+0x78] ist der Task selbst (child=40007C90); st=[task+0x24] nach dem Aufruf. **st=4 (pending, Poll wiederholen) tritt nur bei 9B89D8-Aufrufen auf** (callee 4037EC28, 4049AE20/AE80/AF28/AF10, 403AD8E0, ...), 9B0918-Aufrufe liefern st=1. Der in Hyp. 34 dominante Hang-ip 403A6628 lag ausserhalb des 120er-Logs (Cap zu fruh erschoepft). Ziel-Objekt [callee+0x14] und dessen vtable+0x54-Methode noch unbekannt.

## 2026-11-22 - Hyp. 36 (Snapshot-Werkzeug PS3_SNAP_AT)
Patch patches/gt6-snap-at.patch (ppu_loader.cpp Thread + runtime/diag/ps3_snapshot.c): nach N s alle committeten VM-Regionen (reg_<ea>.bin, regions.txt, ~1 GB), Thread-Regs/Stacks, Sync-Tabellen. Lauf snap2 (work/snap_run2, 200 s, notut) gueltig.
Befund: Threads 2-40 in lwcond_wait/Syscalls (130/141/107), Hauptthread in cellFiberPpuWaitFlag. Mutex: 10 aktiv, alle owner 0. Sem: 8 mit value=0 (max 1024), keine Waiter. evq5 (key 0x23A0 = cellAudio-Notify) cap4 count4 ohne Receiver (vermutl. Symptom, vgl. Hyp. 19/20).
Wrapper-Suche (find32 0x01484968): 111 Objekte, 110 mit vtable 0x1487348 -> Slot 0x54 = 0x9E5FC0: Bind-Trampolin, ruft 0x9880BC(*arg4, this+0x14, [this+0x14]+0x34 ...) -> [x+0xC].vtable+0x28. Zielfunktion noch offen.

## Hyp. 37 - Snapshot snap_run2 (200 s, notut): Script-Task und Ziel des Pending-Calls
- Poll 0x9EEA88 gehoert zu 12 Task-Knoten (vt 0x14875B0, Poll +0x14); State-Objekt (vt 0x14811E8) +0x24 Status, +0x28 Zustand. Aktiver Task 400DB544 (Parent 400C7F88), State 40007990 Status 5.
- Bytecode: task+0x1c = ip (Array von Record-Zeigern), Record byte0 = Opcode, Handlertabelle 0x1487660+24*opc+0x10. Letzter Record vor Yield: opc 0x06 (arg 0x9A), danach 0x36 (015DE7D8).
- Opcode 0x06 (0x9F0748): Stack task+0x20 (base[0], Top +0x1c) pop 2 -> Callee 4037A844 (vt 0x1483EC8, +0xdc=0x9B0918), Arg-Objekt 400E97F0 = String "gtmode".
- 0x9B0918 -> obj2 4009EFE8 (vt 0x1485B50) +0x54 = 0x9C625C -> +0x58 = 0x9C6184 -> Functor obj2+0x14 = OPD 014CD330 = 0x6C54DC = MGOM.start.
- Manager 7FF01FC4: +0x48 = 1 (pending), +0x50 = "gtmode" -> Request wird nie konsumiert. Siehe boot-presents-fix.md 2.3.

## Hyp. 38 (offline, snap_run2): warum Consumer nicht laeuft
- Hauptthread (tid 1) steht in menu_start_project: Stack 0x568CCC/6C54CC/6C558C, Wait-Kette A21D50 -> A21CBC -> A4305C (cond wait).
- Workers tid 28/35/43: lr=00A121F0 -> Rueckkehr aus A187CC (lwcond wait in Worker-Schleife 0xA12170). Tick-Hook sitzt bei loc_00A121AC (Schleifenanfang) und feuert nur nach Wakeup.
- Kein Thread mit 0x568658 auf dem Stack; Pump-Request-Hook (func_00568C94 Eintritt) ok, aber Tick wird nie getrieben.
- A21E04 (signal) -> A21D8C: ist Waiter-Flag +0x28 gesetzt -> A42FFC (signal), sonst +0x29=1 (pending). Pre-Signal bleibt erhalten.

## Hyp. 39 (probe_sync39_20261122_220806_1, notut, 220 s)
- Sync-Pump vor 568CC8: "boot" (state 1->3->4->done, `sync pump done state=0` L7829), danach "gtmode": project load gtmode.mproject, states 1,3,4,3,4...
- gtmode: `sync pump done state=4` (L29752) nach 4000 Iter; state_after=3 3729x, =4 3538x, flag4C=1 load4D=1 -> Sequenz wird getickt, wird nie fertig (+0x91).
- Patches: gt6/src/stubs.cpp gt6_menu_project_sync_pump; tools/apply_gt6_post_lift.py add_menu_sync_pump (backup work/_bk_h39/ppu_recomp_012.cpp).

## Hyp. 40 (snap_h40, PS3_SNAP_AT=100 im sync-pump-Build)
- Consumer 0x568658: state 3->4 CAS, tickt manager+0x1d4[0..2] via 5C406C, setzt state zurueck auf 3, solange +0x91==0; alle fertig -> state 5.
- 5C406C: pro Tick Handler[+0x88] aus Tabelle 145D0D4 (5C1B3C,5BD718,5A8218,5B80DC,5B97A0,5A5BB0), +0x88++; Ende wenn A13644()=1 (Byte 0x164AB90 unter Mutex 164AB50) -> +0x90=1 -> 5C3EC4.
- Snapshot: Objekte 7FF0B000/7FF0B800/7FEAC000: +0x88=0, +0x8C=5/5/A, +0x90/91=0; 0x164AB90=0.

## Hyp. 41 (2026-11-22): Fertig-Flag der Sequenz-Objekte
- Offline (snap_h40): einziger Setter von +0x90 im Sequenzcode = 5A3AC0 (Func 5A3AAC), Aufrufer: 5680FC (Consumer-Exit 0x56886C/0x5E6D78) und 5A7A10 (generischer weak-ref-Wrapper, von 5AB428 mit >20 Aufrufern). Kein Handler setzt es selbst.
- A13644 liest Byte 0x164AB90 = Objekt 164AB80 (vt 146FA48) +0x10 unter Mutex 0x164AB50. Getter vt+0x8 = 3C0E84 (lbz 0x10(r3)), Setter vt+0xC = C3FE14 (stb r4,0x10(r3)); keine direkten bl-Aufrufer -> nur indirekt.
- Probe probe_flag41_20261122_222528_1 (GT6_FORCE_LOADFLAG=1, Sync-Pump i==20 schreibt 0x164AB90=1): Pump-State -> 0, Boot laeuft weiter (cellMusicInitialize2, open game024.db). Danach NULL-Deref in A21D50/A21CBC (Rueckweg 568CC8, Waiter manager+0x18) -> exit-chain code=0xFFFFFFFF.
- Interferenz Worker-Hook vs Haupt-Pump: nicht separat gemessen (Hook feuert laut Hyp. 38 nie).

## Hyp. 42 (2026-11-22): Rueckweg nach Sync-Pump, Natur des Flags 0x164AB90
- A21D50 (bl bei 568CC8) nach Pump: r3=mgr+0x18 korrekt, aber nach A42DE8 (Lock) r29=0 -> A21CBC liest NULL+0x29. Lock/HLE (ppu_sysprx lwmutex, gcm_pump) klobbern r29 NICHT (Diagnose-Klammern probe_flag42d..i).
- Ursache: DRAIN_TRAMPOLINE nach dem Lock-Call fuehrt ein vom Sync-Pump hinterlassenes g_trampoline_fn aus (Cross-Fragment-Fallthrough aus func_00568658), das r3/r29 nullt.
- Fix: gt6_menu_project_tick drained g_trampoline_fn direkt nach func_00568658 (stubs.cpp). probe_flag42j: A21D50 after lock r29=7FEAC018, Boot laeuft weiter.
- Danach exit-chain code=-1 lr 7F9588 = func_007F9520 (ppu_recomp_018): wenn Byte +0x95E==0 und A13644()!=0 -> +0x95E=1, Zeit (A2F308) nach +0x960; spaeter (now-stamp > 0x97FDF) -> func_00F9A080(-1) = exit.
- Schluss: 0x164AB90 = Quit/Abbruch-Anforderung mit Grace-Timer, nicht "Projekt fertig". Die Sequenzobjekte beenden sich bei Quit; GT6_FORCE_LOADFLAG bleibt reines Diagnose-Werkzeug (erzeugt Shutdown).
- Echter Fertig-Setter fuer +0x91 weiter unbekannt -> Hyp. 43.

## Hyp. 43
5C3EC4 (Finalizer) setzt +0x91=1; Aufrufer: 5C406C (nur wenn +0x90 durch A13644/Quit) und Shutdown 5FBAF0. Schleife 568800 = Haupt-Game-Loop, endet nur bei Quit. Hang = kein Menue-Rendering im Tick, nicht fehlendes Done.

## Hyp. 44 (Game-Loop, Pump unbegrenzt)
- GT6_PUMP_ITERS=2000000: >15600 Iter, State 3/4, ~2193 Flips/320 s, frame_00 = Legal+Logo+Spinner (probe_pump44b). Kein Menue-Frame.
- Back-Trace Track-Opens (009F8E40, probe_bt44): 009F7204<-009F73D0<-009F7420<-009F79D8<-008C70C8/008C1540 (11/40); 009F418C<-009BB16C<-005F3FE8<-005FA4D0<-005FA730<-568784 (Consumer).
- Ursache Dauerschleife offen.

## Hyp. 45 (Teil)
- probe_bt44: 3754 soc-job Chains, 4062 GT.VOL-Opens, 5213 IsLoaded(NPN); Snapshot: Main-Thread lr=568CB4 (im Sync-Pump), Objekte 7FEAC000/7FF0B000/7FF0B800 +0x88=0. Einmal job 3 rc=-1. Ursache offen.

## Archiv aus STATE.md (Hyp. 109-116, verschoben 2026-11-23 Ueberwacher)
- Hyp. 109-111: statische Kette Wipe: 7D083C (Wrapper, Singleton 0x159FD890) > 7CD628 > 88B878 > bl A25C64 (je 1 Aufrufer, 7D083C ohne direkten). CALLTRACE_TO auf 7D083C/7CD628/88B878/88B8E0: 0 Treffer (Exit-Laeufe h110 4/4 mit CALLTRACE=200, 88B8E0 ist ein bl-Site).
- Hyp. 112: GSTACK im Exit-Lauf (run.log.err, h110): Worker tid32 "9qstY" (A304D0>7FB1F0>7FB090>7DF57C>7DFF44>7DF7DC>802004>1AE7CC>1AE5E4>1AE074>1AAC8C>7D083C>7CD628>88B878>A25C64). Unfiltered Calltrace: kein Exit (Heisenbug).
- 1AAC8C = Cleanup-Task (Obj+0x1F30: 7D0904,7D0DE8,7D0FC0,7D083C,7D08DC), einziger Aufrufer 1AE1E8 in 1AE074. Frage: warum laeuft Cleanup beim X-Press, Singleton-Vektor 71E4455C hat NULL-Element.
- Hyp. 113: A25C64 = Fill [begin,end-8] mit 0 (Vektor elem+0x2C: begin@+8, end@+0xC). Leer begin=end=0 -> end-8 wrap (unsigned) -> Fill 0..FFFFFFF8 = Wipe.
  Elem-Objekt unkonstruiert/genullt (race). Loop-Log: normale Laeufe 2 Elemente ok (7FFEE090/E0D8); 2. Exit-Typ: erster NULL-Write aus CAC2D4 (1AE074+0x488), nicht A25C64 -> generelle Race.
- Umgehung: Guard in func_00A25C64 (generated 023): end<8 -> return. Backups work/_bk_h113/. h114/h115 (10 Laeufe): 0 Exits, Guard feuert ~30% (Elem-Zeiger Muell/NULL).
- Hyp. 115: Guard-Survivor Frame 9000 (4x) = GT-Logo+Spinner. fs-Zugriffe enden frueh (kein IO-Wait). 2/4: A2FAD0 Ringlisten-Walk mit NULL-Knoten = Busyloop (3.7M null-writes).
- Befund: Teardown-Tasks (1AE074: +0x178 1AAC8C, +0x508 7CFDD0>88B928) laufen auf Singleton/Listen, die parallel genutzt/genullt sind = Use-after-free-Race. Ursache offen.
- Hyp. 116: TLS-TID-Cache (A3046C) liefert pro r13 eindeutige ids (1,2,5,9..34) -> TID-Duplikat widerlegt. 1AAC8C/1AAD14 laufen JEDEN Frame (kein Wait/Teardown-Trigger) = normal.

## Spinner-Zustand Watchdog + Calltrace (2026-11-23, probe wd2/ct, orig+X@100, build-v020)
- WD bei 200/320 s identisch: ~20 Worker in sys_lwcond_wait (lr A4309C), tid1/2/3/5 nur lr. EVQSTAT: q4 pushed=205k, q5 64k (pending=3), q7 64k, q1 17k, q9 21k; kein Waiter-Stau.
- NEU: `[null-write] wrote32 0 to NULL+0x40 by guest-fn A2FAD0` 4,55 Mio x in 340 s (~13k/s), dazu 2x NULL+0x18 by 88B450 beim Boot. A2FAD0 = "wake all" (vtable-Slot 7 Fiber-Thread-Klasse): Schleife ueber Listenknoten, stw 0,0x40(node->+8). Element-Pointer NULL -> Fiber-Liste hat NULL-Eintraege (verwandt mit Hyp. 83 NULL-Element).
- CALLTRACE_TO=A2FAD0: Aufrufer lr=567DA4 = func_00567D74+0x2A4, tid=32 (Fiber-Run-Thread), r3=0x7FFBE280 r31=0x7FFD8E88. 567D74 hat einen direkten Aufrufer (6D5230); Rest ueber vtable.

### Fiber-Liste Busyloop (2026-11-23, probes nwt/wk/ww2, build-v020 + Diag)
- null-write tick: ~78M NULL+0x40-Writes/s von tid32 in A2FAD0, konstant 180+ s (nwt) -> Schleife laeuft praktisch dauernd, nicht 13k Aufrufe/s mit kurzer Schleife.
- [WK]-Diag in Schleife: obj=7FFBE280 cnt=1, hdr(obj+0xC)=7FFFEDC0, hdr.next=0 -> r9=0, Null-Page liest 0, cmpw nie gleich -> Endlosschleife (PS3 wuerde crashen).
- Mit PPU_WWATCH (Inline-Stores aus, Timing anders): Sentinel EDC0 sauber init (A2F638, tid1), Knoten EDD0 via A2FC54, KEIN Busyloop. Snapshot-Laeufe: Sentinel EDB0 sane, tid32 in lwcond_wait.
- Fazit: Busyloop = Alloc/Race-abhaengiger Zusatzfehler (Sentinel nullt in manchen Laeufen); Spinner haengt auch in sauberem Regime -> NICHT Ursache der Ladephase.

## STATE-Archiv (2026-11-23, aus STATE.md verschoben)
## Erledigt / widerlegt (Einzeiler)
- Pad/Dialog-Kette (Hyp. 1-14): alles ohne Wirkung, durch Umgehung (15) hinfaellig. RPCS3 `--no-gui` als Orakel tot (Shader-Precompile).
- Plan B Pad-Replay: PAD_LOG=<pfad> (patches/gt6-v020-padlog.patch, build-v020 neu gebaut, getestet) + scripts/live-padlog.ps1: user spielt live, Log -> PAD_SCRIPT-Replay.
- SDK-Update ps3recomp v0.19 -> v0.20.0 (Klon third_party/ps3recomp-v020, lokale Patches gemergt, Build gt6\build-v020): Baseline noadj 220s/Frame 4200 identisch (GT-Logo+Spinner), Fortschritt gleich; Flips ~3x weniger (Pacing). Backend-Vergleich Vulkan vs D3D12 offen (PS3RECOMP_RSX_VULKAN + rsx_vulkan_backend_init).

- probe.ps1: -FreezeSec, -Seconds 0, END-Zeile, hdd0-Kopie/Lauf (-Parallel ok). PadScript nur Press-Tokens (0x0 verboten).
- Hyp. 78-80: REALFLAG (WaitFlagEx) = DEFAULT, Dialog rendert korrekt. noadj+REALFLAG: Exit ~52s (Race, Hyp. 81/82/86 pinned=deterministisch).
- Hyp. 83: Exit = A25C64 (vector.clear) aus 88B8E0, NULL-Element im Zeigervektor 71E4455C -> zeroed 14E4000..FFFFFFF0. Hyp. 84-89: Puffer/new/Lock nicht Ursache (Heisenbug).
- Hyp. 92: orig + PAD X (80-140s) -> Frame 9000 = GT-Logo+Spinner. AdjustScreen passiert.
- Hyp. 109-116 (Details in eu-boot-log.md "Archiv"): Wipe = A25C64 Fill end-8 wrap, Aufrufer Worker-Cleanup 1AAC8C; Guard (A25C64 end<8 return) stoppt Exit, Spinner bleibt -> Wipe ist NICHT Ursache der Ladephase.

## UEBERWACHER-FINDINGS (2026-11-23, Review Hyp. 1-116 gegen ps3recomp v0.20 + third_party/GT5P)
1. Kette Hyp. 83-117 (35 Hyp.) jagt Exit-Race = Symptom. Guard-Survivor zeigen: auch ohne Exit bleibt Logo+Spinner. Race-Jagd STOPPEN.
2. UNGETESTET, billig, je 1 Batch (-Parallel 4): `PS3_PRIO_START=1` (lv2-Prioritaetsstart, SYSCALLS.md; Race-Klasse "Thread laeuft vor Init"), `PPU_RESV_OFF=1` A/B (stwcx-Reservation), `SPU_LOCKSTEP_QUANTUM`.
3. Probe != Live: user sieht live Menue nach Testrace. Probe nutzt FRISCHE userdb pro Lauf (GT6_HDD0-Kopie ohne db), boot.adc-Patches, <=320 s. Spinner evtl. = Erststart-Setup (DB/Save-Aufbau), dauert real >10 min. Test: Live-Run mit users persistenter db + 15 min, Frame-Captures 4200/9000/20000/40000.
4. GT5P-Schwesterport (gleiche PDI-Engine, third_party/GT5P/docs/progress.md): Wurzeln waren Runtime-Schreiber ins Spiel-Heap (VM_HLE_INJECT_BASE, GT6 ok = 0x03000000) und HLE-Stub mit falscher Argzahl (cellDiscGame schrieb in OPD-Tabelle). -> HLE-Stubs auditieren, die in Gast-Zeiger schreiben (PPU_WWATCH auf Opfer-Adresse, Writer-Attribution 'host' vs 'guest-fn').
5. Messen mit `PS3_VERBOSE=0` (probe.ps1 setzt das): Logging serialisiert Threads = Heisenbug-Ursache (GT5P README).

ERGEBNISSE 2026-11-23 (probe.ps1 -KeepDb, RSX_CAP=start:count:stride via -Env, build-v020):
- Befund 3 WIDERLEGT: persistente db (-KeepDb), orig+X@100s, 900 s/100k Flips: Frame 4200 AdjustScreen, 7200..19200 stabil GT-Logo+Spinner. Fresh-db ist nicht die Ursache.
- Befund 2 NEGATIV: PRIO_START=1 / SPU_LOCKSTEP(Q1000) / Kontrolle: Frame 4200 identisch (AdjustScreen, 28,4% schwarz). PPU_RESV_OFF=1 schlechter: nur 6555 Flips/430 s, NP2-IsLoaded-Schleife.
- Befund 4 Audit (statisch, offen): Verdacht M-H cellSysutilGetBgmPlaybackStatus (cellSysutil.c ~507, memset 0x28 vs SDK-Struct), M sys_process_get_paramsfo memset 256, cellSync Barrier/Rwm Host-Layout. cellFs/SaveData nicht auditiert.
- Spinner-Zustand (wd2/ct): Waiter alle idle, keine Event-Staus. NEU: wake-all A2FAD0 ~13k/s von tid32 (func_00567D74+0x2A4), Fiber-Listenknoten mit NULL-Element (NULL+0x40-Writes, 4,5M). Details eu-boot-log.md.

- Fiber-Liste A/B (snap 200s, REALFLAG 0 vs 1): Obj 7FFBE280 count=1, Knoten-Payload nicht NULL, Struktur identisch -> NULL+0x40 kommt NICHT aus dieser Liste; REALFLAG ohne Einfluss.
- Fiber-Busyloop: A2FAD0 laeuft 78M NULL-Writes/s, Sentinel obj+0xC hat next=0 (nur in manchen Laeufen, Alloc/Race); Snapshot/WWATCH-Laeufe sauber, Spinner auch dort -> nicht Ursache.

Audit #1/#2 (BgmPlaybackStatus/paramsfo gegen SDK), dann RPCS3-Vergleich: welche Syscalls/Files nach AdjustScreen fehlen in unserem Lauf.

## PDIPFS-Orakel-Test (2026-11-23, probe pdi)
- fsv (PS3_VERBOSE=1, 140 s, normale hdd0): 118 PDIPFS-Opens ok, 0 fehlgeschlagen, kein Zugriff auf PDIPFS/59.
- pdi: hdd0 = Kopie RPCS3-USRDIR (14 GB, 17,5k Dateien, work/gt6_hdd0_rp; Originale unberuehrt), -KeepDb, orig, 300 s, X@100s: 18,8k Flips, 3,1M null-writes, 9,7k NPN-IsLoaded, kein Open PDIPFS/59, kein Pamf/Dmux/Vdec-Treffer im Err-Log. Identisch zum Standard-Spinner.
- Region: KORREKTUR: RPCS3 nutzt dieselbe EU-Disc BCES01893 (BCJS37016 = interner Savedata-Name); GT6_1.N vs GT6.N = Update-Staende der Daten. RPCS3-Log = 1:1-Orakel. Spinner-Zustand unabhaengig von PDIPFS-Inhalt -> Install/Daten-Hypothese verworfen.

## Gast-PC-Sampler + RPCS3-Abgleich (2026-11-23, probe gprof)
- Sampler: gt6/src/gt6_gprof.cpp (GT6_GPROF=1, GT6_GPROF_SEC=n), tastet ctx.cia + prof_pc (letzter Syscall-Callsite) alle 5 ms. cia ist bei Threads immer Entry (0x14E0898), nur prof_pc taugt.
- Run work/probe_gprof_20261123_121842_1 (build-v020, orig, 220 s): Steady-State 37 Threads je 2,7 %: 29 pc=0xA4305C (sys_lwcond_wait-Wrapper), MpAnk F543AC, pnZ 27465C, prsIy A4F6E4, lgFF A61B80, SpuEvH A564EC. Kein Spin.
- Schluss: Deadlock-Wait, kein Busyloop. Loader 9qstY (tid 32) steht in lwcond_wait; im RPCS3-Log ab Zeile 157234 laeuft derselbe Thread weiter (LoadModule 0x2a/0x2d, PDI-Thread 0x100003a/b, Worker-Stat 59/FI).
- RPCS3 ZBm9Y IsLoaded(0x38)-Poll (1857x) laeuft dort auch bis Session-Ende: kein Unterschied zu uns.
- VERSION: RPCS3-USRDIR EMAIN.SELF 9209104 B / EBOOT.BIN 165712 B / Daten GT6_1.N (gepatcht, Update). Unsere Basis work/bin: EMAIN 8843160 B / EBOOT 72920 B / GT6.N. Oracle ist also Update-Stand, nicht Disc-Basis.
- Offen: lwcond-Adresse + Signaler von tid 32 ermitteln; pruefen ob Basis-EMAIN den 59/FI-Request kennt.

## STATE-Archiv 2026-11-23 (1.22-Abschaetzung)
- ABSCHAETZUNG Recomp Patch-EMAIN 1.22 (RPCS3 EMAIN.SELF 9209104 B; FIXEDELF114 = 1.14, 9059040 B), NICHT gestartet, User entscheidet:
  1) SELF->ELF: gt6/scripts/decrypt_self.py braucht pycryptodome (fehlt) + Keys/RAP; ELF liegt dann als work/patchelf/. Aufwand ~1-2 h, Risiko Keys.
  2) Lift + Gen (relift-gt6/gen-functions-gt6, ~1 h Rechenzeit) und Neu-Build ~2 min; alle Adress-Patches/Guards (H113 A25C64, boot.adc-Gates) neu portieren: 0,5-1 Tag. Gesamt ~1-2 Tage.



## STATE-Archiv 2026-11-23 (1.22-Port-Schritte)
- 1.22-Recomp Schritt 1 FERTIG: work/bin122/EMAIN.elf (23787792 B) per tools/self_decrypt_np.py, Klic aus RPCS3-Log; 1.00-Selbsttest identisch. Naechster: Diff 1.00/1.22, Lift in generated122.
- 1.22 Lift+Build: gt6-122/generated (74914 Funcs, code-end 0x10B8154), build-v122 linkt (GT6_V122-Guard stubs.cpp), ctor 0x1183C/lr 0x11880, setjmp C61F88/longjmp C620AC gepatcht. Probe v122b laeuft.
- 1.22 build-v122: memset/switch-Entries + setjmp-Guards (scripts/post-lift-122.ps1) -> 0 unresolved, 0 setjmp-overflow, ~9480 Flips/150 s; Frame 4200 schwarz (Hooks fehlen).
