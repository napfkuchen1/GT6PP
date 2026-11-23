Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Quit nur maskiert (p3-Guard parkt tid1). main()=0x14010 kehrt <12 s zurueck, Main-Loop 146E8 lief 0 Iterationen: Task AFDFC0 = legitimer Boot-Check (strcmp BCES01893), kein Fehler. Flips ~5770 = Runtime-Ticker, Game zeichnet nicht (1 Draw, C1 FAIL). Letzter Commit: git log.
Naechster Schritt: 1.22-Gegenstueck des 1.00-Game-Loops 0x568800 finden (Signatur aus work/bin/_t100.elf, Aufrufer AF9350-Tick/cb 0x16CD0C0-0x2F40; 1.00-Quelle `git show 6697a6d:<pfad>`, PORT_HOOKS.md). Wer haelt main auf HW nach 146E8 am Leben (Stufen 141E8/91E464/1414C, 10338->1096C->13FD0)? Statisch (xref.py/gdis.py), dann EIN Lauf mit Capture (-Seconds 90). Wenn Loop nie startet: fehlenden Starter/Hook portieren.
Nicht wiederholen: AFDFC0/strcmp-Kette; AC746C-Wait-Skip; BFF0A0/BFF578/C1F4C8 harmlos; LEDGER Quit-Flag/IsExitGame.
Laeuft noch: nichts. generated clean, Binary mit Diagnose -> zuerst scripts\build-all.ps1.
Lesen: STATE.md, PORT_HOOKS.md.
