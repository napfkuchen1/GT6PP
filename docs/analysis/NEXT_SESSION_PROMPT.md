Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit11. Teardown = Folge. Baseline fuer Probes: `probe.ps1 -Hdd0Src work\gt6_hdd0_rp -Env "PS3_LANG=en-gb;PS3_GAMEDATA_ROOT=<abs work/_gd_empty>"` (altes gamedata/ von 22.11. verfaelscht Save-Pfad). scripts/opendiff.py <run-dir> vergleicht Opens mit Oracle.
Naechster Schritt: Erste Abweichung: Oracle ruft nach 9/7N/XG 3x cellSaveDataAutoLoad2 GAME6 (je -4), dann sysmodule 0xF044 + sceNpTrophyInit. Wir: GAME6, BKUP6, dann Term (nie F044/Trophy). Wer erzeugt Request fuer BKUP6 (dirName inline obj+0x70, Result obj+0xB0, Worker AF0B94/AF5704, Wrapper AF50B8.. nie gerufen)? Statisch: xref --field 0x70 an Request-Erzeuger/Aufrufer 0089Bxxx-008A4xxx; sonst Snapshot-Walk. Regel: Retry-Zaehler/Fehlerstatus-Quelle finden, Return von AutoLoad2 gegen Oracle (0x8002b401) bleibt gleich.
Nicht wiederholen: A2F290/Teardown/finalize-Skip; GT6_SAVE_CBRES, PS3_SYSCACHE_PLAIN, PS3_MEM_AVAIL_REAL (alle negativ, Knobs in third_party); VMPageFile-Trigger (Folge von Page-Faults).
Laeuft noch: nichts.
Lesen: STATE.md, eu-boot-log.md "Arbeit11".
