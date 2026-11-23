# 1.00-Linie (archiviert 2026-11-23)
Bis 2026-11-23 lief das Projekt auf Game v1.00 (Disc-Basis EMAIN 8843160 B, GT6.N). Seitdem einzige Linie: Game v1.22 + ps3recomp v0.20.
Archiviert unter `ARCHIV/v100/` (nur Nachschlagen/Portieren, nie bauen):
- `gt6/generated` (1.00-Lift, 75538 Fn), `gt6/build-v020` (letzter 1.00-Build), `work/bin` (1.00-ELF, SHA ACB00C19..), `work/emain_analysis`
- `src/stubs_100.cpp` (stubs.cpp mit 1.00-Menue-Pump func_00568658), `src/gen` (1.00-SPU-Registry), `scripts/` (relift/gen-functions/lift-spu-gt6/build-gt6), `inputs100.json`
Funktionierende 1.00-Hooks (zum Portieren, Anker per Muster): PFS-Cache-Fill b5b260, ZWAP-Gate, MGOM.start-Pump (Hyp. 39/42), a3-Titelfarbe, boot.adc-Gates, SPURS-Job-Walker, AdjustScreen (cellFiber WaitFlag REALFLAG). Adress-Mapping 1.00->1.22: `tools/map_funcs.py`.
Befunde 1.00: Hauptmenue nie erreicht; nach AdjustScreen GT-Logo+Spinner = Deadlock (37 Threads geparkt, 29 in sys_lwcond_wait, Loader 9qstY wartet). Widerlegt: Pad/Dialog-Kette, Exit-Race, PRIO_START/LOCKSTEP/RESV_OFF, fresh db, PDIPFS-Daten fehlen, Sysmodule/Savedata-Divergenz.
Oracle-Diff: PDIPFS/9-Opens = RPCS3 bis EE/3C; danach RPCS3 59/FI (Movie), wir 85/H2... Entscheidung nach EE/3C offen.
Weitere Details: `docs/analysis/eu-boot-log.md`, `STATE_full_2026-11-22.md`.
