Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Quit ~30 s GELOEST durch port_hooks p3 (FileDeviceHost-Flush AC7418/AC75B0, GT6_NO_FDFLUSH=1 = alt). 90 s: ~5770 Flips, kein Teardown. Capture Frame 3500 schwarz (1 Draw). p4 (b5b260 cache-fill) kein Effekt. Letzter Commit c9a73e1.
Naechster Schritt: schwarzes Bild/Ladephase: warum nur 1 Draw, kein 59/FI-Open, cellMusicInitialize2 nie gerufen. Statisch Aufrufer-Baum, dann Probe -Seconds 90. PackageNullGuard 5F81B0: 1.22-Anker per Signatur aus work/bin/_t100.elf suchen; H113 A25C64: kein 1.00-Code im git (nur PORT.md "offen") -> verwerfen.
Nicht wiederholen: LEDGER 1.22 (Quit-Flag, userdb, savedata, sceNp) + Quit-Jagd; SPURS/a3/AdjustScreen erst nach Ladephase.
Laeuft noch: nichts. ppu_recomp_022 tragen noch [SETST]-Diagnose (work/_bk_022; _bk_023 vor p3 neu patchen).
Lesen: STATE.md, PORT_HOOKS.md.
