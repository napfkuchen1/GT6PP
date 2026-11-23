# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-23. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`.
Regeln/Fallen: `CLAUDE.md`. Gesicherte Fakten/Kanon: `LEDGER.md` (zuerst lesen). Voller Verlauf Hyp. 1-35: `ARCHIV/docs-analysis/STATE_full_2026-11-22.md`. Details/Messwerte: `eu-boot-log.md`.
**Pflege:** je Erkenntnis EINE Zeile in "Aktive Kette" oder "Erledigt" + "Naechster Schritt" aendern. Zeilen <=200 Zeichen.

## Ziel / Problem
Hauptmenue (gtmode) erreichen. Erststart-Dialoge sind per `boot.adc`-Gates umgehbar (Hyp. 15, `scripts/patch-boot-adc.py`).

## Baseline-Varianten (probe.ps1 `-Boot`)
`orig` = Original | `noadj` = Dialog+Adjust uebersprungen, Tutorial-Rennen laeuft | `notut` = alles uebersprungen, 27-Track-Schleife.
Varianten aendern `work/gt6_vol/.../boot.adc` -> NIE parallel starten. Originale in `work/ARCHIV/boot.adc.*`.
Standard: `scripts\probe.ps1 -Name x -Boot notut -Seconds 320`. Frame-Capture: `-Frame N` (Frame 4200 ~320-420 s).
Binary: `gt6\build\gt6.exe` (Game 1.22 + ps3recomp v0.20, `scripts\build-all.ps1`).

## Aktive Kette
Hauptloop 0x568800 = Game-Loop. Script-VM startet gtmode, BGM laeuft. Flips ~9500/190s.
Capture: orig = AdjustScreen wartet auf X (Render korrekt, REALFLAG). Nach X: GT-Logo+Spinner = wie noadj.
Offen: Ladephase nach AdjustScreen; noadj-Exit bei 52s (NULL-Element im Zeigervektor, Hyp. 83-89).

## Erledigt / widerlegt (Details: eu-boot-log.md "STATE-Archiv")
- Hyp. 1-116, Befund 2/3 (PRIO_START, LOCKSTEP, fresh db), Fiber-Liste/Busyloop, Exit-Race, Snap-Diff: alle negativ/Symptom. Spinner bleibt.
- Live (user) + Probes: GT-Logo+Spinner nach AdjustScreen identisch. Probe-Setup ok.
- Befund 4 Audit offen: BgmPlaybackStatus, paramsfo memset, cellSync Layout, cellFs/SaveData.
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), PAD_LOG, scripts/live-padlog.ps1. Runtime = ps3recomp v0.20.

## RPCS3-Orakel (Ueberwacher, gleiche EU-Disc BCES01893; BCJS37016 = nur interner Savedata-Name)
- RPCS3 nach AutoSave2 BKUP6: open PDIPFS/59/FI (535 MB Intro-Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. fsv-Lauf (VERBOSE): 0 fehlgeschlagene PDIPFS-Opens, 118 ok.
- Test pdi: RPCS3-USRDIR-Kopie (work/gt6_hdd0_rp) als hdd0, 300 s: NEGATIV, GT-Logo+Spinner, kein Open auf PDIPFS/59. Daten fehlen NICHT als Ursache.
- Gast-PC-Sampler (gt6/src/gt6_gprof.cpp, GT6_GPROF=1, GT6_GPROF_SEC=n): Spinner = 37 Threads geparkt, 29 in sys_lwcond_wait-Wrapper (pc 0xA4305C), kein Spin/Busyloop.
- Loader 9qstY (tid 32) haengt in lwcond_wait; RPCS3 laeuft dort weiter (PDI-Thread -> 59/FI-Open -> Pamf/Vdec). Ausloeser des 59/FI-Requests unbekannt.
- VERSIONS-DIVERGENZ: RPCS3 fuehrt gepatchtes Spiel (EMAIN 9209104 B, EBOOT 165712 B, Daten GT6_1.N); wir recompilen Disc-Basis (work/bin EMAIN 8843160 B, EBOOT 72920 B, GT6.N).
- Basis-EMAIN (work/bin, 8843160 B) statisch: Movie-Code (tv_*.pam, cellPamf/Dmux/Vdec/Sail), PDIPFSNetworkPatch*, MSystemPatch vorhanden. Kein UPDATENODEINFO/PATCHSEQUENCE.
- Basis nutzt /APP_DATA/%s.%d (GT6.N), GT6_1.N nur im Update-EMAIN. Stack-Walk tid 32 (snap_rf1) nur Altlasten; lwcond-Signaler offen.
## Naechster Schritt
Quit (~30 s) unabhaengig von Guards/Savedata/NP/IsExitGame/HDD/Task-State; Online-Patch-Pfad (processPatch) inaktiv (NP offline). Details: eu-boot-log.md "scriptflow".
Hyp. userdb widerlegt: initUserDB (boot_sequence_common) nie erreicht/geloggt (kein Open userdb0101.dat, kein GetFreeSize). Quit folgt direkt auf "LOAD complete GAME6" (GT6.0-5 gelesen).
Pfad: SaveDataUtil.load(AUTO) -> DialogUtil.openProgressDialog -> ProgressDialog.open -> func(_autoLoad) -> _load (sutil.load native, bindCheck) -> _autoLoadGameCallback -> context.wait. Danach Ende.
Hyp. VMtrace: PS3_CALLTRACE_FROM=9EEA88/9F0748 liefert 0 Calls: Adressen Hyp. 31-35 stammen aus 1.00-Aera, nicht 1.22. Handler-Tabelle/Poll in 1.22 neu finden (gdis/xref, Opcode-Tabelle 24 B/Eintrag).
Naechster Schritt: 1.22-Script-VM-Poll finden (Aufrufer von Handler per xref --call), dann CALLTRACE_FROM darauf, letzte Opcodes vor Quit lesen (ADC-Disasm: tools/adch_disasm.py, work/dialog_adc.txt).
Infra: probe.ps1 killt gt6 per taskkill /T. PS3_HLE_TRACE deckt NP-Direktaufrufe nicht ab. CALLTRACE-Zeilen "[CALL] ->" in run.log.err.

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
Hook-Inventur: docs/analysis/PORT_HOOKS.md. Boot-tragende Hooks aktiv in 1.22; offene (b5b260/ZWAP/SPURS/a3) liegen NACH Quit-Punkt, cellMusicInit2 nie gerufen -> Portieren allein loest Quit nicht.
Hyp. fdflush: FileDeviceHost-Flush-Guard portiert (port_hooks p3, AC7418/AC75B0): Quit ~30 s WEG (90 s: 5769 Flips, kein Teardown); GT6_NO_FDFLUSH=1 -> Quit wie vorher. Naechst: C1-Capture, dann b5b260 (p4).
