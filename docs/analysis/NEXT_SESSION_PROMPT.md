Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit11, Commit bb1e06e (opendiff.py + Diff-Doku). Teardown = Folge (Step 21 Script-Task, main-Return-Finalizer 13FD0), Kette beendet. DATEN-DIFF (scripts/opendiff.py <run-dir>): mit `probe.ps1 -Hdd0Src work\gt6_hdd0_rp` + Env `PS3_LANG=en-gb` folgen unsere Opens dem Oracle bis 9/7N/XG.
Naechster Schritt: Erste echte Abweichung: Oracle oeffnet danach /dev_hdd1/pditsm/pagefile.sys (VMPageFile, Fn B07748, Probe: bei uns 0 Treffer), dann grim2/grim007.db, GT6_1.N. Statisch: `xref.py --call 0xB07748` -> B07EC8/B08A14/B08EA8 -> B08CE8/B090D0/0107D0B4.. aufwaerts bis zur Bedingung/Native; HLE-Rueckgabe (cellFs /dev_hdd1, sysCache, fcntl) zuerst. Wenn Bedingung = Rueckgabewert/Pfad (bei uns /dev_hdd1/cache/BCES01893/ statt /dev_hdd1/) -> HLE fixen, EIN Lauf mit opendiff.
Nicht wiederholen: A2F290-Status/Teardown/finalize-Skip (LEDGER, eu-boot-log Arbeit11); max. 3 neue: Force-2 bringt nichts, Sprache DE war Input-Divergenz, pfs override (9/56/PW) benign.
Laeuft noch: nichts.
Lesen: STATE.md, eu-boot-log.md "Arbeit11".
