# GT6PP EU - STATE (single source of truth)

Stand: 2026-11-22. Branch `eu-first-build` im Haupt-Checkout. Disc: EU `BCES01893`.
Regeln und Fallen: `CLAUDE.md`. Detail-Logs (nur nachschlagen): `docs/analysis/eu-boot-log.md`, `work/MENU_RUN_NOTES.md`, `docs/analysis/CONTINUE-HERE.md`, `docs/HANDOFF.md`, `docs/analysis/eu-session-handoff.md`.
**Pflege:** nach jeder Erkenntnis Tabelle + "Naechster Schritt" hier im selben Zug aktualisieren, Details in `eu-boot-log.md`.

## Problem
Hauptmenue nicht erreicht. Erststart-Sprachdialog (~Frame 3300, `LanguageSelectRoot`) rendert (Panel, Titel, 4 Zeilen), reagiert aber nicht auf Pad, und das Zeile-1-Highlight fehlt (RPCS3 zeigt es). Highlight fehlt auch ganz ohne Eingabe -> Verdacht: Fokus/Highlight ist Script-/Tick-getrieben, nicht Pad-getrieben.

## Baseline / Standardlauf
- Binary: `gt6\build-clangcl\gt6.exe` (altes `gt6\build\gt6.exe` NIE nehmen). Rebuild clang-cl ~2 min inkrementell.
- Lauf: `powershell -File scripts\probe.ps1 -Name base -Seconds 320 -Frame 4200` -> erwartet black ~87.4 %, ops=158 (cap_base1/base2). Lauf braucht >200 s.
- Parallel bis 4-5 Instanzen (`-Parallel 4`). Determinismus: 17/18 Boots identisch; Soak: `scripts/soak-gt6-eu.ps1`, `scripts/hunt-menu-branch.ps1` (Detektor-Falsch-Positiv bekannt, siehe CLAUDE.md).
- Pad-Pfad (Referenz): Manager 0x0165AD40, Listener ab 0x165B1A8 Stride 0xE0, Mapper A39CD8 (Thread-Body tid 27), Kopie A390E4/B90614, Decoder A395F0. Dialog-Vtable 0x1460530, Slot +0x1F4 = 0x600A50 (ListBox-Fokus-Check), Event-Dispatcher 5D9B68 (Slot +0x128).
- Probes (Default aus): `PPU_RPAGE`, `PAD_SCRIPT`, `PPU_RWATCH/WWATCH`, `PS3_CALLTRACE(+_AFTER/_TO/_R3)`, `PS3_WD_AT`, `PS3_EVQSTAT`, VTHOOK. Patches in `patches/`.

## Hypothesen
| # | Hypothese | Status | Evidenz |
|---|---|---|---|
| 1 | Maus/Analogstick/Xbox-Pad als Eingabe | widerlegt | negative Ergebnisse 11-21, Xbox-Pad 11-22 ohne Wirkung |
| 2 | WaitFlag-Waker / idle-worker | widerlegt | WaitFlag-Experimente, ~20 idle lwcond-Worker normal |
| 3 | Sprach-Persistenz / frische userdb / `PS3_LANG` | widerlegt | Dialog = Erststart-Dialog, unabhaengig von Systemsprache |
| 4 | Race / nichtdeterministischer Pfad | widerlegt | 17/18 identisch; "Menue-Pfad"-Treffer war Falsch-Positiv |
| 5 | RPCS3 als Dialog-Orakel | unbrauchbar | `--no-gui` haengt im Shader-Precompile (3 Laeufe verschwendet) |
| 6 | unsichtbarer Vektor-(lvx-)Leser des Pads | widerlegt | PPU_RPAGE inkl. Vektor: Leser nur Kopierhelfer |
| 7 | sys_mempool_* fehlt | umgesetzt, kein Effekt | Commit 8ed9afa, Dialog unveraendert |
| 8 | sys_timer period=0 EINVAL / get_current_time klein | gefixt, kein Effekt | One-Shot-Fix, Epoch-Fix, Zeit-Hypothese tot |
| 9 | cellPad LEN-Konstanten falsch | gefixt, kein Effekt | PRESS_ON 24/SENSOR_ON 28 -> 20/24; Mapper schreibt Sensorwerte, Dialog gleich |
| 10 | fehlende Event-Queues (RPCS3 15 vs unsere 9) | widerlegt | q3/q6/q8 leer = normal (kein USB-Device, Shutdown-Pfad), q9 = Timer-Queue, SPURS laeuft |
| 11 | Pad-Events im Dialogbaum | widerlegt | Dispatcher: 1 Event/Frame an Wurzel, kein Pad/Fokus-Event; Spiel pollt GetInfo2+GetData >15000x, Konsument ignoriert Eingabe |
| 12 | Fokus-Setter ListBox (+0x1F4) laeuft | widerlegt | 0x600A50: 0 Aufrufe, 6 von 131 Callern geprueft, VTHOOK: Slot nie |
| 13 | RPCS3-Boot-Diff Threads/Queues | Spur abgeschlossen | LLE (libio/usbd/Spurs) vs HLE, keine fehlende Queue relevant |
| 14 | Dialog-Update / Script-VM-Tick / Draw-Fokus-Seite | zurueckgestellt | Highlight fehlt auch ohne Eingabe; DSP-Probe 5D9B68 [r25]=0 im Steady-State; durch Umgehung (15) nicht mehr blockierend |
| 15 | Dialog/Adjust/Tutorial per boot.adc-Gate umgehen | **bestaetigt** | 3 Ein-Byte-Datenpatches (`scripts/patch-boot-adc.py`), gtmode-Projekt laedt |
| 16 | Track-Sound-Ladeschleife (54 Files x338) blockiert Menue | **offen, 2 Laeufe verbraucht** | Treiber = Sound-Player-Create 7D8308 (Worker tid 33), Aufrufer unbekannt; Details unten |

## Naechster Schritt (EINER)
1. **Hyp. 17:** Aufrufer von func_007D8308 (CALLTRACE_TO=7D8308) + Vergleich Original-Boot ohne Tutorial-Skip; ggf. Track-Preload umgehen. Siehe "Hyp. 16 Analyse" unten.
2. Danach: mfc-REJECTED-Divergenz (ea=0x7FFFFFFF, img=19 pc=0xF0C, ~1 von 3 Laeufen) und blauer Block AdjustScreen (M3).
3. Hinweis: extrahierter Baum `work/gt6_vol` ist gepatcht; Original `work/ARCHIV/boot.adc.orig`.
Optional: US-Disc (BCUS98296) als Gegenprobe, falls Build-Basis vorhanden.

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done, Exit "8/8 identisch" nicht formal erfuellt. M3 (RSX/first frame) offen bis Menue-Frame. Siehe `ROADMAP.md`.

## Aufraeumen 2026-11-22
`work/build*.log` und `work/_db_aside_*` nach `work/ARCHIV/` verschoben (nichts geloescht). `work/_bk_*` bleibt. `probe.ps1` archiviert userdb kuenftig selbst nach `work/ARCHIV/`.
Offen: voller 320-s-Baseline-Lauf mit `probe.ps1` noch nicht gefahren (nur Smoke-Test 20 s).

## Umgehung Sprachdialog (2026-11-22, Hyp. 15)
- Gate in `boot.adc` `display_sequence_gt6`: `LanguageSelectRoot.open` nur wenn `getOutOfSystemLanguages().size > 0` (INT_CONST 0 bei 0x18924 und 0x196D6). Datenpatch am extrahierten `work/gt6_vol/projects/gt6/boot/boot.adc` (wird per pfs-override geladen): Operand 0 -> 99 (Byte +1). Original: `work/ARCHIV/boot.adc.orig`.
- Lauf `nodlg` (probe_nodlg_20261122_155157_1): Dialog weg, naechster Screen `AdjustScreenRoot` ("Bildschirm anpassen", deutsch) rendert, wartet auf X (Pad). Render-Defekt: blauer Block oben rechts ueber 1/4 Bildschirm (M3).
- Zweiter Patch: Gate 0x18A69 `JUMP_IF_FALSE`(15) -> `JUMP_IF_TRUE`(14) ueberspringt AdjustScreenRoot (Kopie `work/ARCHIV/boot.adc.nodlg_noadjust`). Lauf `noadj`: siehe unten.
- Lauf `noadj` (probe_noadj_20261122_155749_1): AdjustScreen uebersprungen, Boot laeuft weiter -> applySaveData -> `tutorial.xml` -> `race.adc`/`race_tutorial` (Erststart-Intro-Rennen), Frame 4200 = GT-Logo-Ladebildschirm. Pad war nur fuer Dialoge noetig -> Blocker ist umgehbar.
- Dritter Patch: Gate 0x18FDA JUMP_IF_FALSE->JUMP_IF_TRUE (Tutorial ueberspringen, `TutorialUtil.done` + `startProject("gtmode")`), Kopie `work/ARCHIV/boot.adc.nodlg_noadjust_notut`. Lauf `notut`: siehe unten.
- Lauf `notut` / `menu3` (3 parallel, probe_menu3_20261122_161447_*): Tutorial uebersprungen -> `gtmode.adc`, `GTModeRoot.gpb`, home/*.img laden = **Hauptmenue-Projekt wird geladen**, aber Bildschirm bleibt GT-Logo-Ladebildschirm (Spinner animiert, black 99.5 %). Frame 4200 wird nicht mehr erreicht (Frame 3000 ok).
- **Hyp. 16 (offen):** danach Endlosschleife: 54 `sound_gt/track/*.sgb/.sgh` (0428..0456) werden 338x hintereinander geladen (13.6k Opens, 19.7 GB gelesen in 540 s); pro Durchlauf Threads tid 60-64 (Entry 0x014E0898 "ZAbZY") create/exit. Loader meldet "fertig" nie -> Completion-/Retry-Check. 1 von 3 Laeufen divergiert frueher (8x `[mfc] REJECTED malformed transfer img=19 pc=0xF0C ea=0x7FFFFFFF`, Stillstand bei usercmd #4864) - eigene Spur.
- Boot-Zeit: Dialog ist nicht mehr noetig; bis Ladebildschirm ~100-150 s, Rest = Track-Sound-Schleife.
- Skript: `scripts/patch-boot-adc.py` (reproduziert die 3 Patches; Original `work/ARCHIV/boot.adc.orig`). WICHTIG: extrahierter Baum ist gepatcht -> Baseline-Vergleiche mit Original-boot.adc.

## Hyp. 16 Analyse (2026-11-22, 2 Probe-Laeufe, Zeitbox verbraucht)
- Loop-Muster: 27 Tracks (0428..0456) in FESTER Reihenfolge (0455 0438 0428 0453 0442 0429 0432 0452 0431 0450 0456 ...), pro Track .sgh (160 B, 2x geoeffnet) + .sgb (3.6-5.4 MB, per Thread gelesen). Nur im 1. Durchlauf zusaetzlich scene/script, character, effect/texset, motion, piece/home/*.img, TutorialDialog.gpb -> danach reine Track-Schleife, nichts Neues wird geladen.
- Thread-Entry 0x014E0898 = OPD (-> func_00A304D0, TOC 0x14ED560) = generischer Functor-Thread-Wrapper (ruft [obj+0x18], dann sys_ppu_thread_exit). Lauf `ct304d0` (CALLTRACE_FROM=A304D0): Functor = 0x007E7F90 -> Thunk auf 0x7E7C6C = Stream-Reader-Loop (Queue obj+0x1A8, Gesamtgroesse obj+0x318, Position obj+0x328). Also ist der Thread nur der Datei-Leser; er "endet" normal (r3=0), kein Fehler.
- Treiber: `0x7E90F0` (Open-Stream, baut Pfad mit ".sgb" 0x1077398, Pool 0x159CEC0) wird vom Sound-Player-Create `func_007D8308` (lr 0x7D844C, ruft vtable-Slot +0x28 des Players) aufgerufen, auf Worker-Thread tid 33 ("p-OmN", Stack 0x8000, ebenfalls Entry 0x014E0898), r5 = 2..8 variiert. Lauf `ct7e90f0` (CALLTRACE_TO=7E90F0): 60x Aufruf, alle aus 7D8308+0xD1E. Weder 7E90F0 noch 7D8308 haben direkte `bl`-Caller (virtuelle Aufrufe) -> Aufrufer der Schleife noch offen.
- SPURS-Folgefehler (nur Lauf 2, spaet, nach Schleifenbeginn): `bad sizeBinary=0`, `dispatch MISS fp=0xDDB604318D2ACB6D size=34704` (SPU-Job ohne lifted Image, DROPPED). In Lauf 1/3 nicht vorhanden -> wahrscheinlich nicht Ursache.
- Hypothese: Sound-Subsystem laedt/spielt zyklisch alle Track-Banks (Preload-Schleife, Worker tid 33), Abschluss-/Ready-Flag der Banks wird nie gesetzt (SPU-Decode/Sound-Job fehlt?) -> Menue wartet. NICHT bewiesen.
- Naechster Schritt (Hyp. 17): (a) `PS3_CALLTRACE_TO=7D8308` -> lr/Aufrufer-Klasse des Players; (b) Vergleich: sind die gleichen sgb-Zyklen im Original-Boot (nur Dialog-Gates ungepatcht) vorhanden? sonst Artefakt der Tutorial-Skip-Patches; (c) Umgehung: Track-Sound-Preload per Datenpatch/HLE ueberspringen (sgh-Open fehlschlagen lassen).
