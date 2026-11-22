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
| 14 | Dialog-Update / Script-VM-Tick / Draw-Fokus-Seite | **offen** | Highlight fehlt auch ohne Eingabe; DSP-Probe 5D9B68 [r25]=0 im Steady-State |

## Naechster Schritt (EINER)
1. **Zeitbox 1 h: Dialog umgehen** statt weiter am Pad zu bohren: Aktivierungs-/Sprachwahl-Pfad (ADCH: `onActivate` -> sound + close) per Hook erzwingen, sehen was danach blockiert (Menue-Boot, naechster Blocker).
2. Danach: Boot-Zeit bis Dialog analysieren (wo gehen die ~200 s hin: Asset-Load, Shader, Frames?) -> kuerzere Iteration.
3. Falls Umgehung scheitert: Script-VM-Tick / Draw-Fokus-Seite (Hyp. 14) und M3-Dialog-Rendering.
Optional: US-Disc (BCUS98296) als Gegenprobe, falls Build-Basis vorhanden.

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done, Exit "8/8 identisch" nicht formal erfuellt. M3 (RSX/first frame) offen bis Menue-Frame. Siehe `ROADMAP.md`.

## Aufraeumen 2026-11-22
`work/build*.log` und `work/_db_aside_*` nach `work/ARCHIV/` verschoben (nichts geloescht). `work/_bk_*` bleibt. `probe.ps1` archiviert userdb kuenftig selbst nach `work/ARCHIV/`.
Offen: voller 320-s-Baseline-Lauf mit `probe.ps1` noch nicht gefahren (nur Smoke-Test 20 s).
