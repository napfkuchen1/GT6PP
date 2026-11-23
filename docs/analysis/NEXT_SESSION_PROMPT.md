Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Game-Loop 1.22 = 0x616C80 (tid30 via 6170AC, Tick 68FF84) LAEUFT, zeigt nur Legal/Logo (C1 FAIL, wie 1.00-Stand). main()-Rueckkehr legitim. Quit nur maskiert (p3-Guard). Letzter Commit: git log.
Naechster Schritt: Strategiewechsel (STATE.md): Snapshot-Diff 100 s vs 140 s ODER Umgehung 8A88DC/C45408-Wait (Timeout kurz) -> steigt Zaehler 1d8 / Draws? Tick-Handler-Tabelle 0x15B242C, tid29 Produzent, tid30 Konsument (snap work/snap_a7).
Nicht wiederholen: AFDFC0/strcmp; AC746C-Wait-Skip; "Loop startet nie" (widerlegt); LEDGER Quit-Flag/IsExitGame.
Laeuft noch: nichts. generated clean (Diagnose-Backup work/_bk_a7 nur Kopie), Binary traegt A7-Logs -> build-all.ps1 -Force nicht noetig, generated ist zurueckgespielt: Binary neu bauen.
Lesen: STATE.md, PORT_HOOKS.md.
