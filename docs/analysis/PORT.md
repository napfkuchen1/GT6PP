# PORT_122 - Gast-Adressen 1.00 -> 1.22 (je Patch 1 Zeile + Beleg)
Basis: work/bin/EMAIN.elf (1.00, sha1 fae74cdc84c6d3..). Ziel: work/bin122/EMAIN.elf (1.22, sha1 0e1fc30db223a653..., 23787792 B).
Neu lokalisieren per Signatur/xref (scripts/xref.py, gdis.py); Beleg = Befehl/Lauf.

| Patch | alt (1.00) | neu (1.22) | Beleg |
|---|---|---|---|
| PFS-Cache-Fill (b5b260) | 0xB5B260 | offen | - |
| H113 Guard | 0xA25C64 | offen | - |
| ZWAP-Gate | offen | offen | - |
| MGOM.start Pump (Hyp. 39/42) | offen | offen | - |
| per-fp a3 Titelfarbe | offen | offen | - |
| boot.adc-Gates | Datei (scripts/patch-boot-adc.py) | Datei in 1.22-Daten pruefen | - |
| ctor-Walker (ctor_walk_patch) | func 0x118C8, lr 0x1190C | func 0x1183C, lr 0x11880 | CRT -0x8C; `ctor_walk_patch.py <gen> 0x1183C 0x11880` |
| setjmp / longjmp | 0xB98168 / 0xB9828C | 0xC61F88 / 0xC620AC | env GT6_SETJMP/GT6_LONGJMP; 28 Callsites |
| code-end (Lift) | 0xF908C4 | 0x10B8154 | letzter OPD-Funktionsstart |
| memset Duff-Einsprung (computed entries) | A4FDE0.. A4FE68.. A4FEEC.. | B118E0..B1191C, B11968..B119A0, B119E8..B11A20, B11A64..B11A9C | Probe v122b: `unresolved indirect call -> 0xB11A04` (bctr B118DC/B11964/B119E4); `add_computed_entries.py <json> 122` |
| Mapper 1.00->1.22 | tools/map_funcs_122.py | 20 eindeutig (u.a. 9F8E40->AB080C, A12170->AD1670, A26510->AE6C34, B5A944->C1F604) | Rest "none": Code geaendert, anderes Matching noetig |
| setjmp-Guards (add_setjmp_guards) | 16 Funktionen (scan, adressfrei) | 16 Funktionen | `scripts/post-lift-122.ps1`; Probe v122e: `depth overflow` 113 -> 0 |
| Probe-Stand build-v122 (orig, 150 s) | Game-Loop ~9480 Flips | gleich, 0 unresolved, Frame 4200 schwarz | v122d/v122cap/v122e; Hooks (Script/BootPresents/Pump) noch nicht portiert; SPU-fp 1.22 ohne lifted image (5x) |
| SPU | 16 Job-Images per fp-Scan, PM id5 byteidentisch @0x14DAA80, 1 Embedded-ELF @0x1346280; Ausgabe gen122 + gt6-122/generated/spu_lifted; CMake GT6_V122 schaltet GT6_SPU_GEN/LIFT | fertig, 0 MISS |
