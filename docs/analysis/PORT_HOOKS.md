# PORT_HOOKS - 1.00-Hooks (Ref 6697a6d) vs 1.22 (Stand 2026-11-23)
Quelle 1.00: `git show 6697a6d:<pfad>` (ARCHIV/v100 geloescht). 1.22-Anker: tools/port_hooks.py, scripts/post-lift.ps1, gt6/src/stubs.cpp. Details je Adresse: PORT.md.

| Hook | in 1.22? | Anker 1.22 | Wirkung / Beleg |
|---|---|---|---|
| PFS Stream read/seek/tell override | ja (port_hooks p1) | AAAC5C / AAB164 / AAB0B8 | PFS-Dateien aus Host-Cache; generated enthaelt Hooks (Lauf: "pfs override: serving plaintext") |
| FileObject-vtable-Guards | ja | AAA4B0 / AAA530 / AAF354 | NULL-Objekt -> r3=0 |
| Host-Open-Wrapper | ja | AB080C (gt6_orig_func_00AB080C in ppu_recomp_023) | prepare/commit Pfad |
| Script read/path/seek (main.adc-Override) | ja, Fuzzy-Match | A67E1C / A67F60 / A67DC4 | Skript aus Host-Dateien |
| MGOM.start Request + Sync-Pump + Worker-Pump | ja, Fuzzy-Match | 6171D0 / 617218 / AD16AC | Menue-Projekt-Pump (Hyp. 39/42) |
| ctor-Walker / setjmp+guards | ja | 1183C-11880 / C61F88,C620AC | Beleg PORT.md |
| boot.adc-Gates | ja | scripts/patch-boot-adc.py (1.22-Offsets) | Dialoge uebersprungen (notut laeuft bis ProgressDialog) |
| ZWAP-Gate (cellMusicInitialize2 arg2=Zeiger auf CELL_OK) | Host-Seite ja (stubs.cpp:1325) | - | In 1.22-Lauf KEIN cellMusicInitialize2-Aufruf (0 Logzeilen): Gast erreicht den Punkt nie |
| PFS-Cache-Fill b5b260 (userdb-Cache fuellen) | p4 portiert (GT6_NO_CACHEFILL), Probe cf 90 s: kein Effekt (5774 Flips, kein Open) | Kandidat func_00C1FE74: A26510->AE6C34 @C20368, Alloc AE6FE8, obj+0x28/+0x2C/+0x30, B5A944->C1F604 | initUserDB in 1.22 nie erreicht (kein Open userdb0101.dat) -> erst relevant nach Quit-Ursache |
| FileDeviceHost-Flush (A08A74/A08B8C) | JA p3 | AC7418 init / AC75B0 flush | KAUSAL: Quit ~30 s weg (fdf 5769 Flips; GT6_NO_FDFLUSH=1 -> Quit) |
| H113 Guard (A25C64), PackageNullGuard (5F81B0) | NEIN | 1.22-Anker offen | nicht geprueft |
| SPURS-Job-Walker, a3-Titelfarbe, AdjustScreen REALFLAG | unklar | host-seitig (gt6/src, patches/gt6-h46*, gt6-rsx-ignore-stale-a3) | AdjustScreen in 1.22 nie erreicht |

## Befund
Alle Hooks, die den Boot bis zum Savedata-Load tragen, sind in 1.22 aktiv. Die fehlenden (b5b260, ZWAP, SPURS, a3, AdjustScreen) liegen NACH dem aktuellen Quit-Punkt (LOAD complete GAME6) -> Portieren allein loest Quit nicht. Quit-Delta zu 1.00 liegt zwischen LOAD complete und initUserDB/initSound.
