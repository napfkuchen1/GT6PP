Ziel: Hauptmenue (C6), GT6 EU, Game 1.22 + ps3recomp v0.20.0 (einzige Linie).
Stand: Commits bis "docs: fix line endings" (nach 7259b74). Guard-/ctxfiber-Probes: Gast-Quit nach ~30 s unveraendert, kein Spinner/Null-Call. Doku-Reste + probe.ps1 taskkill erledigt.
Naechster Schritt: Quit-Flag 0x1796DC8 (AD2998, Loop 0x146E8) wird per PPU_WWATCH von keinem Store gesetzt -> ungehookter Writer. Pruefen: fileBuf der 6 cellSaveData-Reads (AutoLoad2 BCJS37016-GAME6, direkt vor sceNp Term) vs 0x1796DC8; wenn Ueberlapp -> Savedata-HLE fixen, sonst Snapshot vor Term + snap_walk.
Nicht wiederholen: LEDGER §4, mempool-HLE, AFDFC0/0x1798F00 (ist Titel-ID-Strcmp, nicht Quit).
Laeuft noch: nichts.
Lesen: STATE.md, NEXT_SESSION_PROMPT.md. Caveman ultra.
