# GT6PP PROGRESS - Checkpoint-Tabelle (Ueberwacher 2026-11-23). EINZIGE Stelle fuer "was laeuft".
Regel: Jede Sitzung traegt nach jedem Probe-Batch EINE Zeile ein (Commit, Build, Checkpoints). Nie ohne Beleg-Lauf. Nur ergaenzen.
Warum: Stand "AdjustScreen + Eingabe geht" (user, 23.11. frueh) ging bei Umstellung auf 1.22 verloren, ohne dass es notiert war.

## Checkpoints (aufsteigend; ein Lauf gilt bis zum ersten FAIL)
C0 Start: boot.txt ok, unresolved=0, kein Crash bis 60 s
C1 Bild: Frame-Capture bei ~60-90 s NICHT schwarz (nicht-schwarz-Anteil >5 %)
C2 AdjustScreen: Capture zeigt Screen-Adjust (Orig-Boot, Variante `orig`)
C3 Eingabe: PAD_SCRIPT-X wird angenommen -> Szene wechselt (Capture danach != C2)
C4 Spinner: GT-Logo + Spinner (bekannter Hang)
C5 Film: Open `PDIPFS/59/FI` im FS-Log (Oracle-Pfad)
C6 Menue: gtmode-Hauptmenue-Frame

## Referenzstaende
- `ref-1.00-adjust-ok` (git tag auf 44085a5): 1.00-Linie, Hooks vorhanden. Erreicht C0-C4 (user live 10:46 + Probes). Nachbau: `git worktree add ..\ref100 ref-1.00-adjust-ok` ODER ARCHIV/v100 (Quelle) + ARCHIV/old-builds.
- Oracle RPCS3 (Game 1.22): erreicht C6.

## Lauf-Tabelle (neueste unten; Spalten: Datum | Commit | Linie | Boot | C0 C1 C2 C3 C4 C5 C6 | Lauf-Ordner | Notiz)
2026-11-23 | 44085a5 | 1.00 | orig | ok ok ok ok ok -- -- | (Live user, work/padlog_20261123_104620.txt) | Referenz, Spinner = Hang
2026-11-23 | a2b97c2 | 1.22 | noadj | ok FAIL - - - - - | probe_hk122 | schwarz, Script-Hooks/Menue-Pump fehlen -> REGRESSION ggue. Referenz
2026-11-23 | ee62bbc | 1.22 | noadj | ok FAIL - - - - - | probe_lang122_20261123_161107_1 | non-black=n/a lang=en-gb
2026-11-23 | ee62bbc | 1.22 | orig | ok FAIL - - - - - | probe_pump122_20261123_161949_1 | non-black=0%
2026-11-23 | ee62bbc | 1.22 | orig | FAIL - - - - - - | probe_pump2_20261123_162746_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_pump3_20261123_162956_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_pump4_20261123_163140_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | ok FAIL - - - - - | probe_pump5_20261123_163320_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_lax_20261123_163545_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_qlr_20261123_163922_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | ok FAIL - - - - - | probe_qlr2_20261123_164059_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | ok FAIL - - - - - | probe_ww_20261123_164516_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_ww2_20261123_164706_1 | non-black=n/a lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_lst_20261123_165151_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | FAIL - - - - - - | probe_ct_20261123_165727_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | 1.22 | orig | ok FAIL - - - - - | probe_ev_20261123_170710_1 | non-black=0% lang=en-gb
# Notiz 1.00-Referenz: Live (padlog_20261123_104620) erste Pad-Eingabe bei ~59 s -> AdjustScreen schon vor ~55 s sichtbar; Probe-Capture dort Frame 4200 = 320-420 s (Frame-Zaehler != Sekunden).
2026-11-23 | 3f16db4 | 1.22 | orig | ok FAIL - - - - - | probe_b2_20261123_171116_1 | non-black=n/a lang=en-gb
