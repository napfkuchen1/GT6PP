# MENU RUN NOTES (Ziel: Hauptmenue-Capture)
Arbeitsverzeichnis: Haupt-Checkout, Branch eu-first-build (Worktree war leer: kein Build/work/Disc).
Befund vor Start (aus Memory/eu-boot-log): Pad funktioniert (ZWAP-Fix); Press auf Sprachdialog -> presents -> legal -> Dialog erneut.
Offen: Dialog verbraucht Pad scheinbar nicht (kein Reader auf listener+0x54); Pointer-Cursor im Dialog.

## Zyklen
- base1: Baseline frame 4200 -> black 87.4%, ops=158 OK (work/cap_base1).
- circ1: PAD_SCRIPT CIRCLE @130s -> Dialog unveraendert (work/cap_circ1). Kein Effekt.
- probes: RWATCH/CALLTRACE auf Pad-Manager: nur A39CD8/A390E4/A395F0 lesen Pad; kein skalarer Konsument im Dialog. Konsument evtl. vektor-basiert oder VM tickt nicht.
- rpcs3-oracle (2 Laeufe, 100s/200s Wait, work/rpcs3_ref/): RPCS3 --no-gui bleibt >240s auf "Precompiling shader interpreter variants" (leerer Balken) -> kein Dialog-Referenzablauf. Hypothese "RPCS3 als Orakel" verworfen (Aufwand/Nutzen).
- rpage: Vektor-faehiger Lesewatch (PPU_RPAGE) -> kein Vektor-Leser im Listener-Block; Hypothese widerlegt. cap_base2 OK (320 s noetig).
- soak-eu: 17/18 identische Boots, 1 Boot nahm Menue-Pfad (arcade/gtmode/garage .mpackage statt LanguageSelect). Hunt 40 Boots 0 Treffer. Race, Ursache offen.

## hunt-par (2026-11-21 abend)
- 4-5 parallele Hunt-Instanzen (16 Kerne) = ~4 Boots/min statt 0.6. Eigene Zeitstempel-Ordner, kein Konflikt.
- Hunt-Skripte setzten PS3_HEADLESS -> "backend init skipped", nie Capture. Var-PRAESENZ zaehlt (="0" reicht nicht). Fix: Remove-Item Env:PS3_HEADLESS.
- "MENU BRANCH HIT" war FALSCH-POSITIV: arcade.mpackage wird in JEDEM Boot (Log-Zeile ~999) VOR LanguageSelectRoot.gpb (~1227) geladen. Detektor sampelt alle 4 s -> manchmal nur arcade sichtbar. hit_menu3 (run17, Frame 4000, 158 draws): Sprachdialog sichtbar, Cursor ja, Zeile-1-Highlight nein. => "seltener Menue-Pfad" widerlegt (frueherer Soak-Treffer vermutlich gleicher Artefakt, Log weg).
- Captures: work/hit_menu3/cap17 (bb0-7.png). Detektor jetzt: nur LanguageSelectRoot; Timeout 300 s ohne Dialog = MENU-Kandidat.

## 2026-11-21 ADCH-Analyse LanguageSelectRoot
onFocusNotify/onActivate gelesen (siehe docs/analysis/eu-boot-log.md). Naechster Schritt: PS3_CALLTRACE_TO=600A50 + PS3_CALLTRACE_AFTER=150. Zyklusbudget ueberschritten, Stopp.
ct_listbox: 0 Zeilen, Calltrace sieht nur indirekte Calls; direkte Entry-Probe noetig.

## 2026-11-21 Entry-Probe 0x600A50
fprintf am Eintritt von func_00600A50 (ppu_recomp_013.cpp, danach zurueckgebaut). clang-cl-Build, cap 4200/320 s: Dialog-Phase erreicht (LanguageSelectRoot geladen), ENTRY600A50 = 0 Treffer, Baseline unveraendert (black 87.4 %, ops=158). => ListBox-Fokuspruefung wird nie aufgerufen; Fokus-Notify-Kette startet gar nicht. Naechster Schritt: Aufrufer von 0x600A50 (xref in ppu_recomp_*.cpp) + deren Aufrufer bis zum Script-/Dialog-Tick hochverfolgen.

## 2026-11-21 Vtable-Befund 0x600A50
0x600A50 = Descriptor {0x600A50,TOC 0x14ED560} bei 0x14C4828, referenziert von Vtable 0x1460530 (159 Slots) an Slot-Offset +0x1F4 (0x1460724). Vtable-Basis wird nur in 0x601878/0x6019B8/0x6063B8 (Ctors, setzen obj+0) geladen. Entry-Probe (Log work/entryprobe2_run.err): 6063B8 3x (r3=70255D40, 7FEE4800, 7FEE52A0, lr=60654C), 601878 1x (r3=7FEE4800, lr=9791A4), 6019B8 0x, 600A50 0x. => Objekte der Klasse werden gebaut, virtueller Aufruf Slot +0x1F4 findet nie statt. Probe zurueckgebaut. Naechster Schritt: Aufrufstellen lwz rX,0x1F4(vptr)+bctrl finden (ADCH/ELF-Scan) und auf Objekt 7FEE4800 pruefen, welcher Pfad den Fokus-Slot ruft; ggf. Ctor 6063B8 vptr verifizieren.

## 2026-11-22 Event-Dispatcher / Steady-State
- Neuer Trace-Filter PS3_CALLTRACE_R3=<hex>:<len>[;..] (r3-Bereich) + Dispatcher-Probe (o30/ev0/Vtable/8 Worte, nur bei Ziel 5D9B68). Patch: patches/gt6-calltrace-r3-o30.patch. PS3_CALLTRACE_AFTER=<sek> ueberspringt Boot (Budget-Falle: ohne AFTER fuellt der Boot 20000 Calls).
- ACHTUNG: Heap-Adressen der Dialog-Objekte (7FEE4000/7FEE5540 vs 7FE05540/7FE0F540) variieren von Lauf zu Lauf -> r3-Bereichsfilter nur mit frischen Adressen aus dem selben Lauf. Der fruehere "0 Calls auf 7FEE4000 nach 200 s" ist damit nicht belastbar; die Entry-Probe 0x600A50 (adressunabhaengig) bleibt gueltig.
- Boot (ct_evt.err): 663 Dispatches an 7FEE4000/7FEE5540 (Events 7251AA04, B634, D340 ...) -> Dialogbaum wird beim Bau mit Events versorgt.
- Steady (ct_evt2/3/o30b.err, AFTER=200): nur EIN Event/Frame (0x7251D194-Typ) an ein Wurzelobjekt (7FE05540/7FE01540) via func_0099BED4->5D9CC0->5D9B68. 5D9B68 = Vtable-Slot +0x128 der Klasse (Vtable 0x145BC28 -> Descriptor 0x14C38B8 -> func 5D9B68): rekursive Weiterleitung an obj+0x30 (Kind 7FEE7540, Vtable 0x145BC28, +4=2). Rekursion im Steady-State NICHT beobachtet: Event wird auf Wurzelebene konsumiert/uebersprungen (Pruefung *(ev)==0 nach 9A8120->9A7F5C, noch nicht verifiziert: ev0 nach 9A8120 loggen).
- Kein Pad/Fokus-Event erreicht den Dialogbaum im Steady-State.
- Naechster Schritt: ev0 NACH 9A8120 loggen + was 9A7F5C mit dem Event macht; alternativ pruefen, wer 0x7251D194-Events erzeugt (99BED4-Aufrufer) und ob Pad-Events ueberhaupt erzeugt werden (Eventquelle fuer Fokus/Activate).

## 2026-11-22 ev0-Probe + Pad-Event-Test
- ev0 NACH 9A8120 = nonzero Handler-Zeiger (403CF988/403919B0 alternierend) -> Steady-State-Tick wird auf Wurzelebene konsumiert, keine Weiterleitung an obj+0x30 (Dialogbaum). Bestaetigt (work/evp.err).
- Pad-Test (PAD_SCRIPT 150:0040 160:4000 200:0040, CALLTRACE TO=5D9CC0 AFTER=140 N=40000): ausschliesslich Event 0x72523194 (Tick) von 99BED4, kein weiteres Event -> Pad-Druck erzeugt KEIN Event im Dispatcher 5D9CC0/5D9B68 (work/evpad2.err). Eingabe wird offenbar nicht in Dialog-Events uebersetzt.
- Naechster Schritt: Eingabe-Konsument zwischen Pad-Mapper A39CD8 und UI: wer liest die Mapper-Ausgabe (Struktur nach A39CD8), welcher Aufrufer erzeugt UI-Events (Erzeuger-Funktionen von Event-Hashes 7251AA04/D340 aus Boot per Caller-Trace). Probe entfernt, Backup work/_bk_ppu_recomp_013.cpp zurueckgespielt.

## 2026-11-22 Event-Erzeuger / Pad-Thread
- Erzeuger von 5D9CC0: nur Template-Sender 99BED4 (Tick, 2477x), 99BD4C, 9EEC60 (Boot-UI-Events, viele Descriptoren 72521xxx-72523xxx, stride ~0x70-0xD0), 99ECA8. Alle generisch, viele Aufrufer; Pad-Code ist keiner davon (work/ct_gen.err).
- Pad-Mapper A39CD8 hat keinen direkten Aufrufer; laeuft als Thread-Body auf tid=27 via Thunk A1C1F8 (indirekter Call, r3=D00B2EF0, r31=0x15708C0, r29 = steigender Zaehler) in Dauerschleife (work/ct_map.err). PS3_CALLTRACE_R3=165AD40:0x800 (Pad-Manager) liefert 0 virtuelle Calls (Zugriff nur direkt).
- Naechster Schritt: Ziel der Mapper-Ausgabe verfolgen: in A39CD8 die Schreibziele (vm_write, Stores) auf Objekt D00B2EF0 / 0x15708C0 identifizieren und per PPU_WWATCH/PPU_RWATCH pruefen, ob/wer diese Ziele auf dem Main-Thread liest.

## RPCS3-Log-Abgleich (2026-11-22)
- Roadmap: nichts hat Prio vor dem Menue. M2 offen nur setjmp/longjmp; M3 D3D12-Backend/Shader; M4 XInput/Wheel spaeter.
- RPCS3.log (3:48 min): 58 Threads. Nach cellPadInit: _cfg_evt_hndlr, lgFF, 4x TM_FFB_WorkerThread, libusbd_callback/usbd_thread; Event-Queues 17, Ports 13, Timer 54 Zeilen (sys_timer_connect_event_queue data1=5 data2=0x1f40), lwcond 31, sys_fs_fcntl 160 (0xc0000006 /dev_bdvd,/dev_hdd0).
- Spiel ruft in RPCS3 cellSysutilGetSystemParamInt(0x112 ENTER_BUTTON_ASSIGN); unsere HLE liefert CROSS -> kein Unterschied. Sysmodule 0x21 (key2char) laedt auch bei uns.
- Polling-Threads in RPCS3: ZWAP (cellMusicGetPlaybackStatus2 17058x), ZBm9Y (IsLoaded 0x38 13409x). Bei uns IsLoaded 5407x; Music-Stub log-once -> Polling unbestaetigt.
- Unser Log zaehlt Thread/Queue/Timer-Aufrufe nicht -> kein direkter Zahlenvergleich moeglich. Offen: TM_FFB-Threads/sys_timer->Queue bei uns verifizieren, Zaehler in HLE einbauen.

## sys_timer One-Shot Fix (2026-11-22)
- RPCS3-Abgleich (Warning-Log, log.yml wird von rpcs3 --no-gui NICHT beachtet; Pfad mit Leerzeichen muss in "..." im ArgumentList): Spiel erzeugt Timer (gFKsE/9qstY, Queue 0x8d033900) und startet sie.
- Bei uns: sys_timer_start(period=0, base=absolute Systemzeit us) -> EINVAL, Timer feuerte nie (~6700 Starts pro Lauf).
- Fix: period==0 = One-Shot bei absoluter Systemzeit (ps3_system_time_us exportiert aus ppu_sysprx.cpp, Backup work/_bk_ppu_sysprx.cpp, work/_bk_sys_timer.c; Kopie work/sys_timer_oneshot_fix.c).
- Ergebnis: Timer feuern jetzt, Dialog UNVERAENDERT (black 87.4 %, ops=158, cap_timer2, Pad-Script gedrueckt). Echter Bug, aber nicht die Dialog-Ursache.
- Offen: sys_event_queue/port- und Thread-Zaehler gegen RPCS3, Pad-Mapper-Ausgang, RPCS3-Trace per GUI-Log-Einstellung.

## Event-Queue-/Pad-Zaehler-Abgleich (2026-11-22)
- RPCS3 (Warning-Log, ab 12 s) legt 15 Event-Queues an, wir 9. Fehlend bei uns: sys_config-Queue size 32 (+Thread _cfg_evt_hndlr, kommt aus echter libio via sys_config_start), usbd-Queue 127 (sys_usbd_initialize), 2x size 42 und 1x size 32 (libsre/Spurs-Pfad), 1x size 127. Erklaerung: RPCS3 laeuft mit LLE-libio/usbd/Spurs, wir mit HLE -> kein Defekt per se.
- Pad-Zaehler (cellPad.c, [padcnt], Backup work/_bk_cellPad.c): Spiel ruft nur cellPadGetInfo2 + cellPadGetData (je >15000x, 1:1) und einmal ClearBuf; kein GetCapabilityInfo/SetActDirect/PressMode/SensorMode. Pad wird normal gepollt -> Pad-Datenquelle ok, Konsument ignoriert Eingabe.
- Naechster Schritt: Pad-Mapper-Ausgang (D00B2EF0 / 0x15708C0) per WWATCH/RWATCH; pruefen ob Mapper-Thread (tid=27) Daten ueberhaupt in Spiel-State schreibt.

## Pad-Mapper-Watch + PAD_SCRIPT-Oktal-Falle (2026-11-22)
- WWATCH/RWATCH 0x15708C0 (cap_padmap1): Objekt = Thread-Wrapper (Ctor A1C26C tid=1, Leser A1C130/A1C1F8 starten Thread-Body). KEIN Pad-Ausgang. Mapper-Ausgang liegt woanders (Schreibziele in A39CD8, gt6/generated/ppu_recomp_023.cpp).
- PAD_SCRIPT-Masken MUESSEN 0x-Praefix haben (strtoul base 0): "0040" = oktal 0x20 (press 0x0020). Lauf padreal1 mit 0x0040/0x4000 (log: press 0x0040 / 0x4000 bestaetigt): Dialog UNVERAENDERT (black 87.4 %, ops=158, Zeile 1 ohne Highlight, Mauszeiger sichtbar). Fruehere PAD_SCRIPT-Tests ohne 0x ggf. ungueltig, Ergebnis aber jetzt mit gueltiger Eingabe bestaetigt.
- cap-gt6 -Env trennt an Kommas: PPU_RWATCH=<hex>,<len> geht nicht (Laenge verloren).
- Naechster Schritt: A39CD8 lifted lesen, echte Schreibziele (Pad-Mapper-Ausgang) finden, dort WWATCH/RWATCH.

## Pad-Mapper-Gating + LEN-Konstanten (2026-11-22)
- A39CD8: r21 = Pad-Manager 0x165AD40; Ausgaenge manager+0xB08..0xB14 (0x165B848..). padnz2: Mapper liest 0x40 an 0x165ADE8/ADEA zur Presszeit -> Lieferung ok.
- Gating im Mapper: button[1] Low-Nibble*2 = r0; Stick/Sensor-Pfad (+0xB0E..B14) nur bei r0==0x18 (len 24). Wir lieferten len 28 -> Pfad tot.
- Ursache: cellPad.h CELL_PAD_LEN_CHANGE_PRESS_ON=24/SENSOR_ON=28; SDK: 20/24. Gefixt (Backup work/_bk_cellPad.h). Game setzt SetPortSetting(0, 0x6) -> len 24.
- Verifiziert (padw2): Mapper schreibt jetzt 0x200/0x18F (Sensor-Ruhewerte) nach 0x165B84E..B85E. padlen1/padw2/padr3: Dialog weiter unveraendert (black 87.4 %, ops=158).
- padr3: Listener-Records 0x165B1A8+ werden nur vom Mapper (Listenwalk), 0x03002F00 (Flag=1) und Decoder A395F0 (read2) gelesen. Naechster Schritt: Aufrufer/Konsument von A395F0 und Ausgabe nach dem Decoder.
- Diagnose im Code: [padpress] (cellPad.c, stderr nur bei PAD_SCRIPT-Druck), PPU_RWATCH_NZ (ppu_loader.cpp, env-gated). Riesige Watch-Caps machen Lauf zu langsam (>330 s).

## Zeitquellen-Check + Anim-Diff + Upstream + Xbox (2026-11-22)
- Anim-Diff Frame 3400 vs 4200: Dialog statisch, nur Cursor-Pixel differieren -> keine laufende Animation.
- Upstream ps3recomp: keine neuen Hinweise zu Pad/Dialog.
- Xbox-Pad (echtes XInput): keine Reaktion -> Problem nicht Eingabe-Backend.
- Zeitquellen statisch geprueft: ppu_timebase_now = QPC, 79.8 MHz, monoton, Anker bei Erstnutzung (ok). sys_time_get_system_time = QPC-Mikrosekunden seit Erstaufruf (ok, gleiche Hostuhr). sys_time_get_timebase_frequency = 79800000 (ok).
- Auffaellig (klein): sys_time_get_current_time liefert QPC-Uptime (sec seit Boot), nicht Epoch-Zeit wie LV2. Kann Datums-/Erststart-Logik beeinflussen. Nicht als Ursache bestaetigt.
- Fazit: keine Zeitquelle defekt. Offener Kandidat: Dialog-Open-Sequenz wartet auf Event/Callback (sysutil, Queue, Eventflag), nicht auf Zeit.
- Naechster Schritt: Thread-/Wait-Dump bei Frame ~3400 (wer blockiert worauf), plus Test current_time als Epoch.

- Epoch-Test (2026-11-22): sys_time_get_current_time liefert jetzt Unix-Epoch (GetSystemTimePreciseAsFileTime; Backup work/_bk_sys_timer.c). Capture cap_epoch1: black 87.4 %, ops=158 -> Dialog unveraendert. Zeit-Hypothese damit erledigt (Fix bleibt, da LV2-konform). Naechster Schritt: Wait-Dump aller Threads bei Frame 3400.

## Wait-Dump bei ~270/300 s (2026-11-22)
- Neu: env `PS3_WD_AT=<s1>,<s2>` (ppu_loader.cpp, Thread in lv2_syscall; gt6 hat keinen boot_main-Watchdog). Dumpt pro Guest-Thread lr/r3/sp, laufenden lv2-Syscall (g_sc_inflight) + HLE-inflight. Backup work/_bk_ppu_loader3.cpp. Logs work/wd2_run.log.err, work/evq1_run.log.err (PS3_EVQSTAT=300).
- Zustand (beide Samples identisch = statisch): ~20 Worker idle in sys_lwcond_wait (lr A4309C); tid1 (Fiber-Ctx) in cellFiberPpuWaitFlag, tid32 in cellFiberPpuRunFibers (lr A2FB4C); tid3 usleep 16 ms (lr A37464, Frame-Takt); tid27 Pad-Mapper usleep 12.5 ms; tid 5/36/37/42/43 lr A30550 ohne Syscall.
- Event-Queue-Waiter OHNE Timeout: q3 (tid15, lr A566C4), q4 (tid18, lr 82039C), q8 (tid22, lr 0), q9 (tid31, lr 7F9F6C). Mit Timeout: q1 (tid2), q6 (tid20), q7 (tid21). cond_wait 10 s: tid16/17/30.
- EVQSTAT: q3, q6, q8, q9 bekommen NIE einen Push. q4 size=1: 221 Pushes, stoppt nach Boot (~Event 1500). q1 ~15k, q5 ~61k (pending=4, kein Waiter), q7 ~61k (Timer). Ports: port2->q3 (name 0xD0A77), port3->q6, port4->q8; nur port1->q1 sendet (A466A4+0x742).
- Bewertung: Sender fuer q3/q8 (und q6/q9) feuern nie. Kandidat fuer fehlende Dialog-Fokus-/Open-Sequenz: Producer von port2/port4. Nicht bestaetigt.
- Naechster Schritt: Erzeuger/Sender von port2 (name 0xD0A77) und port4 per Caller-Trace auf sys_event_port_send (syscall 134) finden; Consumer q3 = func um A566C4, q8 = Thread-Entry tid22.

## Queue/Port-Zuordnung (2026-11-22, EVT_PUSHLOG=4, PS3_EVT_CREATE_STACK)
- Neu: env `PS3_EVT_CREATE_STACK=1` (sys_event.c, port_create); Stack-Dump blieb im Log leer (ppu_dump_guest_stack liefert nichts). Backup work/_bk_sys_event2.c. Logs work/pcs1_run.log.err, work/pl4_run.log.err.
- port2->q3 (name 0xD0A77) gehoert zum Thread tid15 "Spu Event Handler" (SPURS-Eventhandler, entry 14E14C0). Sender waere SPU-Seite (throw_event), nie aktiv.
- port3->q6: usbd-Kontext (cellUsbdSetThreadPriority2, tid20 pnZ). Sender = usbd-HLE, nie aktiv (Stub).
- port4->q8: mempool-Thread tid22 "lgFF" (unser sys_mempool). Sender fehlt.
- q4 (tid18 sgx-audio-thr, size=1) = SPURS-Queue, src=0xFFFFFFFF53505501 ('SPU\1') + d=0x701AC000/<wid 0..A>: ~200 Pushes im Boot, danach Stillstand -> SPURS-Workloads melden nichts mehr.
- q5/q7 = Audio-Notify (key 0x23A0 / 0x48DA6C685BCC82D), laufen (61k Pushes). Keine Audio-Ursache.
- q9 tid31 MEfYS: Sender unbekannt.
- Naechster Schritt: warum SPURS nach Boot keine Events mehr sendet (Spurs-Workload-Status 0x701AC000, Workload-Wakeups); usbd-Events (q6) gegen RPCS3 pruefen.

## SPURS-Check (2026-11-22, SPURS_KSTAT=20, PS3_EVT_CREATE_STACK=1; Lauf ks3 mit GT6_BUILD_DIR=gt6\build-clangcl)
- Korrektur: "Stack-Dump leer" (pcs1) war falsch; run-gt6.ps1 nutzt ohne `GT6_BUILD_DIR` das alte gt6\build\gt6.exe. Mit clangcl-Build liefert PS3_EVT_CREATE_STACK Stacks.
- Neu: `SPURS_KSTAT=<sek>` in cellSpurs.c (Kernel-Thread: Slots, je wid state/ready/sig/act/idle/runs). Backup work/_bk_cellSpurs2.c. Log work/ks3_run.log.err.
- Ergebnis: SPURS laeuft weiter. Beide Kernel-Threads loopen (loop#20000), wid0-7 state=2, runs steigen (wid5 12k->20k, wid7 9.8k->15k), alle Slots idle/ready 0. Stillstand-Hypothese SPURS widerlegt; q4-Stopp = Jobchain 0x701AC000 liefert keine Completion mehr (sgx-audio-Chain), nicht Kernel.
- Port-Ersteller (Guest): port1 func_00A47588 (PDI GFXS); port2 (->q3, Spu Event Handler) func_00A434FC/00A4259C; port3 (->q6) func_00274178 <- A37E58 <- B62864 <- 007D7340; port4 (->q8) func_00A5DE60+0x2A0 <- A2B94C <- A1C130.
- Naechster Schritt: Sender-Wrapper der Klassen von port3/port4 (analog port1 A466A4+0x742) finden und die Aufrufer per Entry-Probe/Calltrace pruefen; Consumer q6=tid20, q8=tid22.

## 2026-11-22 Cleanup + RPCS3 usbd-Abgleich
- Diagnosen entfernt: [padpress] (cellPad.c), SPURS_KSTAT/g_kstat_runs (cellSpurs.c), PPU_RWATCH_NZ (ppu_loader.cpp), PS3_EVT_CREATE_STACK (sys_event.c). Backups: work/_bk_cellPad3.c, _bk_cellSpurs3.c, _bk_ppu_loader4.cpp, _bk_sys_event3.c. PS3_WD_AT bleibt. Rebuild gt6/build-clangcl OK.
- cellPad-Tests (libs/input/tests/test_pad_*.c) nicht ausgefuehrt: POSIX (sys/mman.h, sdl2-config), kein clang/gcc im PATH, kein WSL. Nur unter Linux/WSL lauffaehig.
- RPCS3 sys_usbd.cpp: Events 1=ATTACH(arg2=Geraetenr), 2=DETACH, 3=TRANSFER_COMPLETE(arg2=transfer_id), 4=TERMINATE. initialize schreibt handle 0x115B, KEIN Event bei init/register_ldd. ATTACH nur wenn registrierter LDD zu vorhandenem Device (VID/PID) passt. Ohne Device bleibt receive_event blockiert -> q6 bekommt auch in RPCS3 ohne USB-Geraete keinen Push. => q6-Stillstand ist KEINE Divergenz, usbd-Hypothese fuer Dialog-Stall schwach. Xbox-Pad ueber usbd nur relevant falls Spiel einen LDD fuer Pad registriert (cellPad laeuft bei uns via HLE).
- Unser sys_usbd_receive_event (lv2_register.c:2517) liefert type 0 + Sleep(20) statt zu blockieren; guest ignoriert (korrekt-ish). Naechster Schritt: Sender port3/port4 Wrapper (analog port1 A466A4+0x742), q9-Sender, Job-Chain 0x701AC000.
- Verifikation Cleanup-Build: cap clean1 (Frame 600, 110 s) black 99.2 %, ops=17 = erwartete Kurzlauf-Baseline, kein Regress. q4 pusht im Kurzlauf weiter (65k bei 110 s), Stillstand-Messung frueherer Laeufe (~200) erneut pruefen (Messzeitpunkt/Queue-Zuordnung).

## 2026-11-22 Sender port3/port4 (statisch + Entry-Probe)
- Guest sendet via syscall 0x8A=138 (sys_event_port_send): Sites func_00273724 (usbd-Klasse, port3/q6), func_00A5CE70 (port4/q8), func_00A568F4 (SPURS/q3), 0082114C, A466A4 (port1), A61558/A61594/A62EE8/A62FD8/A63010.
- 00273724: queued Request + port_send(obj+0x8C), KEIN direkter Aufrufer (indirekt = USB-Transfer-Callback). Ohne USB-Geraet nie aufgerufen, wie RPCS3.
- A5CE70 <- A5D018 <- A2C264 (Schleife ueber 3 Objekte, dann A5D018) = Shutdown/Destroy-Pfad; Entry-Probe (cap ent1, Frame 600): A2C264/A5D018/A5CE70 = 0 Treffer, A5DE60 (Creator) 1x. => q8 sendet nur beim Beenden: leeres q8 ist NORMAL. q6/q8/q3 Stillstand = erwartete Idle-Waiter, KEINE Fehlerquelle. Queue-Hypothese damit insgesamt widerlegt (q9 ungeprueft, vermutlich analog).
- gt6/generated/ppu_recomp_023.cpp nach Probe zurueckgespielt (work/_bk_ppu_recomp_023.cpp), noch nicht neu gebaut.
- Naechster Schritt: Dialog-Seite: wer ruft ListBox-Fokus (Slot +0x1F4 Vtable 0x1460530) / welcher Pfad erzeugt onFocusNotify; Pad-Konsument jenseits des Listener-Records; ggf. Eingabe-Ereignisklasse (Pad-Event-Typ) pruefen.

## 2026-11-22 q9 geprueft
- q9 (size 4, tid31 MEfYS) hat KEINEN Port: es ist eine Timer-Queue (sys_timer 2 und 3 per connect_event_queue, d1=0x7FFD4CD0/0x7FFD4C68). Timer 2 wird als One-Shot (period=0) ~49x/s neu gestartet (5394 Starts in 110 s, base ~1.7 ms vor sysnow) -> Timer-Queue lebt, Consumer arbeitet. Timer 3: 0 Starts (unbenutzt in dieser Phase).
- PS3_EVQSTAT zaehlt nur Port-Sends, NICHT timer_send_event -> "q9 nie Push" war Messartefakt. Alle 'fehlenden' Queues (q3/q6/q8/q9) damit erklaert, Queue-Spur abgeschlossen.
- Probe [timer-start] entfernt (Backup work/_bk_sys_timer2.c = Stand vorher inkl. Epoch-Fix).

## Fokus-Seite: Slot +0x1F4 Aufrufer (2026-11-22)
- 131 Aufrufstellen `lwz ..,0x1F4(vtbl)+bctrl` in gt6/generated; 6 Kandidaten per Entry-Probe (Frame 4200, 320 s): 5D2BB0, 5D2F24, 782DC, 34E014, 54DAE0, 68D384 -> 0 Treffer. Keiner laeuft vor/im Sprachdialog.
- Fazit: Fokus-Pruefung wird von keinem dieser Sites erreicht; restliche ~125 Sites ungeprueft. Besser: Generic-Hook in ps3_indirect_call (Ziel==0x600A50 + Vtable-Slot-Loads) oder Aufrufer der Dialog-Update-Funktion (Vtable 0x1460530 andere Slots) verfolgen.
- Probes entfernt, Backups work/bk6, Build clean.

## VTHOOK (Vtable 0x1460530, 2026-11-22)
- Temp-Hook in ps3_indirect_call_impl (env PS3_VTHOOK): loggt indirekte Calls, deren Ziel ein Code-Zeiger der Vtable 0x1460530 ist (Slots 0..0x2FC). Lauf Frame 4200: 261 Zeilen (work/vth_run.log.err).
- ListBox-Objekt 7FEE6800 lebt: Slot 0x4 (ctor 601878, lr 9791A4), 0x28 (600B40, lr 99BD40), 0x30 (600AC4, lr 99B54C), 0x8. Slot 0x1F4 (600A50): 0 Treffer; Nachbar 0x1F8 (54D220 Default) von lr 54D50C aufgerufen.
- 0x290/0x294 Treffer = std::map-Code (587464), Zufall, kein Dialogbezug.
- Naechster Schritt: Aufrufer von 600B40 (lr 99BD40) / 600AC4 (lr 99B54C) -> Dialog-Update-Funktion rund um 99B5xx/99BDxx lesen: wo wuerde der Fokus-Aufruf stehen und welche Bedingung blockt.
- Hook entfernt (Backup work/bk6/ppu_loader_pre_vt.cpp), Build clean.

## 99B518 / 99BC94 gelesen (2026-11-22)
- 99B518 (lr 99B54C) und 99BC94 (lr 99BD40) = generische Handle/Container-Lookups (Vtable+0x30 holen, Refcount-/Weak-Ptr-Deref, dann +0x28). Viele Aufrufer in ppu_recomp_000 (14DAC, 16544, ...). KEIN Dialog-Update, keine Fokus-Bedingung hier. Spur tot.
- Fokus-Aufruf (Slot 0x1F4) kommt also aus Pfad, den ein Pad-/Navi-Event ausloest, der nie startet. Naechster Schritt: nach LEN-Fix erneut Pad-Ausgang pruefen: PAD_SCRIPT mit 0x-Maske + PPU_RPAGE auf Listener-Records 0x165B1A8.. (Stride 0xE0) -> liest ueberhaupt jemand die Button-Felder?

## RPAGE-Lauf + DSP-Probe (2026-11-22)
- PPU_RPAGE auf Listener-Records 0x165B1A8 (nach LEN-Fix): Leser nur Kopierhelfer A390E4/B90614/A39CD8/A3CE18/A3CC40; 40A470 = Resolver-Artefakt (naechster Symbolname, ungenau). Kein echter Konsument.
- DSP-Probe in 5D9B68 (nach 9A8120): Wert [r25] (h) ist im Steady-State 0 fuer alle Objekte (ev0=4035E260 Tick); h!=0 nur beim Boot-Aufbau (Handlerzeiger, erste 200 Treffer). Probe verlangsamt Lauf so stark, dass Frame 4200 nicht erreicht wird -> Steady-State-h!=0 nicht ausgeschlossen, nur nicht gesehen.
- Einsicht: Highlight fehlt auch ohne Eingabe -> Initialfokus ist wahrscheinlich Script-/Tick-getrieben, nicht Pad-getrieben. Pad-Spur damit niedrige Prio.
- Naechster Schritt: Roadmap M3 (RSX erster Frame / Dialog-Rendering) und Script-VM-Tick pruefen statt weiter Pad.
