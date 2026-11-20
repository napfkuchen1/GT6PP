# EU disc (BCES01893): first build and headless boot

Setup and result of building GT6PP from a clean clone and running it against a
user-owned EU disc dump. Complements `eu-bces01893-compat.md` (static checks)
and `repro-gaps.md` (what was missing to get here).

## Build

- ps3recomp `v0.18.0` + `patches/ps3recomp-gt6-runtime.patch`, LLVM-MinGW from
  `scripts/build-gt6.ps1`. Two things about that patch: the file is UTF-16 and
  has to be converted to UTF-8 first, and its `rsx_d3d12_backend.{c,h}` hunks do
  not match `v0.18.0` (excluded with `git apply --exclude`; the headless run
  does not use that backend). It already contains the `ps3recomp-mingw-seh`
  hunks, so the two must not both be applied. A first build with only the
  MinGW patch is described under "First attempt" below.
- `functions_corrected.json` regenerated with `tools/find_functions.py` and
  `tools/boundary_audit.py` (70,823 functions), then `scripts/relift-gt6.ps1`.
  All post-lift patches applied; `add_boot_presents_hooks` needed the
  per-function fix from this branch.
- Embedded SPU ELFs: `extract_spu_images.py` + `build_spu_workloads.py`
  (same four offsets as the docs, `spu_workloads.c` came out identical).
- 15 SPU job images: cut out of the decrypted `EMAIN.elf` by fingerprint (see
  `repro-gaps.md`), then `scripts/lift-spu-jobs.ps1` (6,562 functions).
- `scripts/build-gt6.ps1` links `gt6/build/gt6.exe`.

## Run

`PS3_VERBOSE=1`, `PS3_HEADLESS=1`, `scripts/run-gt6.ps1 -Seconds 90`, disc tree
with `PS3_GAME/` from the EU disc and `USRDIR/GT.VOL` as a hardlink to the
copied volume. The first table is from the first attempt (v0.18.0 + MinGW
patch only), which ran about 6 seconds; see below for the second build.

| Observation | Value |
|---|---|
| Title id read from `PARAM.SFO` | `BCES01893` |
| `BootCheck` | `type=1, titleId='BCES01893'` |
| `GT.VOL` opened via `/dev_bdvd/PS3_GAME/USRDIR/GT.VOL` | yes |
| Update-overlay lookups | `/dev_hdd0/game/BCES01893/USRDIR/PDIPFS/K/{4D,E9}` opened |
| `cellSpursInitialize` | "PDI", 5 SPUs |
| WWS workloads added | `Wws_Job` / `ElemSetRenderHP`, `ElemSetRender`, `ElemSetUpdate`, `ElemSetGeneral`, ... |
| `[spurs-job] dispatch HIT` | 56 |
| SPU dispatch misses / `NOT LIFTED` | 0 |
| Distinct job images hit | 6 (`1B6BDAC375C5438D`, `ABD49FC58F53F368`, `C1E79DAD1A299848`, `CB9BD0241BB0DE67`, `F523F26F69764538`, `FDFFAAC1BCD5352E`) |
| `unresolved indirect call` lines | 181 (same kind as in `CONTINUE-HERE.md`) |
| Display | headless, no RSX backend; nothing was rendered |

All job images hit by the guest are found in the registry, which also shows that
cutting the images out of `EMAIN.elf` gives the same fingerprints the owner
captured at runtime.

### First attempt (v0.18.0 + MinGW patch only)

The process did not stay up. After about 6 seconds it died with
`ACCESS VIOLATION: read at host <vm_base>+0x100000000` (rva `0xAF7FD3`, guest
read at `0xFFFFFFFF`, "crash is NOT a PPU thread"). That is the SPU event crash
described in `spu-event-crash-check.md`: the SPURS completion index runs past
the 16-entry handler table and the unresolved-call reporter then dereferences
guest `0xFFFFFFFF`. The build here is ps3recomp `v0.18.0` plus only the MinGW
SEH patch, so the producer-side fix from `ps3recomp-gt6-runtime` is not in it.
Adding `ps3recomp-gt6-runtime.patch` (see Build) fixes it: the same run now
survives the full 90 seconds with no access violation.

### With the runtime patch

| Observation | Value |
|---|---|
| Process | alive after 90 s (stopped by the script), no access violation |
| Boot script | `script override: serving decrypted /scripts/gt6/main.adc (857518 bytes)`, i.e. the extracted EU file |
| `[spurs-job] dispatch HIT` | about 35,600 (same job images, no misses) |
| `takeflip` lines | 16 |
| `unresolved indirect call` | about 13,800; 6,731 of them are `0x009F9380` |

`unresolved indirect call` is no longer 181 as in the first run, it keeps
growing while the guest spins. No `draws` statistic was checked here.

### Second round: patched lifter, memset entries, real lwcond

Three changes on top of the table above, each checked with a headless run:

1. **Relift with the patched lifter** (`patches/ps3recomp-gt6-runtime.patch`
   also carries the lifter changes). The absolute jump-table switch generation
   there removes the `0x009F9380` spin; the SPURS completion fix stays.
2. **Memset entry points** (`tools/add_computed_entries.py`, see `repro-gaps.md`).
   After this the run has 0 `unresolved indirect call` lines.
3. **`patches/ps3recomp-lwcond-real-wait.patch`.** The stock `sys_lwcond_wait` is a
   1 ms poll and the signal calls do nothing, so every wait returns early.
   GT6's event wrapper (`func_00A21CBC` / `A4305C`) waits once without a
   predicate loop. In the earlier runs the main thread (stack `0xCFE00000`)
   left a wait too early, returned from its function and the file worker
   (tid 14, `func_009F811C` / `9F7F94` / `9F8534`) then read the request that
   still lived in that dead stack frame (`0xCFEFF480`): vtable slot full of
   junk, calls into page 0, a space-filled lwmutex. With real wait/signal
   semantics (per-lwcond semaphore keyed by the queue id at `lwcond+4`,
   `signal_all` wakes every waiter, `ETIMEDOUT` honoured, lost signals stay lost)
   none of that happens any more.

| Observation | Value |
|---|---|
| Run length | 150 s headless, process alive, no access violation |
| `null-call` lines | 0 (was several per run on tids 1 and 14) |
| `unresolved indirect call` | 0 |
| `pfs override` files served | 56, among them `SettingProject.gpb`, `specdb/GT6/DB0106.dat` (16 MB), `specdb/GT6/US/CarName.dat`, `database/gt6/menudb.dat` |
| Threads created | 44 (`sys_ppu_thread_create`), SPU workers, audio, `TM_FFB_WorkerThread` x4 |
| `cellGcmSys` | only `GetLabelAddress(0x48..0x4B)` so far, no flip, no draw |
| `unresolved NID` (24 lines) | cellFiber (`0xA4599CF3`, `0xF6C6900C`), cellUsbd, sys_net (`0x13EFE7F5` getsockname, `0x8AF3825E`), sys_io `0x1F71ECBE`, sysPrxForUser `0xA5D06BF0`, `0xCA9A60BF` |

Debug aid: `PS3_LWCOND_LOG=1` prints every lwcond wait and signal with the
queue id, thread and return address; `PS3_LWCOND_POLL=1` brings the old poll
back. The two stale-stack notes: the `[mainstack]` / `[hostchain]` dump scans
raw stack words, so frames of calls that already returned show up in it
(`func_00A4305C` under the script loader was one of those).

The repo already has experimental `ps3recomp-lwcond-generation*.patch` and
`-qid-pending` patches. This one does not cap the wait at 1 ms; it is not built
on them and has not been tried together with them.

### Third round: cellFiber WaitFlag / CheckFlags

The two unnamed cellFiber imports are `0xA4599CF3` = `cellFiberPpuWaitFlag` and
`0xF6C6900C` = `cellFiberPpuCheckFlags` (found by hashing the cellFiber export
names; `sha1(name + suffix)`, first 4 bytes little endian). The GT6 call sites
(`0xA2F448`, `0xA2F8E8`) store 1 into a word, call `WaitFlag(&word, 0)`, and the
other side clears it and calls `CheckFlags(scheduler)`. `gt6/src/stubs.cpp` now
registers two overrides: `WaitFlag` yields the current fiber until
`*flag == value` (gives up outside a fiber), `CheckFlags` returns `CELL_OK`.

Same 150 s headless run as before: still 0 `null-call`, 0 `unresolved indirect
call`, no access violation. `unresolved NID` lines drop from 24 to 14 (left:
`cellUsbd` `0x7FE92C54` / `0xBD554BCB`, `sysPrxForUser` `0xCA9A60BF` /
`0xA5D06BF0`, sys_io `0x1F71ECBE`). The guest now gets past `menudb.dat` and
loads the boot and dialog projects (`projects/gt6/boot/boot.adc`,
`BootProject.gpb`, `dialog.adc`, `DialogProject.gpb`) and
`projects/gt6/boot/DE/PresentsRootSCEE.gpb`, the EU presents screen. `cellGcm`
still only shows `_cellGcmInitBody` and `GetLabelAddress`; no flip yet in the
headless run.

Still open: what the guest does after `menudb.dat` (the `0xA4599CF3` NID is the
last one reported before the stream of `GetLabelAddress` calls) and the
`null-read` hits at `0x009791B4` / `0x00B6E950` / `0x00A03438`.

## Not covered

- No windowed run, so no statement about `draws`/frame output on EU.
- Script-loader trace: `tools/gt6_pfs_probe_patch.py` was applied to
  `ppu_recomp_022/023.cpp` (`git apply --ignore-whitespace`, the generated files
  are CRLF) and the tree was restored afterwards. With the first-attempt build
  the loader was never reached (crash before it). With the runtime patch the
  probe prints, in order: `pfs-header`, several `mount`,
  `HFileReader::open ... path='/scripts/gt6/main.adc'`, the override line above,
  and `[scriptload] reader=0x7FFD61E0 vtable=0x01484CC8 ret=8`, so the
  8-byte header read succeeds. The probe in this repo version only prints
  `ret`, not the bytes, so "reads `ADCH012`" is inferred from the file the
  override serves, not observed in the log. The `9CC208` result was not logged.
- No windowed run, and the guest spins on `0x009F9380` afterwards; what it waits
  for was not investigated.
- A `tools/patches/spu_event_dispatch_guard.py --apply` run on the first-attempt
  build did not help (same crash); it was not needed with the runtime patch.
