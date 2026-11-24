Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: letzter Commit fbad759 docs: English-only rule for repo content; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Naechster Schritt: tid30 '9qstY' = Game-Loop-Thread (Body via AF0B94 bctrl AF0C28), bei Oracle fuehrt er nach AutoLoad NetStartDialog/Music/Trophy/Sockets aus, bei uns nicht. Per Snapshot (snap_walk.py) tid30 Stack/PC bei 60 s vs Oracle-Aequivalent: wo haengt/loopt er (8A7AD0 Konsumenten-Wait? 616C80 Loop?). Wenn er in 8A7AD0 wartet: Zaehler 0x1d8/0x240 + tid29 Producer 8A88E8 pruefen; sonst Tick-Handler 68FF84 Handler-Tabelle 0x15B242C einzeln auf Rueckgabe pruefen.
Nicht wiederholen: Save/Term/NP/network_available; Main-Loop 146E8 erzwingen (liegt vor AutoLoad, A15_LOOP wirkungslos); 798C1C-State-Force
Laeuft noch: nichts
Lesen: docs/analysis/eu-boot-log.md (Arbeit15 + Arbeit7 Wait-Analyse)
