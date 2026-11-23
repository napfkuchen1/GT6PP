Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Game-Loop 1.22 = 0x616C80 (tid30 via 6170AC, Tick 68FF84) LAEUFT, zeigt nur Legal/Logo (C1 FAIL, wie 1.00-Stand). main()-Rueckkehr legitim. Quit nur maskiert (p3-Guard). Letzter Commit: git log.
Naechster Schritt: Tick 68FF84 (1.00-Gegenstueck 5C406C, Methodentabelle 145D0D4, Handler4 5B97A0 Jobliste vtbl+0x120==3) statisch auf 1.22 mappen (xref/gdis, SNAP_ELF=work/bin/_t100.elf fuer 1.00); Objekte = *(r28+0x1d4+4i), Done-Byte +0x96. Dann Snapshot+snap_walk.py: Zustand obj+0x88 und Jobliste. Wenn Jobs nie fertig: SPURS soc-job-Completion pruefen (1.00 Hyp. 45).
Nicht wiederholen: AFDFC0/strcmp; AC746C-Wait-Skip; "Loop startet nie" (widerlegt); LEDGER Quit-Flag/IsExitGame.
Laeuft noch: nichts. generated clean (Diagnose-Backup work/_bk_a7 nur Kopie), Binary traegt A7-Logs -> build-all.ps1 -Force nicht noetig, generated ist zurueckgespielt: Binary neu bauen.
Lesen: STATE.md, PORT_HOOKS.md.
