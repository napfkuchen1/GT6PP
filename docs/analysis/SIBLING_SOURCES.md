# Sibling sources and checks (research 2026-11-24; unverified items marked)

## Sources
- https://github.com/MormonFTP-hub/gt5-recomp: GT5 EU (BCES00569, v1.00), NOT a fork of GT5P, builds on ps3recomp, "playable" (menus/races, STATUS.md 23.11.). Source/patches not readable via API: only README/STATUS.md/CHANGELOG.md known. First breakthrough (changelog 1 Nov): "heap placed where GT5 expects it" got it to the real top menu (mechanism unknown). 3 Nov freezes: lost wake-ups, SPU jobs on one core, game giving up on slow RSX scene loads. NP not a boot blocker; no early-quit fix mentioned.
- https://github.com/sp00nznet/ps3recomp: latest tag v0.20.0 (21.11.). Two later commits (22.11., e.g. 316be1d) restore #822, #646, #804 (InitOnce) lost in the v0.20.0 merge. Our `third_party/ps3recomp-v020` is at d81c393e (21.11.): probably lacks them (not verified). No GT6 issues/PRs.
- https://github.com/sp00nznet/GT5P (local `third_party/GT5P/docs/progress.md`): same PDI engine, also not in menu; traces "SPURS chain: shutdown after 11 job(s)" (l.1162), worker asks for memory, gets none, exits (l.1144-1149), pending flag/uninit slot (l.446-459, 979).

## Checks, cheapest first (do before blind runs)
1. One run with `PS3_EXIT_CHAIN=1` + `PS3_SCENTER=1` (DIAGNOSTICS.md l.682/746); then trace the return path to 0x13FD0 statically (`xref.py --call`, `gdis.py --fn`).
2. Diff `third_party/ps3recomp-v020` against upstream commits after v0.20.0 (316be1d, e85647a): are #822/#646/#804 (InitOnce) present? If not, cherry-pick locally, rebuild, one baseline run.
3. Log heap/memory at start: `sys_memory_get_user_memory_size` (SYSCALLS.md l.352), `sys_memory_allocate`/container calls of GT6; look for an alloc failure before the shutdown (GT5 heap-layout analogy, GT5P l.1144).
4. Compare GT5P "shutdown after N jobs" / pending-flag trace with our chain.
5. Only as one batch (`-Parallel 3-4`): `PS3_PRIO_START`, `PPU_RESV_OFF`, more game threads (hint only, no GT6 evidence).

## Update source and completeness audit (user hint 2026-11-24)
- https://nenkai.github.io/gt-modding-hub/ps3/other/updates/#gt6 lists BCES01893 updates 1.01-1.22 (`EP9001-BCES01893_00-0000000000000000-A01xx-V0100-PE.pkg`, 1.02-1.22 under `.../BCES01893_T359/b80952de9329a9ba/`). Updates must be installed IN ORDER, none skipped (except delisted 1.01). Page gives no sizes/hashes/contents; it warns of "massive issues on RPCS3 from 1.06". Install/decrypt: see that site's "Decrypting USRDIR files".
- Observed locally (not yet analysed): our served data is disc GT.VOL (1.00 tree, `work/gt6_vol`) with only EMAIN swapped to 1.22 (from the RPCS3 update). Default `work/gt6_hdd0/.../USRDIR/PDIPFS` = 25 MB; the oracle copy `work/gt6_hdd0_rp/.../PDIPFS` = 14 GB (update overlay `PDIPFS/K/..` is looked up at boot, eu-boot-log l.38). Probes with `-Hdd0Src work\gt6_hdd0_rp` use the oracle data.
- Audit task: compare the oracle's update USRDIR file list/sizes (EBOOT.BIN 165712 B, EMAIN.SELF 9209104 B, PDIPFS, GT6_1.N saves) with what our probe actually serves (default vs `_rp`); check every file the 1.22 update replaces/adds is present and readable by the VFS (open-failures in the log for USRDIR/PDIPFS paths). Hypothesis: mixed 1.00 data + 1.22 EMAIN explains missing load progress (no PDIPFS/59/FI open).
