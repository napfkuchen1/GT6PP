Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit10 (Commit siehe git log). Term = C++-Projekt-Teardown (PDINetwork.finalize 9AD1DC) synchron in tid1 via 13C44->A52140->A7E6BC->A7BA60->A2FFCC (Step-Schleife, A2F290 Rueckgabe 0-3). Kein Host-Quit, kein Script-Caller. Oracle-main blockiert 76->106 s, kehrt nie zurueck. Draws: 30 Quads nach dialog.mproject, dann 0.
Naechster Schritt: A2F290 lesen (gdis 0xA2F290 120), Rueckgabecodes 0-3 + Abbruchquelle; EIN Lauf mit HOSTBT/Log an A2F290-Rueckgabe (Wert pro Iteration). Regel: liefert A2F290 bei uns 0/1/3 waehrend Oracle-Pfad 2 (wartet) -> Quelle dieses Status (Job/Projekt-Load-Status) per xref --field aufschluesseln; HLE-Rueckgabe zuerst pruefen.
Nicht wiederholen: Z.102-Hypothese, CALLTRACE_TO 1198C, Script-grep nach finalize (0), Save-Varianten.
Laeuft noch: nichts.
Lesen: STATE.md, eu-boot-log.md "Arbeit10".
