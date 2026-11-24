# PORT_HOOKS - 1.00 hooks (ref 6697a6d) vs 1.22 (state 2026-11-23)
Source 1.00: `git show 6697a6d:<path>` (ARCHIV/v100 deleted). 1.22 anchors: tools/port_hooks.py, scripts/post-lift.ps1, gt6/src/stubs.cpp. Details per address: PORT.md.

| Hook | in 1.22? | Anchor 1.22 | Effect / evidence |
|---|---|---|---|
| PFS stream read/seek/tell override | yes (port_hooks p1) | AAAC5C / AAB164 / AAB0B8 | PFS files served from host cache; generated contains hooks (run: "pfs override: serving plaintext") |
| FileObject vtable guards | yes | AAA4B0 / AAA530 / AAF354 | NULL object -> r3=0 |
| Host-open wrapper | yes | AB080C (gt6_orig_func_00AB080C in ppu_recomp_023) | prepare/commit path |
| Script read/path/seek (main.adc override) | yes, fuzzy match | A67E1C / A67F60 / A67DC4 | script from host files |
| MGOM.start request + sync pump + worker pump | yes, fuzzy match | 6171D0 / 617218 / AD16AC | menu project pump (Hyp. 39/42) |
| ctor walker / setjmp+guards | yes | 1183C-11880 / C61F88,C620AC | evidence PORT.md |
| boot.adc gates | yes | scripts/patch-boot-adc.py (1.22 offsets) | dialogs skipped (notut runs until ProgressDialog) |
| ZWAP gate (cellMusicInitialize2 arg2=pointer to CELL_OK) | host side yes (stubs.cpp:1325) | - | in 1.22 run NO cellMusicInitialize2 call (0 log lines): guest never reaches the point |
| PFS cache fill b5b260 (fill userdb cache) | p4 ported (GT6_NO_CACHEFILL), probe cf 90 s: no effect (5774 flips, no open) | candidate func_00C1FE74: A26510->AE6C34 @C20368, alloc AE6FE8, obj+0x28/+0x2C/+0x30, B5A944->C1F604 | initUserDB never reached in 1.22 (no open userdb0101.dat) -> relevant only after quit cause |
| FileDeviceHost flush (A08A74/A08B8C) | YES p3 | AC7418 init / AC75B0 flush | CAUSAL: quit ~30 s gone (fdf 5769 flips; GT6_NO_FDFLUSH=1 -> quit) |
| H113 guard (A25C64), PackageNullGuard (5F81B0) | NO | 1.22 anchor open | not checked |
| SPURS job walker, a3 title color, AdjustScreen REALFLAG | unclear | host side (gt6/src, patches/gt6-h46*, gt6-rsx-ignore-stale-a3) | AdjustScreen never reached in 1.22 |

## Finding
All hooks that carry the boot to the savedata load are active in 1.22. The missing ones (b5b260, ZWAP, SPURS, a3, AdjustScreen) lie AFTER the current quit point (LOAD complete GAME6) -> porting them alone does not fix the quit. The quit delta to 1.00 lies between LOAD complete and initUserDB/initSound.
