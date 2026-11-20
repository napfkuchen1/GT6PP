# Reproducibility gaps found while setting up from a clean clone

Findings from an independent setup attempt on Windows 11 with an EU disc
(`BCES01893`). None of these were fixed upstream behaviour; they are requests.

1. **`third_party/ps3recomp` base is unpinned.** BUILDING.md says `master`, but
   `patches/*.patch` only apply onto an unrecorded commit. Please record the
   exact base commit hash (or publish the patched tree as a fork/branch).
2. **Patch order is implicit.** `ps3recomp-mingw-seh` overlaps the `cellFs.c`
   change in `ps3recomp-gt6-runtime`. Document the apply order.
3. **`ps3recomp-gt6-bringup-dds.patch` has a hunk header whose line counts do
   not match its body**, so `git apply` rejects it (`git apply --recount`
   is needed).
4. **Line endings.** The patches are LF in the repo, but with Windows
   `core.autocrlf=true` they are checked out as CRLF and fail to apply.
   `.gitattributes` (added in this change) marks `*.patch` as `-text`.
5. **Function lists are not committed.** `relift-gt6.ps1` prefers
   `work/analysis/emain/functions_corrected.json`, which only exists locally.
   Without it, `functions_final3.json` (also local) is the fallback; neither can
   be regenerated from a clean clone. Please commit them (they contain no
   copyrighted data) or document how to produce them.
6. **No recorded hash of the US `EMAIN.elf`.** Adding SHA-256 values to
   BUILDING.md lets owners verify their decrypt step.

Update after getting a first `gt6.exe` linked from a clean clone (EU disc):

- **ps3recomp base that works:** tag `v0.18.0` + `ps3recomp-mingw-seh.patch`
  (that is what the docs were written on). The other patches were not needed
  to get a linking build.
- **Gap 5 is solvable without the owner's files.** `tools/find_functions.py`
  followed by `tools/boundary_audit.py` regenerates `functions_corrected.json`
  from the decrypted ELF (70,823 functions here vs. 70,672 documented; the
  relift and all post-lift patches still applied). Worth adding to BUILDING.md.
- **`apply_gt6_post_lift.py`:** `add_boot_presents_hooks` skipped the second
  function when two functions share a hook (`if call in s: continue` was a
  per-file check). It is now per function (`key + call in s`).
- **SPU images are not produced by `relift-gt6.ps1`.** The link fails with
  undefined `spu_000N_*` / `job_*` symbols until you run
  `extract_spu_images.py` + `build_spu_workloads.py` (HANDOFF.md) and
  `lift-spu-jobs.ps1`. The latter wants `work/spu_jobs/dump/spujob_<FP>_<size>.bin`
  captures, but all 15 job images (the fingerprints and sizes are in
  `spu_workloads_jobs.c`) are plain byte ranges of `EMAIN.elf` (128-byte
  aligned), so the dumps can be cut out of the ELF. File offsets in the
  decrypted ELF, e.g. `spujob_1B6BDAC375C5438D_13840.bin` at `0x139D080`,
  `spujob_FE031AF67ED048DE_46928.bin` at `0x13D2500`.
- **Disc path is hardcoded** in `gt6/src/main.cpp`
  (`PS3-Version/Gran Turismo 6 (USA) (En,Ja,Fr)/PS3_GAME`). Without PARAM.SFO
  there the HLE reports `BLES00000`. Layout used for the EU test: that
  directory holds `PS3_GAME/` from the disc, with `USRDIR/GT.VOL` hardlinked.

With that, the EU disc boots to the documented stop (`BootCheck` reads
`BCES01893` from PARAM.SFO, SPURS initialises, black frame, `draws: 0`).

Region check for the EU disc: see `eu-bces01893-compat.md`.
