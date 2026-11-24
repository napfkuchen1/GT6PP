Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit12 (Commit siehe git log). AutoLoad2-Return/Callback identisch zu Oracle (-4, CBRES egal). GAME6 und BKUP6 sind 2 getrennte Mgr-Objekte (ctor AF5528 aus 89D07C). Baseline: `probe.ps1 -Boot notut -Hdd0Src work\gt6_hdd0_rp -Env "PS3_LANG=en-gb;PS3_GAMEDATA_ROOT=<abs work/_gd_empty>"`.
Naechster Schritt: Aufrufer der Funktion um 89CF10..89D07C finden (`gdis.py 0x89CF10 --fn`, `xref.py --call <fn-start>`), Kette bis zum Save-Controller; dort Retry-Zaehler/Dirname-Wahl (Format 0x11a-Strings, GAME vs BKUP) vs Oracle (3x GAME6 je -4, dazwischen nur pagefile.sys-Recreate) pruefen. Probe-Tools: work/_bk_a12/patch*.py (Entry-Log in ppu_recomp_023.cpp; vor Lauf Backup, danach work/_bk_a12/*_clean.cpp zurueck).
Nicht wiederholen: LEDGER §4; Arbeit12: AF5xxx-Callback/Return, 0x8256xx (NP-Update), CBRES.
Laeuft noch: nichts.
Lesen: STATE.md, eu-boot-log.md "Arbeit12".
