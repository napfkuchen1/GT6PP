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
- Arbeit7 Snapshot work/snap_a7 (probe_a7snap_20261123_232734_1, SNAP_AT=70, Frame 3500: black 100%, C1 FAIL gemessen): 68FF84 hat 9 Aufrufer (u.a. 16924/16FD0 = Worker-Loop 'while([r29+0x11]) tick(*(singleton+0x1d4))', 17DAF0, 616E9C). Tick-Handler 1.22 Tabelle 0x15B242C: 68E35C,6907C0,6722FC,683A64,686C58(=Jobliste),66E6AC. 616C80-Objekt 7FEEE000: +0x48=0,+0x4c/4d=1, +0x1d4..0x1dc=0 -> 616E6C-Loop hat KEINE Objekte (kein Tick von dort). tid30 (fuehrte 616C80 aus) steht im Snapshot in lwcond_wait lr B03BE8 (Stack 920498,8A7B08,892988,AF0C2C = Task-Pool-Worker), 15 Threads lwcond_wait.
- Arbeit7 Lauf a7base/a7nowait (je 100 s, Frame 3500): Produzent tid29 ruft 8A88DC ~6360x/100 s (=63 Hz, Wait wird normal geweckt, Frame-Pacing OK). Wait uebersprungen: kein Unterschied (32 IMMEDIATE-Draws, 139 fs-open, 5x 616C80, schwarz). Pacing/Zaehler 1d8 NICHT Blocker. Details Zaehler/atexit: eu-boot-log.md.
- Arbeit8: AutoLoad2 WIRD erreicht (Prompt-Annahme falsch): GAME6 -4, dann ok/BKUP6 -4; gamedata/ im Repo-Root (PS3_GAMEDATA_ROOT) hat Alt-Saves GT6.N (1.00-Format). Return CBRESULT statt NODATA (GT6_SAVE_CBRES=1): kein Effekt.
- Arbeit8 Oracle (RPCS3-Log Z.155401): GAME6 AutoLoad2 3x (je neuer Thread 'PDI', -4,-4, 3. ok mit GT6_1.N 16MB), dann LoadModule 0xF044 + sceNpTrophyInit; AutoSave2 BKUP6 +4 s. Wir: nach Load sofort sceNp Term (kein 0xF044/Trophy), kein Retry. Snaps work/snap_a8s50/a8s100: Worker 50 s aktiv, 100 s alle lwcond_wait, tid1 im Shutdown (lwmutex_destroy).
## Naechster Schritt
sceNpTerm-Caller = AF9870 (einziger, Fn ~AF9780: NP-Routine ruft 10BC740 NID E6C8F3F9, dann Term, unload sysmodule 0x16/0). Oracle: sceNpInit 76.08 s -> AutoLoad2 76.15 s, Term erst 106 s (Exit). Wir: Init -> Load -> Term sofort. Frage: welche NP-Bedingung (ManagerGetStatus OFFLINE? Rueckgabe E6C8F3F9) beendet Routine; AF9448/AF9780 statisch lesen, NP-Status-Werte vs Oracle (grep sceNp im Oracle-Log 155344-155500).
Offene Hook-Anker: PackageNullGuard 5F81B0 (1.22-Anker per Signatur aus work/bin/_t100.elf), H113 A25C64 (kein 1.00-Code im git -> verwerfen). Danach SPURS-Walker, a3, AdjustScreen REALFLAG, ZWAP.

## Widerlegt / Symptom (nicht wiederholen)
Quit-Flag 0x1796DC8, savedata fileBuf, sceNp Term, Task-State 0x28, userdb/initUserDB (nie erreicht), IsExitGame, AD4294-Listener, Hyp. 1-116, PRIO_START/LOCKSTEP, Exit-Race.
Script-VM-Adressen 9EEA88/9F0748 sind 1.00 (0 Calls in 1.22).

## RPCS3-Orakel (gleiche EU-Disc; erreicht C6)
- Nach AutoSave2: open PDIPFS/59/FI (535 MB Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. RPCS3-Daten als hdd0: negativ -> Daten nicht Ursache.
- Spinner-Zustand (alt): 37 Threads geparkt, 29 in sys_lwcond_wait (pc 0xA4305C); Ausloeser des 59/FI-Requests unbekannt.
- VERSIONS-DIVERGENZ AUFGELOEST (Arbeit7): work/bin/EMAIN.SELF = 9209104 B = RPCS3-EMAIN (1.22, ELF 23787792 B); alte 8843160-B-Zeile war 1.00. Rest-Diff: Save-Prefix: RPCS3 oeffnet USRDIR/GT6_1.N (16 MB, create), wir GT6.N (kleine Alt-Dateien in work/gt6_hdd0, 22.11.). Format '%s.%d' bei F87934; Prefix-Quelle offen. Prefix 'GT6' kommt aus Daten-Lookup (0x85360: Key-Suche 0x10e6310/18/20 in Config-Baum, kein fester Format-String); cellSaveData-HLE bei uns nie gerufen (0 Log), RPCS3 ruft AutoLoad2 (SECUREFILE GT6_1.0, Page_fault in Fn).
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), gt6_gprof (GT6_GPROF=1), PAD_LOG, scripts/live-padlog.ps1, tools/adch_disasm.py. probe killt gt6 per taskkill /T.
