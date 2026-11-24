Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit14 (letzter Commit bf720f4). Save/Term/NP-Kette komplett widerlegt: mit Oracle-Save (work/_gd_oracle via PS3_GAMEDATA_ROOT, gitignored) laedt AutoLoad2 vollstaendig, sceNp Term (= Shutdown-Beginn) laeuft trotzdem parallel zu den File-Ops. network_available, isNewData, NP-ONLINE: alles ohne Wirkung. Knobs (nur lokal, third_party): GT6_SAVE_ISNEW0, GT6_NP_NOTERM.
Naechster Schritt: Quit-Ausloeser VOR dem main()-Return (0x14010, tid1, 13FD0 Finalizer) finden, nicht Term. `scripts/opendiff.py` Oracle vs ours NACH dem Save-Load: was ruft Oracle als naechstes (Dmux/Pamf/59-FI), was wir stattdessen; welcher Script/Native-Return startet bei uns den Shutdown. Probe: `pwsh -File scripts\probe.ps1 -Boot notut -Hdd0Src work\gt6_hdd0_rp -Seconds 100 -Env "PS3_LANG=en-gb;PS3_GAMEDATA_ROOT=<abs work/_gd_oracle>"` (je Variante eigener pwsh-Start, max 2 parallel).
Nicht wiederholen: LEDGER §4; Save-Prefix/AutoLoad2/isNewData/a8[4], NP-Status ONLINE, Term-Guard, network_available.
Laeuft noch: nichts.
Lesen: STATE.md (letzte 3 Zeilen).
