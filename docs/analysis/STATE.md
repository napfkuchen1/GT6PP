# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-23. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`. Linie: nur Game 1.22 + ps3recomp v0.20.
Regeln/Fallen: `CLAUDE.md`. Fakten/Kanon: `LEDGER.md` (per grep). Checkpoints C0-C6 + Lauf-Tabelle: `PROGRESS.md`. Hooks 1.00 vs 1.22: `PORT_HOOKS.md`.
Alter Verlauf: `ARCHIV/docs-analysis/STATE_full_2026-11-22.md`, `eu-boot-log.md`. Pflege: je Erkenntnis EINE Zeile (<=200 Zeichen), alte Zeilen nach eu-boot-log.md.

## Ziel
Hauptmenue (C6). Erreicht bisher: C0. ALLE 1.22-Laeufe FAIL bei C1 (kein sichtbares Bild). AdjustScreen/Eingabe/Spinner kannte nur die verworfene 1.00-Linie.

## Methode (seit 23.11.)
Schicht fuer Schicht, 1.00-Referenz `git show 6697a6d:<pfad>` -> Hooks nach 1.22 portieren (tools/port_hooks.py, scripts/post-lift.ps1). Naechste Schicht erst nach Beleg (Capture/Log).
Baseline-Probe: `scripts\probe.ps1 -Name x -Boot notut -Seconds 90`; `-Boot orig|noadj|notut` nie parallel mischen (boot.adc geteilt).

## Stand
- Quit NUR MASKIERT (Arbeit6): p3-Guard parkt tid1 im Shutdown (AC7418 Event-Wait AC746C, WD@60s). Skip der Wait -> Teardown bei ~98 Flips. Game-Threads laufen weiter.
- main()=0x14010: alle Stufen laufen, IsExitGame(AD2998)=0 immer. BFF0A0 (Stufe 1414C) ist nur Init-Launcher (malloc ok, C1F4C8=Alloc 0x6000, BFF578=Setup-Stub), returnt SOFORT r3=0 (~Z.460 im Log, vor MenuClassDefine-Loads). tid1 steht bei WD@12s schon im Shutdown-Wait (13FD0 Finalizer) -> main() kehrt <12 s zurueck, Game laeuft in tid3/Workern weiter.
- C1 FAIL: Capture Frame 3500 schwarz (1 Draw, 0 nonblack). b5b260 Cache-Fill (p4) portiert, kein Effekt, kein 59/FI-Open.
- Binary traegt noch Diagnose (022/023 generated sind clean, Diagnose in work/_bk_*): vor Baseline `scripts\build-all.ps1`.

- MAIN-LOOP (Arbeit6): main-Stufe 146E8 loopt while(!AD2778()); AD2778 = alle Tasks in Liste 0x17F8F3C (Knoten per AD2750) vtbl[2]!=0. Task-Klasse vtbl 0x15DD3E0 (ctor AFE0A4, new in 124F4), [2]=AFDFC0: Loop {AFE38C-Snapshot von Struct 0x179ED20: byte0&&byte1 -> return 1 (=fertig, main verlaesst Loop)}. byte0=1 via AFE200 (von AFE2A0 wenn AF32FC==1), byte1 via AFE1C8 = (C6390C(x)==0) wenn [obj+0x34]==1, Reset AFE328/AF47A4. Hypothese: byte0/byte1 hier zu frueh 1 (falscher HLE-Rueckgabewert C6390C/AF32FC?) -> main-Loop endet. GEMESSEN: AF32FC liefert String-Ptr 0x179A1E8, AFE200 startet, TASKWAIT #0 st0=1 st1=1 sofort (2 Aufrufe). C6390C=strcmp: byte1=(strcmp(AF32FC(), obj+0x48)==0), byte2 analog. Task wartet also auf Namensgleichheit (Mode/Projektname) und ist sofort gleich -> Strings loggen.

## Naechster Schritt
Warum ist Task AFDFC0 sofort 'fertig'? Beide strcmp-Strings in AFE190 (AF32FC-Ergebnis @0x179A1E8 vs obj+0x48) per fprintf loggen; AF32FC (Mode-Getter) lesen, wer setzt den String (xref). EIN Lauf mit fprintf in generated (func_00AFE190/AFE2A0, Backups work/_bk_fdwait). Entscheidung: wenn AF32FC/C6390C HLE-Wert falsch -> fixen; sonst Task-Flag-Setter per xref pruefen.
Offene Hook-Anker: PackageNullGuard 5F81B0 (1.22-Anker per Signatur aus work/bin/_t100.elf), H113 A25C64 (kein 1.00-Code im git -> verwerfen). Danach SPURS-Walker, a3, AdjustScreen REALFLAG, ZWAP.

## Widerlegt / Symptom (nicht wiederholen)
Quit-Flag 0x1796DC8, savedata fileBuf, sceNp Term, Task-State 0x28, userdb/initUserDB (nie erreicht), IsExitGame, AD4294-Listener, Hyp. 1-116, PRIO_START/LOCKSTEP, Exit-Race.
Script-VM-Adressen 9EEA88/9F0748 sind 1.00 (0 Calls in 1.22).

## RPCS3-Orakel (gleiche EU-Disc; erreicht C6)
- Nach AutoSave2: open PDIPFS/59/FI (535 MB Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. RPCS3-Daten als hdd0: negativ -> Daten nicht Ursache.
- Spinner-Zustand (alt): 37 Threads geparkt, 29 in sys_lwcond_wait (pc 0xA4305C); Ausloeser des 59/FI-Requests unbekannt.
- VERSIONS-DIVERGENZ: RPCS3 fuehrt gepatchtes Spiel (EMAIN 9209104 B, Daten GT6_1.N); wir recompilen Disc-Basis (EMAIN 8843160 B, GT6.N).
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), gt6_gprof (GT6_GPROF=1), PAD_LOG, scripts/live-padlog.ps1, tools/adch_disasm.py. probe killt gt6 per taskkill /T.
