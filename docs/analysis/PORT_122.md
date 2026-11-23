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
