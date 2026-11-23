Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Lift = 1.22 (EMAIN.SELF 9209104 B = RPCS3). Game-Loop 616C80/tid30 + Tick 68FF84 laufen, Pacing 63 Hz ok, Spiel idle nach Legal/Logo (C1 FAIL, 100 s: 32 Draws, 139 fs-open). Letzter Commit: git log.
Naechster Schritt: (1) Save-Prefix: RPCS3 ruft cellSaveDataAutoLoad2 (SECUREFILE GT6_1.0), wir nie (0 Log) und oeffnen GT6.N aus work/gt6_hdd0. Pruefen wer den Prefix 'GT6' liefert (Config-Lookup @85360, Key 0x10e6318) und warum wir AutoLoad2 nicht erreichen; ein Lauf mit leerem hdd0 (-Hdd0Src leer) + PS3_HLE_TOP. (2) sonst Snapshot-Diff 60 s vs 100 s (snap_walk threads/sync). Snap work/snap_a7.
Nicht wiederholen: AFDFC0/strcmp; tid29/30 Pacing (ok); "Loop startet nie"; Versions-Divergenz (geklaert).
Laeuft noch: nichts. Binary traegt A7-Diagnose (generated clean): build-all.ps1 vor Lauf.
Lesen: STATE.md, PORT_HOOKS.md.
