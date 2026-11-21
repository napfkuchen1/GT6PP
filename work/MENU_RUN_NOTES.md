# MENU RUN NOTES (Ziel: Hauptmenue-Capture)
Arbeitsverzeichnis: Haupt-Checkout, Branch eu-first-build (Worktree war leer: kein Build/work/Disc).
Befund vor Start (aus Memory/eu-boot-log): Pad funktioniert (ZWAP-Fix); Press auf Sprachdialog -> presents -> legal -> Dialog erneut.
Offen: Dialog verbraucht Pad scheinbar nicht (kein Reader auf listener+0x54); Pointer-Cursor im Dialog.

## Zyklen
- base1: Baseline frame 4200 -> black 87.4%, ops=158 OK (work/cap_base1).
- circ1: PAD_SCRIPT CIRCLE @130s -> Dialog unveraendert (work/cap_circ1). Kein Effekt.
- probes: RWATCH/CALLTRACE auf Pad-Manager: nur A39CD8/A390E4/A395F0 lesen Pad; kein skalarer Konsument im Dialog. Konsument evtl. vektor-basiert oder VM tickt nicht.
- rpcs3-oracle (2 Laeufe, 100s/200s Wait, work/rpcs3_ref/): RPCS3 --no-gui bleibt >240s auf "Precompiling shader interpreter variants" (leerer Balken) -> kein Dialog-Referenzablauf. Hypothese "RPCS3 als Orakel" verworfen (Aufwand/Nutzen).
- rpage: Vektor-faehiger Lesewatch (PPU_RPAGE) -> kein Vektor-Leser im Listener-Block; Hypothese widerlegt. cap_base2 OK (320 s noetig).
- soak-eu: 17/18 identische Boots, 1 Boot nahm Menue-Pfad (arcade/gtmode/garage .mpackage statt LanguageSelect). Hunt 40 Boots 0 Treffer. Race, Ursache offen.

## hunt-par (2026-11-21 abend)
- 4-5 parallele Hunt-Instanzen (16 Kerne) = ~4 Boots/min statt 0.6. Eigene Zeitstempel-Ordner, kein Konflikt.
- Hunt-Skripte setzten PS3_HEADLESS -> "backend init skipped", nie Capture. Var-PRAESENZ zaehlt (="0" reicht nicht). Fix: Remove-Item Env:PS3_HEADLESS.
- "MENU BRANCH HIT" war FALSCH-POSITIV: arcade.mpackage wird in JEDEM Boot (Log-Zeile ~999) VOR LanguageSelectRoot.gpb (~1227) geladen. Detektor sampelt alle 4 s -> manchmal nur arcade sichtbar. hit_menu3 (run17, Frame 4000, 158 draws): Sprachdialog sichtbar, Cursor ja, Zeile-1-Highlight nein. => "seltener Menue-Pfad" widerlegt (frueherer Soak-Treffer vermutlich gleicher Artefakt, Log weg).
- Captures: work/hit_menu3/cap17 (bb0-7.png). Detektor jetzt: nur LanguageSelectRoot; Timeout 300 s ohne Dialog = MENU-Kandidat.

## 2026-11-21 ADCH-Analyse LanguageSelectRoot
onFocusNotify/onActivate gelesen (siehe docs/analysis/eu-boot-log.md). Naechster Schritt: PS3_CALLTRACE_TO=600A50 + PS3_CALLTRACE_AFTER=150. Zyklusbudget ueberschritten, Stopp.
