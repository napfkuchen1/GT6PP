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

- MAIN-LOOP 146E8: Task AFDFC0 = Boot-Check (strcmp BCES01893), legitim, 0 Iterationen. Details eu-boot-log.md.


- GAME-LOOP 1.22 = 0x616C80 (1.00: 568800), Thread-Eintritt 6170AC, Tick 68FF84, laeuft (tid1/tid30); Details eu-boot-log.md.
## Naechster Schritt
(Arbeit10) Term = Script/Projekt-Aufruf PDINetwork.finalize (9AD1DC) in tid1 via 13C44..A2FFCC, Details eu-boot-log.md "Arbeit10". Bedingung davor finden.
Offene Hook-Anker: PackageNullGuard 5F81B0 (1.22-Anker per Signatur aus work/bin/_t100.elf), H113 A25C64 (kein 1.00-Code im git -> verwerfen). Danach SPURS-Walker, a3, AdjustScreen REALFLAG, ZWAP.

## Widerlegt / Symptom (nicht wiederholen)
Quit-Flag 0x1796DC8, savedata fileBuf, sceNp Term, Task-State 0x28, userdb/initUserDB (nie erreicht), IsExitGame, AD4294-Listener, Hyp. 1-116, PRIO_START/LOCKSTEP, Exit-Race.
Script-VM-Adressen 9EEA88/9F0748 sind 1.00 (0 Calls in 1.22).

## RPCS3-Orakel (gleiche EU-Disc; erreicht C6)
- Nach AutoSave2: open PDIPFS/59/FI (535 MB Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. RPCS3-Daten als hdd0: negativ -> Daten nicht Ursache.
- Spinner-Zustand (alt): 37 Threads geparkt, 29 in sys_lwcond_wait (pc 0xA4305C); Ausloeser des 59/FI-Requests unbekannt.
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), gt6_gprof (GT6_GPROF=1), PAD_LOG, scripts/live-padlog.ps1, tools/adch_disasm.py. probe killt gt6 per taskkill /T.

- (Arbeit14) a8[4] geklaert: ctrl+0xa8 = CellSaveDataStatGet (AF5260/80/A0 = funcStat-Wrapper, r4=GetStat), [4]=isNewData. =1 bei fehlendem Dir korrekt (RPCS3 gleich). Kein Bug im HLE.
- (Arbeit14) Batch GT6_SAVE_ISNEW0 (neuer Knob cellSaveData.c): g6 -> 2x GAME6 cb=-3 dann Term; all -> 1x; base -> GAME6+BKUP6 dann Term. Term unabh. von isNewData. Oracle: 3x GAME6 (3 PDI-Threads) dann AutoSave2 BKUP6, kein Term.
- (Arbeit14) Kette Save (Arb.11-14) >10 Hyp. beendet. Naechster: Term-Ausloeser ausserhalb Save (Aufrufer sceNpTerm-Thread/Script-Retry-Zaehler) oder Umgehung Term (Guard) -> naechster Blocker.
- (Arbeit14) network_available (boot_sequence_common.ad) = (type in gt6/academy/demo), nur false wenn PDINetwork.isDummy -> bei uns true. Nicht Ursache. LoginUtil.checkSaveDataBind laedt NICHT (nur online_id-Vergleich).
- (Arbeit14) Batch PS3_NET_ONLINE=1+PSNR_SERVER (NpStatus ONLINE): kein F044/Trophy, Term wie zuvor. Oracle ruft NetCtlGetInfo/NetStartDialog + Sockets nach GAME6; wir nie. Loads kommen aus scripts/gt6/SaveDataUtil.ad (_autoLoad/load, main.adc 0x69055; GAME6-Daten 6DED0 in boot.adc Z.254).
- (Arbeit14) Naechster: SaveDataUtil.load Return-Array [?,success,?] + Aufrufer/Retry-Schleife (main.adc 69143 ff, adch_disasm) -> welcher Fehlerpfad fuehrt zu PDINetwork.finalize/Term.
- (Arbeit14) Term-Guard (GT6_NP_NOTERM, sceNp.c): Term = Beginn Shutdown (danach IsLoaded NP2, SetInvalidateTile), kein Entscheider. Quit kommt nach 2 fehlgeschl. Loads. NP_TERM_BT liefert nichts.
- (Arbeit14) ORACLE-FUND: GAME6-Load 1+2 -> funcStat -4 (je ~0,2 s), Load 3 ERFOLG: SECUREFILE GT6_1.0..N (16 MB) gelesen = Oracle hat ECHTEN Save. Wir: kein Save -> Erstboot-Pfad -> Quit. Next: Save-Fixture (PARAM.SFO+GT6_1.N in gamedata GAME6) oder Erstboot-Pfad (AutoSave2 BKUP6 statt Quit) pruefen.
