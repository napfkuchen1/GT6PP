# PORT_122 - guest addresses 1.00 -> 1.22 (one line per patch + evidence)
Base: work/bin/EMAIN.elf (1.00, sha1 fae74cdc84c6d3..). Target: work/bin122/EMAIN.elf (1.22, sha1 0e1fc30db223a653..., 23787792 B).
Re-locate by signature/xref (scripts/xref.py, gdis.py); evidence = command/run.

| Patch | old (1.00) | new (1.22) | Evidence |
|---|---|---|---|
| PFS cache fill (b5b260) | 0xB5B260 | open | - |
| H113 guard | 0xA25C64 | open | - |
| ZWAP gate | open | open | - |
| MGOM.start pump (Hyp. 39/42) | open | open | - |
| per-fp a3 title color | open | open | - |
| boot.adc gates | file (scripts/patch-boot-adc.py) | check file in 1.22 data | - |
| ctor walker (ctor_walk_patch) | func 0x118C8, lr 0x1190C | func 0x1183C, lr 0x11880 | CRT -0x8C; `ctor_walk_patch.py <gen> 0x1183C 0x11880` |
| setjmp / longjmp | 0xB98168 / 0xB9828C | 0xC61F88 / 0xC620AC | env GT6_SETJMP/GT6_LONGJMP; 28 callsites |
| code end (lift) | 0xF908C4 | 0x10B8154 | last OPD function start |
| memset duff entry (computed entries) | A4FDE0.. A4FE68.. A4FEEC.. | B118E0..B1191C, B11968..B119A0, B119E8..B11A20, B11A64..B11A9C | probe v122b: `unresolved indirect call -> 0xB11A04` (bctr B118DC/B11964/B119E4); `add_computed_entries.py <json> 122` |
| mapper 1.00->1.22 | tools/map_funcs_122.py | 20 unique (incl. 9F8E40->AB080C, A12170->AD1670, A26510->AE6C34, B5A944->C1F604) | rest "none": code changed, other matching needed |
| setjmp guards (add_setjmp_guards) | 16 functions (scan, address-free) | 16 functions | `scripts/post-lift-122.ps1`; probe v122e: `depth overflow` 113 -> 0 |
| probe state build-v122 (orig, 150 s) | game loop ~9480 flips | same, 0 unresolved, frame 4200 black | v122d/v122cap/v122e; hooks (script/boot presents/pump) not yet ported; SPU fp 1.22 without lifted image (5x) |
| SPU | 16 job images via fp scan, PM id5 byte-identical @0x14DAA80, 1 embedded ELF @0x1346280; output gen122 + gt6-122/generated/spu_lifted; CMake GT6_V122 switches GT6_SPU_GEN/LIFT | done, 0 MISS |

## Minimum set for C2 (AdjustScreen), state 2026-11-23
From commit 44085a5 (port source, history only) (tools/apply_gt6_post_lift.py): setjmp guards, script hooks (main.adc override), PFS stream/FileDevice/host open, menu pump, sync pump, boot.adc gates.
| Hook | 1.00 | 1.22 (fuzzy) | Status |
|---|---|---|---|
| Script read/path/seek | 9BB020/9BB11C/9BAFE0 | A67E1C(.71)/A67F60(.82)/A67DC4(.42) | tools/port_hooks.py part2 |
| MGOM.start request | 568C94 | 6171D0 (form+0x48 fits) | part2 |
| Sync pump before wait | 568CCC (A21D50) | 617218 (AE2844) | part2 |
| Worker pump loop | A121AC in A12170 | AD16AC in AD1670 (1.0) | part2 |
| processEventLoop | 568658 | 616D58 (.82) | stubs.cpp gt6_menu_project_tick |
| Open/unclear | PackageNullGuard 5F81B0, FileDeviceHost flush A08A74/A08B8C, boot presents (trace only) | - | not ported |
