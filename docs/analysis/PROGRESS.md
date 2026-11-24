# GT6PP PROGRESS - Checkpoint-Tabelle. EINZIGE Stelle fuer "was laeuft". Linie: nur Game 1.22 + ps3recomp v0.20.0.
Regel: nach jedem Probe-Batch EINE Zeile (checkpoints.py), nie ohne Beleg-Lauf, nur ergaenzen. Ungemessene Laeufe (kein Capture) keine Zeile.
Warum: Stand "AdjustScreen + Eingabe geht" (user, 23.11. frueh, damalige Altlinie) ging bei Umstellung auf 1.22 verloren, ohne notiert zu sein.

## Checkpoints (aufsteigend; ein Lauf gilt bis zum ersten FAIL)
C0 Start: boot.txt ok, unresolved=0, kein Crash bis 60 s
C1 Bild: Frame-Capture bei ~60-90 s NICHT schwarz (nicht-schwarz-Anteil >5 %)
C2 AdjustScreen: Capture zeigt Screen-Adjust (Boot-Variante `orig`)
C3 Eingabe: PAD_SCRIPT-X wird angenommen -> Szene wechselt (Capture danach != C2)
C4 Spinner: GT-Logo + Spinner (bekannter Hang)
C5 Film: Open `PDIPFS/59/FI` im FS-Log (Oracle-Pfad)
C6 Menue: gtmode-Hauptmenue-Frame
Oracle RPCS3 (Game 1.22) erreicht C6. Unsere 1.22-Laeufe: bisher alle FAIL bei C1.

## Lauf-Tabelle (neueste unten; Datum | Commit | Boot | C0 C1 C2 C3 C4 C5 C6 | Lauf-Ordner | Notiz)
2026-11-23 | ee62bbc | orig | ok FAIL - - - - - | probe_pump122_20261123_161949_1 | non-black=0%
2026-11-23 | 86302b5 | orig | ok FAIL - - - - - | probe_pump5_20261123_163320_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | FAIL - - - - - - | probe_lax_20261123_163545_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | FAIL - - - - - - | probe_lst_20261123_165151_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | FAIL - - - - - - | probe_ct_20261123_165727_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | ok FAIL - - - - - | probe_ev_20261123_170710_1 | non-black=0% lang=en-gb

2026-11-23 | 3e76e25 | orig | ok FAIL - - - - - | probe_ctxf_20261123_172901_1 | non-black=0% lang=en-gb
2026-11-23 | 3e76e25 | orig | ok FAIL - - - - - | probe_ctxf2_20261123_173240_1 | non-black=0% lang=en-gb
2026-11-23 | c9a73e1 | notut | ok FAIL - - - - - | probe_fdfcap_20261123_200537_1 | non-black=0%
2026-11-23 | 0b8601d | notut | ok FAIL - - - - - | probe_a7snap_20261123_232734_1 | non-black=0%
2026-11-23 | d95be11 | notut | ok FAIL - - - - - | probe_a7base_20261123_233943_1 | non-black=0%
2026-11-23 | d95be11 | notut | ok FAIL - - - - - | probe_a7nowait_20261123_234129_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8hdd_20261123_235046_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8s50_20261123_235312_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8emptyok_20261123_235811_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8nodata_20261123_235811_1 | non-black=0%
2026-11-24 | 1e49628 | notut | ok FAIL - - - - - | probe_a8cbres_20261124_000147_1 | non-black=0%
2026-11-24 | 5225c7f | notut | ok FAIL - - - - - | probe_a8ct1_20261124_003117_1 | non-black=0%
2026-11-24 | 5225c7f | notut | ok FAIL - - - - - | probe_a8ct2_20261124_003117_1 | non-black=0%
2026-11-24 | 5aa66da | notut | ok FAIL - - - - - | probe_a10_draw_20261124_011603_1 | non-black=0%
