# GT6PP - Arbeitsregeln fuer Claude-Sessions

Projekt: Gran Turismo 6 (EU, BCES01893) als static recomp auf Windows. Ziel aktuell: Hauptmenue.
Sprache mit dem User: Deutsch. Commits/PRs/Fork-Texte: Englisch.
**Einstieg: `docs/analysis/STATE.md` lesen** (Baseline, Hypothesen-Tabelle, naechster Schritt). Aeltere Logs (`eu-boot-log.md`, `CONTINUE-HERE.md`, `HANDOFF.md`, `work/MENU_RUN_NOTES.md`) sind nur Detail-Nachschlagewerk.

## Arbeitsweise
- **Im Haupt-Checkout arbeiten** (`C:\Users\Daniel\Downloads\Games\GT6\ClaudeCode\GT6PP`, Branch `eu-first-build`), NICHT im Worktree: Worktrees haben kein `work/` (45 GB), keinen Build, keine Disc, und Edit/Write-Hooks blockieren dort Haupt-Pfade. Laeuft die Session doch im Worktree: Dateien per PowerShell schreiben.
- **Autonom weitermachen.** Keine Rueckfragen und keine `wrap_up`-Fragen zwischen Schritten. Nur fragen bei echtem Blocker, Credentials, Push/PR/Commit auf Remote. Konservativste sinnvolle Option waehlen, dokumentieren, weiter.
- **Zeitbox pro Hypothese: max. 2 Probe-Laeufe oder 30 min.** Danach in STATE.md als widerlegt/offen eintragen und den naechsten Ansatz nehmen. Nach 3 widerlegten Hypothesen in Folge: Strategie wechseln (Umgehung/Vergleich) statt weiter bohren.
- Hypothese zuerst statisch pruefen (Code lesen), erst dann Probe-Lauf. Vor jedem Lauf pruefen, ob die Frage nicht schon in STATE.md beantwortet ist.
- Nichts loeschen: Alt-Dateien nach `work/ARCHIV/` bzw. `ARCHIV/`.
- Nach jeder Erkenntnis: STATE.md (Hypothesen-Tabelle + 1 Zeile "Naechster Schritt") im selben Zug aktualisieren, Details in `eu-boot-log.md`. Memory nur als Verweis auf STATE.md.

## Laeufe (Pflicht: `scripts/probe.ps1`)
- Alle Probe-/Capture-Laeufe ueber `scripts/probe.ps1`. Es waehlt den neuesten Build, validiert Env/PAD_SCRIPT, archiviert userdb, schreibt in `work/probe_<name>_<ts>_<i>/`, prueft Erwartungszeilen. Parallel starten (`-Parallel 4`) statt sequentiell.
- Lauf = ~320 s (`-Seconds 320`), Frame 4200 fuer Baseline. Lange Laeufe im Hintergrund + `Monitor`, nie `sleep`.
- Auswertung erst, wenn die erwartete Probe-Zeile im Log steht. Fehlt sie: Lauf ungueltig (falsches Binary / Env nicht gesetzt), nicht "Hypothese widerlegt".
- Seltene Treffer (Logs/Captures) nie ueberschreiben; Ausgabeordner immer mit Zeitstempel.
- Detektoren gegen Log-Reihenfolge pruefen, Treffer per Frame-Capture verifizieren (Falsch-Positiv: `arcade.mpackage` laedt in jedem Boot vor LanguageSelectRoot).

## Fallen (alle schon einmal passiert)
- `run-gt6.ps1`/`cap-gt6.ps1` ohne `GT6_BUILD_DIR` = altes `gt6\build\gt6.exe`. Aktuell gilt `gt6\build-clangcl\gt6.exe`. `probe.ps1` setzt das selbst.
- `PAD_SCRIPT` strikt `<sek>:0x<hexmaske>` (CROSS=0x4000, DOWN=0x0040). Namen/ohne 0x ergeben 0/oktal. Im Log `press 0x....` pruefen.
- `PS3_HEADLESS` ist Praesenz-Flag (auch `"0"`), verhindert RSX-Captures -> Variable entfernen.
- `-Env`-Werte nie mit Komma (cap-gt6 trennt dort). In probe.ps1 ist Trenner `;`.
- `PS3_CALLTRACE=N` fuellt sofort -> immer `PS3_CALLTRACE_AFTER=200`. CALLTRACE sieht nur indirekte Calls. Heap-Adressen aendern sich pro Lauf: Filter nie aus altem Lauf uebernehmen.
- Probes im Hot-Path (5D9B68, jeder Tick): Zaehlerlimit + Filter VOR fprintf, sonst wird Zielframe nicht erreicht.
- RPCS3 `--no-gui` haengt im Shader-Precompile (>240 s) -> nicht als Orakel nutzen; `log.yml` wirkungslos; ISO-Pfad in Anfuehrungszeichen.
- `sed` mit Windows-Pfaden mangelt Backslashes (Vorwaertsslashes). `sed`-Replacement mit `\n` = echter Umbruch -> PowerShell. Python nur per PowerShell: `C:\Users\Daniel\AppData\Local\Programs\Python\Python313\python.exe -I`.
- PowerShell: `-shl` auf Bytes ueberlaeuft (BitConverter); `List.AddRange` braucht `[string[]]`; Funktion nicht `R` nennen (Alias). Nach Datei-Edit Backup + Groessenvergleich.
- Generierte Dateien (`gt6/generated`, gitignored) fuer Probes vorher sichern (`work/_bk_*`), danach zurueckspielen. Rebuild clang-cl ~2 min.
- Konstanten/Header-Werte gegen SDK/RPCS3 pruefen, bevor Logik analysiert wird (cellPad LEN war falsch).
- Stubs mit Fehlercode: erst Arg-Log (r3..r9, lr), dann real implementieren. Divergenz beheben != Symptom behoben -> Dialog-Capture nach jedem Fix.
- Watchdog: `PS3_WD_AT=<s1>,<s2>`, `PS3_EVQSTAT=<n>`. `ppu_dump_guest_stack` liefert im gt6-Build nichts.
- Harness blockiert `sleep N; ...` -> `Monitor` mit until-Loop.
