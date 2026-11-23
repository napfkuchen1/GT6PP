Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Quit ist NUR MASKIERT: main()=0x14010 returnt <12 s (alle Stufen laufen, IsExitGame=0), tid1 parkt dann im Finalizer (p3-Guard AC7418). BFF0A0 (Stufe 1414C) ist nur Init-Launcher. Game laeuft in tid3/Workern. Letzter Commit siehe git log.
Naechster Schritt: Stufen von main() (STATE.md) statisch lesen: welche ist auf echter HW der blockierende Game-Loop und returnt hier sofort? Kandidaten 143E8, 141E8, 146E8, 13DE4, 147BC, 148B4. Entscheidungsregel: Stufe mit Wait/Loop auf Event/Flag -> Flag-Setter per xref.py pruefen; HLE-Writer zuerst ausschliessen. Diagnose: fprintf per Replace in generated ppu_recomp_000.cpp (func_00014010), Backups work/_bk_fdwait.
Nicht wiederholen: LEDGER 1.22 + Quit-Flag/IsExitGame; Skip der AC746C-Wait (-> Teardown 98 Flips); BFF0A0/BFF578/C1F4C8 sind harmlos.
Laeuft noch: nichts. generated clean, Binary traegt Diagnose (APPLOOP/APPMAIN) -> build-all.ps1 vor Baseline.
Lesen: STATE.md.
