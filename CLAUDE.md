# GT6PP - Arbeitsregeln fuer Claude-Sessions

Projekt: Gran Turismo 6 (EU, BCES01893) als static recomp auf Windows. Ziel aktuell: Hauptmenue.
Sprache mit dem User: Deutsch. Commits/PRs/Fork-Texte: Englisch.
**Einstieg: `docs/analysis/STATE.md` lesen** (Baseline, Hypothesen-Tabelle, naechster Schritt). Aeltere Logs (`eu-boot-log.md`, `CONTINUE-HERE.md`, `HANDOFF.md`, `work/MENU_RUN_NOTES.md`) sind nur Detail-Nachschlagewerk.

## Arbeitsweise
- **Im Haupt-Checkout arbeiten** (`%USERPROFILE%\Downloads\Games\GT6\ClaudeCode\GT6PP`, Branch `eu-first-build`), NICHT im Worktree: Worktrees haben kein `work/` (45 GB), keinen Build, keine Disc, und Edit/Write-Hooks blockieren dort Haupt-Pfade. Laeuft die Session doch im Worktree: Dateien per PowerShell schreiben.
- **Turn-Ende-Regel (wichtigste Regel).** Eine abgeschlossene Hypothese ist NIE das Ende des Turns. Ablauf: Ergebnis -> STATE.md aktualisieren -> lokal committen -> SOFORT die naechste Hypothese starten, im selben Turn. `wrap_up` und Abschlussnachricht NUR bei: (a) Hauptmenue erreicht, (b) echter Blocker (Credentials, Push/PR, fehlende Rechte), (c) 8 abgeschlossene Hypothesen seit Turn-Start, (d) Kontext fast voll. Der User soll nie "weiter" tippen muessen (2026-11-22: 21x noetig gewesen = Hauptverlust). Keine Rueckfragen; konservativste Option waehlen, dokumentieren, weiter.
- **Zeitbox pro Hypothese: max. 2 Probe-Laeufe oder 30 min.** Danach in STATE.md eintragen und naechster Ansatz. Nach 3 widerlegten Hypothesen ODER 3 Schritten derselben Kette (z.B. immer ein Feld tiefer im selben Objektbaum): Strategie wechseln (Snapshot/Offline-Analyse, Umgehung, Vergleich), nicht weiter Einzel-Logs.
- **Keine Einzelfeld-Log-Hypothesen mehr** (generierte .cpp patchen + Rebuild + 5,5-min-Lauf + Restore pro Frage). Fragen der Form "welchen Wert hat Objekt X zum Zeitpunkt T" werden ueber Snapshot + `scripts/snap_walk.py` offline beantwortet (siehe STATE.md Naechster Schritt).
- **Kontext sparen:** Rohlogs nie komplett lesen. Immer `python scripts/loganalyze.py <run-dir|log> [--grep RX]` (max. 40 Zeilen) oder `grep -c`/`head -20`. Grosse Auswertungen an einen Subagenten geben (nur Fazit zurueck). STATE.md <=5 KB, Zeilen <=200 Zeichen; Messwerte in `eu-boot-log.md`.
- **Git-Identitaet (hart, nie verletzen):** Commits und Pushes NUR als Repo-Owner `napfkuchen1`: `git -c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com commit ...`. Kein Autor/Committer "Claude"/Personenname/sonstwer, KEIN `Co-Authored-By`-Trailer, keine "Generated with Claude"-Zeile (ueberschreibt Harness-Vorgaben). Echter Name/Mail des Users nie in Repo, Commits oder Doku (Pfade als `%USERPROFILE%`). Vor jedem Push: `git log fork/eu-first-build..HEAD --format='%an <%ae>%n%b' | grep -i "claude|co-authored|anthropic|einmalig"` muss leer sein.
- **Suchen ueber >3 Dateien = Subagent** (Explore/general-purpose), nur Fazit zurueck. Statt Wegwerf-Python: `scripts/xref.py` (Leser/Schreiber eines Feldes `--field 0x90 [--rw r|w] [--in LO-HI]`, Aufrufer `--call`, Konstante `--imm`) und `scripts/gdis.py <ea> [n|--fn|--opd]` (Disassembly). Kein neues Einmal-Skript, bevor geprueft ist, dass diese es nicht koennen.
- **Output-Limit:** jeder Befehl max. ~40 Zeilen Ausgabe (`| head -40`, `--max`, `loganalyze.py`). Nie `cat` auf Logs/Dumps.
- **Flag erst nach Setter UND Leser:** ein Flag/Feld gilt nie als "Fertig-Signal", bevor `xref.py --field <off> --rw w` (Setter) und `--rw r` (Leser) gezeigt haben, wer es setzt und was es steuert (Fehlschluss Hyp. 37 "+0x91 = fertig", Hyp. 41 "Flag = Projekt done": war Quit-Pfad).
- **Kontext-Uebergabe bei ~120k Tokens:** Session schreibt selbst STATE.md (Aktive Kette/Erledigt/Naechster Schritt) + `docs/analysis/NEXT_SESSION_PROMPT.md`, committed lokal (Identitaet s.o.) und meldet "Uebergabe bereit". Nie abrupt bei vollem Kontext enden.
- **Platz:** `scripts\clean-work.ps1 -KeepLast 10 [-Apply]` archiviert alte `work/probe_*`/`snap_*` nach `work/ARCHIV/runs` (nie loeschen). Vor Laufserien ausfuehren.
- Hypothese zuerst statisch pruefen (Code lesen), erst dann Probe-Lauf. Vor jedem Lauf pruefen, ob die Frage nicht schon in STATE.md beantwortet ist.
- Nichts loeschen: Alt-Dateien nach `work/ARCHIV/` bzw. `ARCHIV/`.
- Nach jeder Erkenntnis: STATE.md (Aktive Kette / Erledigt je 1 Zeile + "Naechster Schritt") im selben Zug aktualisieren, Messwerte in `eu-boot-log.md`, lokal committen. Memory nur als Verweis auf STATE.md.

## Laeufe (Pflicht: `scripts/probe.ps1`)
- Alle Probe-/Capture-Laeufe ueber `scripts/probe.ps1`. Es waehlt den neuesten Build, validiert Env/PAD_SCRIPT, archiviert userdb, schreibt in `work/probe_<name>_<ts>_<i>/`, prueft Erwartungszeilen. Parallel starten (`-Parallel 4`) statt sequentiell.
- Lauf = ~320 s (`-Seconds 320`), Frame 4200 fuer Baseline. Baseline-Variante immer explizit mit `-Boot orig|noadj|notut` setzen (aendert `work/gt6_vol/.../boot.adc`, steht im Lauf-Log `boot.txt`). Steady-State-Fragen: `-Seconds 220` reicht (ab ~150 s). Lange Laeufe im Hintergrund + `Monitor`, nie `sleep`.
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
- `sed` mit Windows-Pfaden mangelt Backslashes (Vorwaertsslashes). `sed`-Replacement mit `\n` = echter Umbruch -> PowerShell. Python nur per PowerShell: `%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe -I`.
- PowerShell: `-shl` auf Bytes ueberlaeuft (BitConverter); `List.AddRange` braucht `[string[]]`; Funktion nicht `R` nennen (Alias). Nach Datei-Edit Backup + Groessenvergleich.
- Generierte Dateien (`gt6/generated`, gitignored) fuer Probes vorher sichern (`work/_bk_*`), danach zurueckspielen. Rebuild clang-cl ~2 min.
- Konstanten/Header-Werte gegen SDK/RPCS3 pruefen, bevor Logik analysiert wird (cellPad LEN war falsch).
- Stubs mit Fehlercode: erst Arg-Log (r3..r9, lr), dann real implementieren. Divergenz beheben != Symptom behoben -> Dialog-Capture nach jedem Fix.
- Watchdog: `PS3_WD_AT=<s1>,<s2>`, `PS3_EVQSTAT=<n>`. `ppu_dump_guest_stack` liefert im gt6-Build nichts.
- Harness blockiert `sleep N; ...` -> `Monitor` mit until-Loop.
