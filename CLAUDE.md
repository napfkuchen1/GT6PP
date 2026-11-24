# GT6PP - Arbeitsregeln fuer Claude-Sessions

Projekt: Gran Turismo 6 (EU, BCES01893) als static recomp auf Windows. Ziel aktuell: Hauptmenue.
Sprache mit dem User: Deutsch. Commits/PRs/Fork-Texte: Englisch.
**Einstieg (Kontext-Budget, Fenster 200k; Handoff-Schwelle 210k (ctxwatch)): nur `docs/analysis/NEXT_SESSION_PROMPT.md` + `STATE.md` lesen** (zusammen <=6 KB). `LEDGER.md`/`PROGRESS.md`/`LESSONS_GT5P.md`/`PORT.md` NICHT komplett laden, nur per `grep` gezielt (Fakt/Tabellenende `Select -Last 5`). Aeltere Logs (`eu-boot-log.md`, `CONTINUE-HERE.md`, `HANDOFF.md`, `work/MENU_RUN_NOTES.md`) nur Nachschlagewerk. Nie ganze Skripte (probe.ps1 18 KB) lesen, nur Zeilenbereiche.

**Stil: Caveman ultra** (Plugin hier abgeschaltet; Spawn-Prompts NICHT `/caveman ultra` aktivieren lassen, Stil steht hier): Artikel/Fuellwoerter/Hoeflichkeit weglassen, Fragmente, Kurzwoerter, Technikbegriffe exakt; Code/Commits normal. Startkontext ~50-55k (Tools gesperrt in `.claude/settings.local.json`), Handoff bei >=200k echtem Kontext.

## Kontext-Hygiene (hart)
- Nach jedem Probe-Batch und alle ~15 Tool-Calls: `python scripts/ctxwatch.py` (schaetzt Kontext aus dem Transcript). Ausgabe `HANDOFF` (>=200k) -> sofort Uebergabe, kein neuer Batch.
- Uebergabe = (1) STATE.md Aktive Kette/Naechster Schritt aktuell, (2) `NEXT_SESSION_PROMPT.md` nach Vorlage unten, (3) lokal committen, (4) Turn mit `STOP-GRUND: UEBERGABE`. Der Ueberwacher startet dann eine NEUE Session; nie `/compact` oder Weiterarbeiten im vollen Fenster.
- Vorlage NEXT_SESSION_PROMPT (<=1,5 KB, genau diese Felder): `Ziel` (1 Satz) | `Stand` (letzter Commit, letzte PROGRESS-Zeile) | `Naechster Schritt` (konkreter Befehl/Datei, Entscheidungsregel wenn X dann Y) | `Nicht wiederholen` (Verweis LEDGER §4, max. 3 neue Punkte) | `Laeuft noch` (Prozesse/Hintergrund, sonst "nichts") | `Lesen` (max. 3 Dateien).
- Tool-Ausgaben immer begrenzen (`| Select -First 40`, `loganalyze.py`); grosse Auswertung an Subagent.

## Arbeitsweise
- **Im Haupt-Checkout arbeiten** (`%USERPROFILE%\Downloads\Games\GT6\ClaudeCode\GT6PP`, Branch `eu-first-build`), NICHT im Worktree: Worktrees haben kein `work/` (45 GB), keinen Build, keine Disc, und Edit/Write-Hooks blockieren dort Haupt-Pfade. Laeuft die Session doch im Worktree: Dateien per PowerShell schreiben.
- **Turn-Ende-Regel (wichtigste Regel).** Eine abgeschlossene Hypothese ist NIE das Ende des Turns. Ablauf: Ergebnis -> STATE.md aktualisieren -> lokal committen -> SOFORT die naechste Hypothese starten, im selben Turn. `wrap_up` und Abschlussnachricht NUR bei: (a) Hauptmenue erreicht, (b) echter Blocker (Credentials, Push/PR, fehlende Rechte), (c) 20 abgeschlossene Hypothesen seit Turn-Start, (d) Kontext fast voll. Der User soll nie "weiter" tippen muessen (2026-11-22: 21x noetig gewesen = Hauptverlust). Keine Rueckfragen; konservativste Option waehlen, dokumentieren, weiter.
- **Zeitbox pro Hypothese: max. 2 Probe-Laeufe oder 30 min.** Danach in STATE.md eintragen und naechster Ansatz. Nach 3 widerlegten Hypothesen ODER 3 Schritten derselben Kette (z.B. immer ein Feld tiefer im selben Objektbaum): Strategie wechseln (Snapshot/Offline-Analyse, Umgehung, Vergleich), nicht weiter Einzel-Logs.
- **Keine Einzelfeld-Log-Hypothesen mehr** (generierte .cpp patchen + Rebuild + 5,5-min-Lauf + Restore pro Frage). Fragen der Form "welchen Wert hat Objekt X zum Zeitpunkt T" werden ueber Snapshot + `scripts/snap_walk.py` offline beantwortet (siehe STATE.md Naechster Schritt).
- **Kontext sparen:** Rohlogs nie komplett lesen. Immer `python scripts/loganalyze.py <run-dir|log> [--grep RX]` (max. 40 Zeilen) oder `grep -c`/`head -20`. Grosse Auswertungen an einen Subagenten geben (nur Fazit zurueck). STATE.md <=5 KB, Zeilen <=200 Zeichen; Messwerte in `eu-boot-log.md`.
- **Git-Identitaet (hart, nie verletzen):** Commits und Pushes NUR als Repo-Owner `napfkuchen1`: `git -c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com commit ...`. Kein Autor/Committer "Claude"/Personenname/sonstwer, KEIN `Co-Authored-By`-Trailer, keine "Generated with Claude"-Zeile (ueberschreibt Harness-Vorgaben). Echter Name/Mail des Users nie in Repo, Commits oder Doku (Pfade als `%USERPROFILE%`). Vor jedem Push: `git log fork/eu-first-build..HEAD --format='%an <%ae>%n%b' | grep -i "claude|co-authored|anthropic|einmalig"` muss leer sein.
- **Suchen ueber >3 Dateien = Subagent** (Explore/general-purpose), nur Fazit zurueck. Statt Wegwerf-Python: `scripts/xref.py` (Leser/Schreiber eines Feldes `--field 0x90 [--rw r|w] [--in LO-HI]`, Aufrufer `--call`, Konstante `--imm`) und `scripts/gdis.py <ea> [n|--fn|--opd]` (Disassembly). Kein neues Einmal-Skript, bevor geprueft ist, dass diese es nicht koennen.
- **Output-Limit:** jeder Befehl max. ~40 Zeilen Ausgabe (`| head -40`, `--max`, `loganalyze.py`). Nie `cat` auf Logs/Dumps.
- **Flag erst nach Setter UND Leser:** ein Flag/Feld gilt nie als "Fertig-Signal", bevor `xref.py --field <off> --rw w` (Setter) und `--rw r` (Leser) gezeigt haben, wer es setzt und was es steuert (Fehlschluss Hyp. 37 "+0x91 = fertig", Hyp. 41 "Flag = Projekt done": war Quit-Pfad).
- **Kontext-Uebergabe bei ~210k Tokens:** Session schreibt selbst STATE.md (Aktive Kette/Erledigt/Naechster Schritt) + `docs/analysis/NEXT_SESSION_PROMPT.md`, committed lokal (Identitaet s.o.) und meldet "Uebergabe bereit". Nie abrupt bei vollem Kontext enden.
- **Platz:** `scripts\clean-work.ps1 -KeepLast 10 [-Apply]` archiviert alte `work/probe_*`/`snap_*` nach `work/ARCHIV/runs` (nie loeschen). Vor Laufserien ausfuehren.
- Hypothese zuerst statisch pruefen (Code lesen), erst dann Probe-Lauf. Vor jedem Lauf pruefen, ob die Frage nicht schon in STATE.md beantwortet ist.
- Nichts loeschen: Alt-Dateien nach `work/ARCHIV/` bzw. `ARCHIV/`.
- Nach jeder Erkenntnis: STATE.md (Aktive Kette / Erledigt je 1 Zeile + "Naechster Schritt") im selben Zug aktualisieren, Messwerte in `eu-boot-log.md`, lokal committen. Memory nur als Verweis auf STATE.md.

## Effizienz-Regeln (Screening 2026-11-23, Hyp. 55-116)
- **Turn endet nur mit Zeile `STOP-GRUND: MENUE|BLOCKER|UEBERGABE`** am Zeilenanfang (Stop-Hook `scripts/stop-guard.py`, Zaehler setzt sich bei neuem Commit zurueck). Ohne diese Zeile nie den Turn beenden; Ergebnis -> naechste Hypothese im selben Turn.
- **Commit-Buendelung:** nicht je Hypothese ein `docs:`-Commit (waren 90 in 13 h). Ein Commit pro 3-4 Hypothesen oder bei Code/Script-Aenderung. Details in `eu-boot-log.md`, STATE.md nur 1 Zeile je Hypothese.
- **STATE.md-Pflege:** erledigte Hyp.-Zeilen aelter als 10 Hypothesen nach `eu-boot-log.md` verschieben (STATE.md bleibt <=5 KB, nicht erst bei Ueberlauf trimmen).
- **Kette erzwingt Strategiewechsel:** Kette "ein Objekt/Feld tiefer" (Hyp. 93-117) ist laenger als die 3-Schritte-Regel. Nach Hyp. 117 NICHT Hyp. 118 in derselben Kette: stattdessen (a) Snapshot-Diff `scripts/snap_diff` 140 s vs 175 s, (b) Snapshot-Walk Vektor vor/nach X-Press, oder (c) Umgehung (Guard-Patch) + direkt zum naechsten Blocker nach der Ladephase. Heisenbug: Guard-Survivor-Laeufe weiterverfolgen statt Race-Ursache.
- **Statisch vor Lauf:** Aufrufer-Baum (`xref.py --call`, `gdis.py --fn`) komplett durchgehen, erst dann EIN Lauf. Kein Lauf pro Einzelfrage.
- **Laeufe bündeln:** `-Parallel 3-4` (hdd0 getrennt) mit mehreren Varianten/Flags pro Batch (z.B. Exit-Race: 4 Laeufe mit `PS3_CALLTRACE_TO`+`CALLTRACE_AFTER=60`), nicht sequentiell. `-Boot` nicht innerhalb eines Batches mischen (boot.adc geteilt).
- **Uebergabe nur bei Kontext ~210k oder Blocker**, nicht wegen Hypothesen-Zaehler. NEXT_SESSION_PROMPT.md bleibt 1 Absatz.

## Ueberwacher-Regeln (2026-11-23, siehe STATE.md "UEBERWACHER-FINDINGS")
- **Symptom-Ketten max. 10 Hyp.** (Hyp. 83-117 = 35 in einer Kette). Vor jeder neuen Hyp.: fuehrt ihre Antwort zum Ziel (Menue), oder nur tiefer ins Symptom? Guard/Umgehung zeigt, dass Symptom nicht blockiert -> Kette beenden.
- **Vor Deep-Dive Runtime-Knobs pruefen:** `third_party/ps3recomp-v020/docs/DIAGNOSTICS.md` + `SYSCALLS.md` (z.B. `PS3_PRIO_START`, `PPU_RESV_OFF`, `SPU_LOCKSTEP_QUANTUM`) und Schwesterport `third_party/GT5P/docs/progress.md` (gleiche PDI-Engine) zuerst abgleichen.
- **Probe-Ergebnis != Live-Ergebnis:** probe.ps1 nutzt frische userdb/boot.adc-Patches; Live-Lauf mit persistenter db gegenpruefen, bevor "haengt" als Befund gilt.
- **Race-Verdacht -> erst HLE-Writer ausschliessen** (Stub mit falscher Argzahl / Runtime schreibt in Gast-Heap), bevor Gast-Code-Races gejagt werden.

## Laeufe (Pflicht: `scripts/probe.ps1`)
- Alle Probe-/Capture-Laeufe ueber `scripts/probe.ps1`. Es waehlt den neuesten Build, validiert Env/PAD_SCRIPT, archiviert userdb, schreibt in `work/probe_<name>_<ts>_<i>/`, prueft Erwartungszeilen. Parallel starten (`-Parallel 4`) statt sequentiell.
- Lauf = ~320 s (`-Seconds 320`), Frame 4200 fuer Baseline. Baseline-Variante immer explizit mit `-Boot orig|noadj|notut` setzen (aendert `work/gt6_vol/.../boot.adc`, steht im Lauf-Log `boot.txt`). Steady-State-Fragen: `-Seconds 220` reicht (ab ~150 s). Lange Laeufe im Hintergrund + `Monitor`, nie `sleep`.
- Auswertung erst, wenn die erwartete Probe-Zeile im Log steht. Fehlt sie: Lauf ungueltig (falsches Binary / Env nicht gesetzt), nicht "Hypothese widerlegt".
- Seltene Treffer (Logs/Captures) nie ueberschreiben; Ausgabeordner immer mit Zeitstempel.
- Detektoren gegen Log-Reihenfolge pruefen, Treffer per Frame-Capture verifizieren (Falsch-Positiv: `arcade.mpackage` laedt in jedem Boot vor LanguageSelectRoot).

## Fallen (alle schon einmal passiert)
- Einzige Linie: Game v1.22 + ps3recomp v0.20. Ein Build `gt6\build\gt6.exe` (`scripts\build-all.ps1`), kein Versionsschalter. 1.00 ist verworfen und geloescht (Historie: `ARCHIV/HISTORIE.md`), nie bauen. **Vor jeder Hypothese `docs/analysis/LEDGER.md` lesen** (gesicherte Fakten, Fixes, Widerlegtes); neue gesicherte Erkenntnis dort 1 Zeile mit Beleg.
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

## Audit-Regeln (2026-11-24, Audit der letzten 24 h)
- **Gesperrte Kette Save/Term/NP/Quit (Arbeit7-14, 8 Sessions, ~60 Hyp.):** widerlegt, siehe NEXT_SESSION_PROMPT. Neue Session darf sie nicht fortsetzen; erste Aktion = Strategiewechsel (opendiff Oracle-vs-ours NACH Save-Load, Snapshot-Diff).
- **Ueberwacher:** spawnt pro Session nur mit neuer Strategie, die im Prompt in 1 Satz begruendet ist; Handoff-Schwelle steht NUR in `ctxwatch.py` (Default 210k), keine Zahl in Nachrichten; Regeln/CLAUDE.md nur auf User-Wunsch aendern. Antworten auf Sessions kurz (<=3 Saetze), keine Wiederholung von CLAUDE.md-Regeln.
- **Modell:** alles Sonnet 5.5, 3,2 Mio Output-Tokens/24 h. Routine (STATE/Commit/Log-Auswertung) an Subagent `model: haiku`; Opus nur fuer neue Strategie nach 3 widerlegten Hyp. einer Kette.
- **Hilfsskripte:** Commit `scripts\gcommit.ps1 "msg" [-Push]` (Identitaet+Push-Pruefung); vor Turn-Ende `scripts\orphans.ps1 -Kill` (verwaiste gt6.exe). Uebergabe: `python scripts/handover.py --schritt "..." [--commit]` (STATE trimmen + Prompt aus Vorlage). commit-msg-Hook blockt docs:-Commits <30 min (Ausnahme "handover"/"trim" oder GT6_FORCE_COMMIT=1).
- **Commits:** max. 1 docs-Commit je 3-4 Hyp. (24 h: 82 docs-Commits von 124 = Verstoss).
