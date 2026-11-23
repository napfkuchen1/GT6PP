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

### Windowed run (90 s)

Without `PS3_HEADLESS` the D3D12 backend comes up (`[rsx] backend init OK --
window open`), but the guest still issues no flip and no draw: `cellGcm` shows
only `_cellGcmInitBody` and the `GetLabelAddress` calls, and the last files
served are the dialog project and `PresentsRootSCEE.gpb`. Still 0 `null-call`, 0
`unresolved indirect call`, no access violation.

What the threads do at the end of the run (counts of `[WAIT]` lines):
`event_queue_receive(q=4, timeout 0)` ~18,000 and `q=5` ~16,900 from tid 18
(`lr` `0x0082039C` / `0x0081FD34`), `q=7` ~16,900 from tid 21 (`lr`
`0x00A4F784`), `q=1` (62.5 ms, tid 2) ~1,250. tid 1 only polls `q=4`. So the
guest sits in a polling loop on those queues and never gets to the first
present. `cellFiberPpuWaitFlag` is also in that picture (`[HOTREAD]` on
`0x7FEE8084`, `lr` `0x00A2F44C`); the override now blocks on a plain thread
(bounded to 5 s, never hit) instead of returning at once. It did not change the
outcome, so it is not the blocker.

Next: find out which event the loop at `0x0081FD34` / `0x0082039C` is waiting for
(queue 4/5 owners and their senders).

### Where the windowed run stops (analysis)

Logged with `PS3_LWCOND_LOG=1`, `PS3_VERBOSE=1`, 45-55 s:

- The boot phase finishes cleanly. Main (tid 1) and the loader worker (tid 11)
  ping-pong through two lwconds (`0x7FFD55D8` / `0x72539110`); the last cycle
  completes, `PresentsRootSCEE.gpb` is served, the short-lived `PDI` / `Z-9YS`
  threads (36-39) run and exit, and `tmp_save_work.dat` is opened under
  `/dev_hdd1/cache/BCES01893`.
- After that tid 1 makes no further logged syscall or sync call. The render
  worker group (tids 16/17 signal, 19/27/29 wait on `0xD0089DD8`,
  `0xD00BDDD8`, `0xD00B2DB8`, all `lr` `0x00A43038` / `0x00A4309C`) cycles
  with `cellGcmGetLabelAddress(0x48..0x4B)` and nothing else: no flip, no
  `SetFlip`, no `rsx_process_fifo`.
- `[mainstack]` / `[hostchain]` show `func_00F9AC18` (a `cellSailRec` import stub
  in the table) on top. That dump scans raw stack words, so it is not evidence.
  What it does not tell is where main is parked; it is either spinning in
  guest code without a syscall or inside a sync primitive that is not logged.
- `[HOTREAD]` on `0x7FEE8084` (`lr` `0x00A2F44C`) is the `cellFiberPpuWaitFlag`
  caller, a worker queue loop at `0x00A2F464`, i.e. normal consumer behaviour.
- Queue 4/5 polling by tid 18 (`0x0081FC80..0x00820100`) is a 16-entry ring
  dispatcher around `sys_event_queue_receive`; those receives return because
  SPURS completion events keep arriving, so this is activity, not the blocker.
- `gt6/src/gt6_present.cpp` drains the RSX FIFO from its presents hooks, so no
  flip means no drain: the render group waits on labels the RSX would write.

Next step: sample where main is at the end of the run (guest PC sampling, or a
log line for every lwmutex / semaphore / cond call with tid) instead of relying on
the stack scan.

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

## Boot stall after the save check: missing guest caller

After `PresentsRootSCEE.gpb` the main thread called
`cellSaveData AutoLoad2(dir='BCJS37016-GAME6')` and the stat callback
"returned -2" (`ERR_FAILURE`). The log never showed `dispatching funcStat`:
`dispatch_func_stat_full` bails out when `g_ps3_guest_caller` is NULL, and
`gt6/src/main.cpp` never installed it (the other harnesses do). Every
HLE -> guest callback (save data, sysutil, trophy) was dead.

Installing a shim around `ppu_guest_call` before `ppu_run` fixes it. The game's
funcStat now runs and answers `ERR_NODATA` for a profile without save data,
and the title carries on: roughly 400 to 800 `SetPrepareFlip`/`SetFlipImmediate`
pairs in a 60-90 s run and several thousand D3D12 `draw_arrays` calls.

### userdb open fixed (vtable guard)

`gt6_guest_file_vtable_valid` (stubs.cpp) only accepted objects with open/close
OPDs at vtable `+0x20/+0x24`. Device objects such as the `/APP_DATA` mount
(vtable `0x0148CAA8`) keep their open method at `+0x88`, so the guard in
`func_009F3F2C` returned success without opening. `file+0x4c` stayed NULL and
`init_user_db` fell into its failure dialog. The guard now also accepts a valid
`+0x88` slot. With it `userdb0101.dat` and `grim2/grim007.db` open (created on
first use, empty read = EOF, which the guest accepts), the `[sleepmsg]` loop is
gone and the RSX now sees `CLEAR_SURFACE` plus DATA2F quad draws and label
fences, followed by flips. The window is still black: the clear colour is
`0xFF000000` and the quads are untextured. `[HOTREAD]` on `0x7FEE2084` is the
normal `cellFiberPpuWaitFlag` consumer loop.

## First geometry reaches the backbuffer

Two renderer bugs kept every draw invisible even though the RSX saw them:

1. **Immediate-mode vertices were all zero.** `rsx_immediate_finish` wrote the
   collected DATA2F vertices to `RSX_IMMEDIATE_SCRATCH` through
   `cellGcmResolveOffset`, but the reader (`rsx_fetch_attrib`) resolves a LOCAL
   (bit 31 clear) array with `cellGcmResolveLocated(1, off)`. Writer and reader
   landed in different memory. The writer now uses the same resolution.
2. **POLYGON fell into the legacy draw path.** GT6 draws its full-screen quads
   as primitive 10 (POLYGON). The D3D12 vertex-program path only knows
   TRIANGLES, STRIP, FAN and QUADS, and the legacy path emits no pixels.
   POLYGON is a convex fan, so both draw entry points now map it to FAN.

Proof: `FP_FORCE=1` (fragment program replaced by a constant magenta) turns the
whole 1280x720 backbuffer magenta, so vertex transform, rasterisation and
present work. `FP_FORCE` itself had a bug: it only matched `return r[0];`, but
this title's translated programs end in `return (_o == _o) ? _o : (float4)0;`,
so the override silently did nothing and an earlier "even magenta stays black"
conclusion was wrong. Both endings are handled now.

## First real frame

Normal frames were black because the texcoords were constant. GT6 draws its
legal screen with immediate-mode DATA2F triangle strips: per vertex it writes
position (attr0) and texcoord (attr8). `rsx_immediate_finish` only snapshotted
attr0 into a scratch array, so attr8 stayed at whatever the last write was and
every vertex sampled the same texel (`FP_TEX_UV=1` sampling the centre gave
content, `input.tc0.xy` gave black, which pointed here). It now snapshots attr8
as well and feeds it through a second scratch array for the draw.

Result: the backbuffer shows "Sony Computer Entertainment presents"
(`docs/analysis/first-frame-sce.png`), rendered from the game's own command
stream on the EU disc.

Patches: `patches/ps3recomp-gt6-eu-render.patch` (POLYGON as fan, scratch base, FP_FORCE/FP_TEX anchors, immediate attr8) and `patches/ps3recomp-gt6-eu-runtime.patch` (lwcond slot table 256 ->
16384 with destroy cleanup, `cellFsGetFreeSize` free-space override). Apply them
after `ps3recomp-gt6-runtime.patch`, with `--ignore-whitespace`.

## After the first frame

The legal screen fades in and the loading dots appear (frames ~400+), but the
sequence never advances: after 11000 flips (about 150 s) the backbuffer is
still the "Sony Computer Entertainment presents" screen. The US notes in
`boot-project-handoff-fix.md` say the presents table should switch images
every 2 to 4 s and then hand off to the movie sequence, so something is
waiting and never completes.

One run (RSX_CAP, 180 s) ended after about 2000 flips with
`sys_process_exit(1)`. The host backtrace resolves (via `llvm-nm` on gt6.exe)
to `func_00BA2460`, which only calls the abort helper `func_00B8EC2C`; it is
a pure-virtual-style stub reached by an indirect call from `func_00BA2420`.
It happens right after `PresentsRootSCEE.gpb` loads, three short "PDI"
threads are joined and the guest stores 0 to NULL+0x500. A second run did not
abort, so it is timing dependent. Not fixed yet.

## Notes from the existing docs (read for the presents stall)

- `rpcs3-oracle.md`: on the real disc the order is legal frame, display-area screen, epilepsy warning, intro movie, Player Name screen. So after the three presents images the game hands off to the movie, nothing else is needed in between.
- `legal-gpb-draw-fix.md` / `first-draw-audit.md`: image changes in `PresentsRoot` are script driven (`changeImage` + `ScalarInterpolator` timers, 2 s / 2 s / 4 s). A stuck first image means the script timers never fire, not a draw problem. The EU path loads `PresentsRootSCEE.gpb` (DE folder), logged in our run right before the stall/abort.
- `lwcond-experiment.md` is superseded; `pfs-mount-device-check.md` is about the old PFS bind patch and does not apply to the host-file override we use.
- Next check: does `changeImage` get called a second time, and which time source drives the interpolators (sys_time / timebase / frame delta)? A 45 s run with GT6_SCRIPT_TRACE only shows script reads, no timer activity; the run ended with the PDI-thread join and `sys_process_exit(1)` again.

## VBlank/flip handlers ruled out

Upstream ps3recomp README/docs: `docs/DIAGNOSTICS.md` lists every debug env (`GCM_PUMP_DBG`, `MUTEX_WATCH`, `GCM_HANDLER_THREAD`, `PS3_WAITBT`, `GCM_FLIPCB_ONTICK`). GT6 registers both handlers (`SetVBlankHandler` opd 0x014E4868, `SetFlipHandler` opd 0x014E4848). With `GCM_PUMP_DBG=1` they are delivered at ~60 Hz (about 1800 vblank and 1800 flip callbacks in 30 s). So a missing vblank tick is not the cause of the presents stall; look at the guest-side timer/time source or a blocked thread next (`MUTEX_WATCH`, `PS3_WAITBT`).

## ps3recomp upgraded to v0.19.0 (local)

Our whole local ps3recomp delta (EU runtime, lwcond real wait, immediate-mode render fix, MinGW bits) was re-applied on the v0.19.0 tag with `git apply --3way`. 10 conflict hunks: took upstream for `cellSpurs.h`, `ppu_loader.cpp` (their MinGW fix) and `ppu_fs.cpp` (our PDIPFS cache trace only, diagnostic); kept both sides in `cellGcmSys.c` (GCM_DRAWPROBE next to their report hold). Dropped our `cellSpursInitializeWithAttribute2` alias because v0.19.0 has a proper 8192-byte CellSpurs2 version.

Result: builds, boots, first frame ("Sony Computer Entertainment presents", ~62 FPS in the window title), same presents stall as on v0.18.0 (4384 flips in 60 s, no abort in this run). So the stall is not a v0.18.0 runtime bug.

Consolidated delta vs v0.19.0: `patches/ps3recomp-v0.19.0-gt6-eu-all.patch` (replaces the per-topic stack for v0.19.0; the older patches remain for v0.18.0). The ppu_lifter changed upstream (+41 lines); the generated tree was not re-lifted yet.

## The sys_process_exit(1) abort

`func_00B8EC2C` (lifted in `ppu_recomp_027.cpp`) is the game's fatal-error printer: it writes through `sys_tty_write` (syscall 988/403) and then exits; `func_00BA2460` is a thin wrapper around it, called indirectly from `func_00BA2420` (a callback through a global function pointer). So the earlier abort was the game deliberately quitting after an internal error, not a runtime crash.

It did not reproduce after the ps3recomp v0.19.0 upgrade and re-lift: 6 of 6 windowed runs of 100 s (6855 to 7363 flips each) plus 5 earlier runs ran to the end without `exit-chain`. It was only ever seen on the v0.18.0 build (one run at ~2075 flips, one with GT6_SCRIPT_TRACE). If it comes back, check the TTY text in `work/gt6_run.log` right before the exit; the abort log was not saved at the time.

## The presents stall: the game shows a fatal "not enough disk space" dialog (corrects the earlier future theory)

The main thread is not waiting for a lost future. It joins the dialog thread "PDI" (entry 0x014E0898 -> func_00A304D0) after `cellMsgDialogOpen2` (called from func_00A36F7C) shows: "Nicht genuegend Speicherplatz auf der Festplatte. Es werden mindestens 32MB benoetigt." (type 0x80, no buttons, so it never closes). Free-space values (fs, savedata) were ruled out.

Trigger: on the SECOND boot, validation of an existing `USRDIR/db/userdb0101.dat` fails (guest error codes 183/151). A fresh boot (file absent) passes.
- Fresh flow: writes a 512-byte block at pos 0 (starts B8633B64 0C25CE82), reads 100 bytes, then lseek(0) + writes 4096-byte encrypted pages from pos 0. Page 0 therefore overwrites the 512-byte block (starts 359FC9E2 A6ED500B).
- Boot 2 reads 8 + 512 bytes at pos 0 (reader: func_00A40FBC <- 00A0AF18 <- 00A034D8 <- 00A0871C <- 009F92CC <- 009F7B3C <- 009F83D4 <- 009F8078 <- 00A304D0, thread PDI) and rejects the page-0 form.
- Restoring the first 512 bytes from the saved block makes boot 2 pass (pagefile.sys opened, no dialog; next gap: unresolved NID 0xBE50B11E cellMusicInitialize2). Restoring only the first 8 bytes is NOT enough, so the check covers more than the magic.
- Open: what the validator compares against (page-0 ciphertext vs. 512-byte block). Suspects: a key/salt derived from data we do not provide, or an fs semantic difference (write at pos 0 after lseek).

Stopgap: move `work/gt6_hdd0/game/BCES01893/USRDIR/db/userdb0101.dat` to ARCHIV before each boot (fresh flow works).

Diagnostics added: `PS3_FSLOG_WRITES=<fd>` logs `[fswrite] fd want got pos b0..b3` (next to `PS3_FSLOG_READS`).

### Validator bisect (2026-11-20, later session)

Method: restore `work/_db_pre_patch2.dat` (page-0 form), patch bytes from `work/hdr512.bin` (the 512-byte block of a fresh run), boot 22 s, count the dialog.
- The 512-byte block is deterministic (B8633B64 0C25CE82 ... in every fresh run), not random. It acts as an "uninitialised file" marker: the game accepts it, re-reads 100 bytes and rewrites the pages.
- All 512 bytes are needed: patching 0..504, 8..512, 0..256, 256..512, 0..100 or 0..400 still shows the dialog; only 0..512 passes.
- Header magic: 359FC9E2 A6ED500B = encrypted "SQLite format" (same key stream for `userdb0101.dat` and our own `grim2/grim007.db`; `DB0106.dat` uses another, 685AF834).
- Plaintext diff userdb vs grim007 only in change counter, page count and schema cookie; counter equals version-valid-for in both. So the decrypted page-0 header is consistent.
- Putting grim007's first 512 bytes into the db still fails. Truncating the db to the 11 written pages (45056 B) still fails. No failing HLE return (`PS3_HLE_ERRLOG=1`) around the db open.
- Boot 2 trace (`FS_CALLER=1`): open, read 8, close, open, lseek 0, read 512, close, repeat once, then the dialog thread. No further file IO.
- Not yet known: what the guest compares in the 512 bytes. The reader chain is virtual-call heavy (func_009F82C0 -> indirect calls), so static reading is slow; next try a guest function-entry trace after the 512-byte read.
- New diagnostics: `[fsread]` now prints `buf=0x...`; `PS3_FSLOG_READS_BT=1` dumps the guest stack at each logged read.
- Seen once: a run with FS_CALLER+FSLOG stuck at `[HOTREAD8] spinning on 0x21 ... guest-fn=0x005F3434` before reaching the db (not reproduced in 4 reruns).

### Validator trace diff (2026-11-21)

Method: `PS3_ICALL_TRACE=1` + `PS3_ICALL_GATE=<existing file>` now logs `[ict] target r3 lr=…`.
Boot 2 with failing db (page-0 form) vs. same db with the 512-byte marker block restored (passes).
Traces are identical up to the 512-byte read + a 4096-byte page-size getter (`00B59BD8`) + a
memset (`00A4FE78`, caller lr `00B24040`, function in ppu_recomp_025). Then:

- pass: next is the 100-byte read (`00A03438` lr `009F4A60` -> `fsread want=100`), boot continues.
- fail: the 100-byte read never happens; `00A434B8`/`00A43618` run instead, error value 26 first
  appears at `008AAF18` (error handler) -> dialog [183].

So the decision is made from the 512-byte buffer in the code after `00B24040`
(`[r29+0x3C]` stream object check, `func_00AF8AFC(…, 0x64, 0)`), before the 100-byte read.
Not yet resolved: which compare on the buffer fails. Next: read the function containing
`00B24040` up to its branch to `00B24348`, watch `r0=[[r29+0x3C]]`.
Stopgap unchanged: archive/move `userdb0101.dat` before each boot.

Update 2026-11-21 (later): `00B23FD4..00B24060` = open-file path: `func_00B0FF60(r3=ctx,r4=obj,r5=path,r6=0x4C,r7=flags)` (contains the 512-byte read chain `00AF8CD8`), then memset 0x64 at `00B24040`, then `r3=[[obj]+0x3C]; if [r3]!=0 -> func_00AF8AFC(…,0x64,0)` = the 100-byte read. Fail case: that `[r3]` check/read is skipped. Page-0 form is what the game itself writes over the 512 header (same after 60 s), so either the game expects the header region decrypted (guest crypto, possible lift bug in VMX/AES code) or a later header re-write at clean shutdown never happens because runs are killed. Untested hypotheses: (a) clean shutdown writes header; (b) decrypt/compare in guest crypto code miscompiles.

Update 2026-11-21 (writes): hypothesis (a) tested and refuted for the first 40 s of a fresh boot. Page 0 (4096 B, 359FC9E2…) is rewritten as header/journal page *before every data page* (pos=0 then pos=N*4096); its content is identical across all writes and across boots (cmp of 4096 B equal between runs). The 512-byte marker block (B8633B64…) is written once at create and overwritten by the first page-0 write. So game-written page 0 is deterministic and rejected on read in boot 2, while the marker form is accepted. Remaining theories: (b) read-side decrypt/verify in guest code mis-lifted or fed a differing HLE value (key material not stable between create and re-open), (c) file position/offset semantics (lseek whence) differ from the real LV2 so page 0 lands where the game does not expect it. Next test: log lseek whence/offset (`FS_CALLER=1`) during boot-1 page writes and verify pos matches the guest-requested offset.

## Update 2026-11-21 (lseek + SQLite finding)
- Theorie (c) lseek widerlegt: Boot-1-Trace (FS_CALLER=1) zeigt lseek-Offsets = Hostpositionen (0, 4096, 8192 ...), whence=1/off=0 (tell) konsistent, cellFsLseek-HLE korrekt.
- userdb0101.dat ist eine SQLite-DB (Pager): in func_00B0FF60-Kette liest der Code 100 Byte Header (memset 0x64 bei lr 00B24040, Seitengroesse aus Header-Byte 0x10/0x11), Fehlercode 0x1a = 26 = SQLITE_NOTADB.
- Fail-Entscheidung: `[[r29+0x3C]]` = pPager->fd->pMethods == 0 -> Datei-xOpen (func_00A41A2C, game VFS/Verschluesselungs-Wrapper, 512-Byte-Header-Read) hat fd nicht erfolgreich geoeffnet -> 100-Byte-Read entfaellt -> NOTADB.
- Naechster Schritt: func_00A41A2C nach dem 512-Read (lr 00A41384) lesen: welche Pruefung (Hash/Key/AES) lehnt Page-0-Form ab.
- RWATCH-Grenze: PPU_RWATCH hookt nur vm_read8/16/32 (+ jetzt read64). Header-Parse des 512-Byte-Puffers (0x9FFAFA08) liefert nach dem Read KEINE Treffer -> Puffer wird per lvx (vm_raw_ld16, inline in ppu_recomp.h) gelesen. Diagnose-Hook: g_rwatch_vec_on/ppu_rwatch_vec (ppu_recomp.h + ppu_loader.cpp), Armierung ueber PS3_RWATCH_AFTER_512=1 (ppu_fs.cpp, armiert RWATCH auf Lese-Puffer nach 512-Byte-Read). Backup: work/ppu_recomp.h.bak_prevec.
- 512-Puffer-Konsumenten (fd8, Fail-Boot, RWATCH mit Dummy `PPU_RWATCH=10,4` damit Inline-Loads aus sind + `PS3_RWATCH_AFTER_512=1`, nur fd 8): erst Copy durch func_00A03F80 (64 Treffer), dann func_00B5B260 (1), func_00A44838 (2), func_00A44BAC (1), func_00B0D710/D544, func_00B0914C, func_00AFE380, func_00B2CD94/B11018/B2BF2C/B2BE00, func_00B23144/B2323C, func_00B09E10/B09CD8. Nach diesen Funktionen suchen: erste Pruefung ab 00A44838. HINWEIS: PPU_RWATCH muss gesetzt sein, sonst sind Loads inline und unsichtbar (vm_inline_ok).
- Korrektur: 0x9FFAFA08 liegt im Heap (nicht Stack); die spaeteren Treffer (func_00A44838/A44958 = Boundary-Tag-Allocator) sind Wiederverwendung nach free, KEINE Pruefer. Einziger relevanter Konsument des 512-Puffers: Copy func_00A03F80 (64 Treffer, 512 Byte, aus func_00A030B8/009F82C0 read-wrapper) und func_00B5B260 (1 Treffer). Ziel der Kopie ist der naechste Beobachtungspunkt: Zieladresse aus dem Aufruf von func_00A03F80 ermitteln und dort RWATCH setzen (Heap-Adresse vorher auf Stabilitaet pruefen).

## Boot-2 validator: cache never filled (2026-11-21)
- A03F80 = position-keyed stream cipher (decrypt verified correct), not a copy. pMethods/lseek/free-space theories refuted.
- func_00B5B260 allocs an in-memory cache (size rounded up to 64 KB) for each opened file; B5B028 reads from it without fill check. Nothing in the guest fills it (write-watch: no stores) -> 8 MB zero buffer -> header read zeros -> SQLITE_NOTADB (26) -> dialog "Nicht genuegend Speicherplatz".
- A26510 / event_port_send (syscall 138) is tracing/bookkeeping only. Fresh boot / 512-byte marker pass because cache size = 0 -> real reads.
- Fix: fill cache from file (seek 0 + F7666C) after A26510 success. See patches/gt6-b5b260-cache-fill.patch.txt. Result: dialog gone, next gap NID 0xBE50B11E.
- Open: the lift has no real filler; retail likely fills it through a path our runtime lacks (root cause unknown). Fix is a workaround in generated code (gitignored, re-apply after relift).

## cellMusicInitialize2 (2026-11-21)
- NID 0xBE50B11E stubbed in gt6/src/stubs.cpp (returns CELL_OK, no callback). Boot continues: frames presented (3300 takeflips/40 s), no unresolved NIDs, next fs open /dev_hdd1/cache/BCES01893/game024.db.
- Not verified: whether the game later waits for a cellMusic callback; real-frame content not checked.

## Render path after boot-2 fix (2026-11-21)
- Screen now = language-select dialog (LanguageSelectRoot.gpb loaded). Frame 2500 capture (RSX_CAP=2500:1, work/rsxcap*): 158 draws, all rt=0 (backbuffer), no CLEAR op; blue = backbuffer clear colour showing through, black triangle = one half of a quad.
- EMPTYTEX/TEX_MARKEMPTY: every empty sampler is an offscreen surface in RSX local memory (0xC0000000 1216x684 fmt A5, 0xC0660000, 0xC0CC0000, 0xC1320000 (t3 on ALL draws), 0xC1980000 1440x1080 fmt E5 (vs=7 draws, 288 verts), 0xC2200000 1152x648). No draw in the captured frame renders into these surfaces, so they stay zero. Guest textures (SZ 8x8/128x128 glyph/atlas) are not the empty ones.
- Experiment: binding the display-sized screen copy also for 1216x684 (SCREEN_AS_TEX_SAFE=1, env-gated hack in rsx_d3d12_backend.c, uncommitted, backup work/rsx_d3d12_backend.c.bak_safe) turns the dialog panel white and shows borders, but text is still missing and the black half-quad remains.
- Open: who produces the 1440x1080 / 1216x684 surfaces (earlier frames? SPU/transfer?), why only a half quad draws (QUADS->tris expansion for vs=7?).

## Render fix: display-buffer textures + zeta fill (2026-11-21)
- Root cause of empty samplers: GT6 registers 4 display buffers (0x0, 0x660000, 0xCC0000, 0x1320000; `RT_OFFDBG=1` shows `disp=1` for all) and renders the dialog backdrop by sampling the *other* display buffers as textures. The backend mapped all draws to the backbuffer but only bound the screen copy for display-**sized** textures (1216x684 != 1280x720), so the samplers read zeros. Matches the upstream docs (`rsx-first-draw-fix.md`: "by registered offset (preferred)").
- Fix 1 (`rsx_d3d12_backend.c`): bind the screen copy for any texture whose raw offset `cellGcmOffsetIsDisplay()` (incl. offset 0). Replaces the SCREEN_AS_TEX_SAFE size hack.
- Fix 2: the 1440x1080 fmt 0xE5 sampler is the **zeta** buffer (0x1980000) read as texture before any write -> depth 0 = black triangle. `ZETA_FILL` (default on) fills never-written zeta-offset textures with 0xFF (cleared depth 1.0).
- Result (`docs/analysis/eu-language-select-dialog.png`, frame 2500): dialog panel, title bar, 4 menu rows, highlighted row; text is still solid grey/blue glyph blocks (8x8/128x128 atlas content wrong) and the backdrop gradient (yellow/green/cyan) is likely wrong.
- Test tooling: `scripts/cap-gt6.ps1 -Name x -Env "K=V,K=V"` = one call run + frame capture + PNG + pixel stats. DRAW_LIMIT bisect is unreliable (frame content differs per run); use RT_OFFDBG / TEX_MARKEMPTY / TEXEMPTY logs first.
- Upstream comparison: no new upstream commits; US-disc docs stuck at black window; ROADMAP M2 items already done here. Useful: `rpcs3-oracle.md` (RPCS3 in tools/RPCS3 as visual reference), `host-font-sync-fix.md` (fonts load here via pfs override, OK).

## Text blocks = stencil glyphs + depth-as-texture (2026-11-21)
- Glyph textures (DXT1 128x128, DXT5 36x36, DXT5 8x8) are fine: `TEXDUMP="86 88 A8"` hook dumps raw bytes + decoded BMPs, pitch == row bytes everywhere. Not the cause.
- Manifest now prints `zeta=` / `zs=`. Glyph passes (op005..036: vs=0, cmask=0) have zeta 0x1980000, stencil test ALWAYS + INVERT/INCR/DECR on bit 7 (stencil-then-cover). Cover passes (op037/057, vs=7, cmask=F, zs=0) sample the zeta as 1440x1080 fmt 0xE5 texture, crossbar 0xAAFF.
- Old behaviour: OffDS (depth -> colour copy via ds_convert) only for off-screen RT / depth-only passes; GT6 draws to the display buffer, so ZETA_FILL=0xFF made solid blocks.
- Fix (patches/gt6-rsx-zeta-depth-text.patch, apply after gt6-rsx-display-tex-zeta.patch): display-target draws whose zeta is sampled later in the frame get an OffDS (sized >= guest texture 1440x1080, `zeta_sampled()`); ds_convert also runs when the sampling draw does not write depth/stencil; the colour copy SRV applies the guest crossbar (`DS_REMAP=0` = old default mapping).
- Result: `docs/analysis/eu-language-select-text.png` — readable text ("Sprache auswählen", "Schließen", Ελληνικά, Čeština, Magyar).
- Still wrong: backdrop gradient (black/white diagonal, differs per run = screen-copy feedback), stray blue blob right of row 1.

## 2026-11-21 — Sprachauswahl-Hintergrund (RPCS3-Vergleich)
- RPCS3 (Firmware installiert, `tools/RPCS3`) zeigt: einheitlich dunkler Hintergrund, dunkles transluzentes Panel, weißer Text.
- Unser Bild hatte eine weiß/schwarze Diagonale: Panel-/Hintergrund-Draws (fp 04E526C1/04E52681) lesen col0 aus Attribut 3, das der Guest als altes Array (fmt 0x1445, Stride 20, unzusammenhängende Mesh-Daten) aktiv lässt.
- Fix: a3 nur für Text-Quad-VS (fp 0x4E739C1, a3.x = Palette-Index in vp_c[]) vertrauen, sonst a3 am BEGIN_END deaktivieren (vor Layout-Bau), col0 aus VERTEX_DATA4F. Env `A3KEEP=1` = altes Verhalten. Patch `patches/gt6-rsx-ignore-stale-a3.patch`, Debug-Hooks `patches/gt6-rsx-debug-hooks.patch`. Ergebnis `eu-language-select-bg.png`: blauer Titel, Panel, Zeilen, Cursor wie RPCS3.
- Titel-Farbe-Nebenwirkung damit behoben. Offen: "Schließen" etwas dunkler als RPCS3 (evtl. Hover), weitere fps mit a3-Palette nicht gefunden.

## 2026-11-21 — Eingabe an der Sprachauswahl (negativ)
- `PAD_SCRIPT` (Leerzeichen als Trenner, Komma trennt `cap-gt6 -Env`!) mit DOWN/CROSS/CIRCLE/START/RIGHT/LEFT/TRIANGLE/SQUARE: Pad-Daten kommen an (neu: `PAD_TRACE=1`, `patches/gt6-pad-trace.patch`, len=28, ~33 Polls/s, 40 Polls gehalten), aber der Dialog reagiert nicht. Frame bei 3000 und 3500 pixelidentisch (auch Cursor statisch) -> UI-Zustand läuft nicht weiter, Ursache liegt vor der Eingabe (vermutlich wartet das Spiel auf ein Ereignis, nicht auf Tasten).
- Beobachtung: ~1 `cellSysmoduleIsLoaded(NP2)` pro Frame, 179x `port_send(port=1)` aus func_00A466A4+0x771. Nicht weiter verfolgt.
- Nächster Schritt: RPCS3 am selben Dialog mit Tastatur bedienen und beobachten, welcher Zustand folgt; dann die Event-Queue (port_send/func_00A466A4) bzw. Dialog-Zustandsmaschine untersuchen.
- RPCS3-Gegenprobe (ohne Eingabe): Zeile 1 ist dort bereits hervorgehoben (heller Rahmen/Füllung), Cursor an gleicher Stelle. Unsere Ausgabe hat keine Hervorhebung. Draw-Liste (cap_col2, `VTX_COL=1`): nur fps 0x4E526C1/0x4E52681/0xF8FFDC1 mit konstantem col0 aus VERTEX_DATA4F, Alpha-Serie 0.5..1.0 (Fade-In) -> kein fehlender Render-Pfad erkennbar. Schluss: fehlende Hervorhebung und ignorierte Eingabe haben vermutlich dieselbe Ursache (Dialog-Zustand nicht "aktiv"/Fokus nicht gesetzt), nicht a3. GUI-Automation gegen RPCS3-Fenster ist hier unzuverlässig (Mehrmonitor-Koordinaten); lieber RPCS3-Log/PAD-Config nutzen.

## ps3recomp docs check (GETTING_STARTED, FAQ, DIAGNOSTICS) + HOTREAD run

- ps3recomp docs contain nothing on pad input, sysutil callbacks or menu focus; no GT6 mentions. Useful: diagnostic env knobs (`PPU_HOTREAD`, `PS3_CALLTRACE[_FROM/_TO/_LR]`, `PS3_SCENTER`, `LV2_ERRDBG`, `PS3_EVF_FORCE`, `FLOW_CONDKICK`), all already present in local third_party.
- Run with `PPU_HOTREAD=1 PPU_SPINBT=1 LV2_ERRDBG=1` on the language-select frame: 1384x `[HOTREAD] spinning on 0x01681E80 (=0x01681E00) guest cia=0x014E0898 lr=0x00B6E52C`. 0x014E0898 = entry of dialog thread "PDI"; 0x01681E00 is the WWS `GPUSyncArray` workload data EA (wid 5, see spu-spurs.md), 0x01681E80 = its +0x80 word.
- No `PM NOT LIFTED` line any more, no LV2 errors. Only `_cellSpursWorkloadFlagReceiver2(wid=5 set=1)` once.
- Hypothesis (unproven): the PDI worker polls a lock-free queue word that the GPUSync SPURS job (or its completion signal) never updates, so the dialog state machine never advances -> no highlight, no input reaction.
- Next: find the writer of 0x01681E80 (WWATCH on that address), check whether wid 5 job ever runs (`spu_run_policy_module` log), compare against RPCS3.

### Follow-up: GPUSyncArray hypothesis mostly refuted
- All 8 WWS workloads (wid 0-7) are admitted and run the PM repeatedly (`SPURS_PM_TRACE`): wid 5 = 61 runs, each `END status=0x2 pc=0x9C0 polls=0 exited=1`. wid 5 is the workload-flag receiver (recv=5, flag word 0xFFFFFFFF = not raised; `SPURS_W5DIAG` patch `patches/gt6-spurs-w5diag.patch`). No scheduling starvation.
- 0x01681E80 is the head word of a circular list inside the job-chain struct (init `<- 0x0` by func_00B6E278, then `<- 0x1681E00` = self pointer = empty list by func_00A6E72C). No later writer (PPU_WWATCH). The "spin" is func_00A6EBD8 (called from func_00B6E4E8 = per-frame GPU sync), a u16 counter walk: the frame loop still flips, so this is a per-frame poll, probably not THE stall.
- Open question: PMs exit with polls=0 and never DMA wid 5's list at 0x1681E80 (wid 6 does DMA 0x1681C80). Unknown whether that is correct (empty list) or a missing PPU-side push. RPCS3 comparison of job-chain traffic would decide.
- ps3recomp docs (local copy under third_party/ps3recomp/docs, 46 files) read: no pad/menu/sysutil material. Useful tools: `PS3_DEBUG=<file>` debug console (`threads`, `mem`, `stat`), `SPU_INTERP_STATS`, `SPURS_PM_TRACE`.

## Input path traced (2026-11-21)

`PAD_TRACE=1` now also prints the pad buffer EA and a guest stack on the first poll with a button set (`patches/gt6-pad-trace.patch`).
- Pad data reaches the game: buffer EA 0x0165ADE0 (inside the pad manager struct at 0x0165AD40). The poll runs on the PDI/UI thread (tid 26, entry func_00A304D0 -> func_00A3D114), no separate pad thread.
- `PPU_RWATCH=165ADE8,4` + `PAD_SCRIPT=0.1:0x4000`: the pad manager update `func_00A39CD8` and `func_00B90614` read D2 = 0x40 (CROSS) as nonzero, so the buffer is consumed (len 0x1C, port status 0x7E, D1/D2 read per frame, then func_00A38FC4/func_00A38FE8 edge/hold processing).
- So the input does NOT get lost before the game: the dialog's state machine ignores a delivered CROSS. Remaining suspects: widget focus/active flag never set (same cause as the missing row-1 highlight), or a gate on another sysutil event/callback.
- Next: trace readers of the pad-manager OUTPUT (hold/press masks) and what the dialog widget update checks before acting on them.

## Maus-/Timing-Experimente (2026-11-21)
- Captures mit `-Frame 300` sind zu frueh (schwarz); Dialog erst ab ~Frame 2500 sichtbar. userdb0101.dat vor jedem Boot nach work/ARCHIV (Boot-2-Bug).
- Pad-Press nach sichtbarem Dialog (Flip-Clock 2800-2900): keine Reaktion.
- cellMouse: Game ruft nur `cellMouseInit(7)`, danach KEIN `cellMouseGetData` (MOUSE_TRACE=1, 3000 Frames, 0 Zeilen). MOUSE_FAKE (Patch `patches/gt6-mouse-fake.patch`) aendert das Bild nicht (cap_ms1). Maus-Hypothese damit widerlegt: Zeiger wird ohne Mausdaten gezeichnet.
- Offen: Row-1-Highlight/Eingabe; naechster Schritt Draw-seitig pruefen (Highlight-Draw fehlt?) oder Pad-Leser func_00A39CD8 Ausgabe -> Widget-Gate.

## Eingabe-Pfad Teil 2: Listener, Fiber, WaitFlag (2026-11-21)
- Frame-5000-Zustand identisch zu Frame 2600 (black=87,4 %, ops=158): Dialog ist stationaer.
- RPCS3-Log: cellMusicInitialize2 mit Callback; Stub in `stubs.cpp` queued jetzt INITIALIZE_RESULT (`MUSIC_NOCB=1` aus). Kein sichtbarer Effekt.
- Pad-Manager 0x0165AD40: 7 Listener-Knoten (Stride 0xE0, erster 0x165B1A8, vtable 0x0148A128), `func_00A390E4` kopiert 0x80 Byte Pad-Daten nach listener+0x54. RWATCH 165B1A8,700: nur func_00A39CD8 liest +4/+0xC, KEIN Leser der kopierten Pad-Daten nach dem Boot. Das Dialog-Skript pollt also keine Eingabe.
- Skript-VM laeuft in genau einem cellFiber (RunFibers tid 31, ea 7FF1A800, opd 014E0848), immer READY (Yield-Schleife). `PAD_LISTENERS=1`, `FIBER_DUMP=1`, `WAITFLAG_LOG=1` (Diagnose, Patch `patches/gt6-pad-listeners-fiber-dump.patch` + stubs.cpp).
- WaitFlag-Log: einziger Waiter flag=0x7FEDA084 value=0 cur=1, lr=0x00A2F44C (func_00A2F410, Thread-lokales Objekt). Der Waker (func_00A2F8B8 "resume") wird nie aufgerufen; func_00A2FAD0 ("wake all", lr 0x567DA4) genau einmal im Boot. Beide haben keine statischen Aufrufer (nur indirekt).
- Bewertung: die Fiber ist vermutlich ein Idle-Worker, kein Eingabe-Gate. WaitFlag-Hypothese nicht bestaetigt, nichts geaendert (2-ms-Bailout bleibt).
- Nicht erledigt: "Schliessen"-Helligkeit, Row-1-Fokus, Eingabe. Naechster Schritt: Produzenten-Seite (wer ruft func_00A2F8B8 indirekt) per Laufzeit-Hook auf ps3_indirect_call-Ziel 0xA2F8B8 suchen, oder den Fokus-Setter im Widget-Baum (Draw-Liste cap_col2 vergleichen) direkt suchen.
- Hinweis Tooling: cap-gt6 `-Env` ist komma-getrennt, Werte mit Komma (PPU_WWATCH=addr,len) gehen nicht. WWATCH-Ausgabe heisst `[ww]`, RWATCH `[rwatch]` (in .err).

## WaitFlag real wait state (2026-11-21)
- Korrektur: Der Fiber (sched 7FED9600, ea 7FF1A800) ist kein reiner Idle-Worker. tid 31 fuehrt die UI/Script-Update-Kette aus und haengt danach in cellFiberPpuRunFibers.
- Experiment `WAITFLAG_REAL=1`: neuer Zustand F_WAIT_FLAG in cellFiber.c (`cellFiberPpuWaitFlagEx`), RunFibers kehrt zurueck wenn nur Flag-Waiter uebrig sind. Default aus.
- Ergebnis: nur 1 WaitFlag-Aufruf (flag=7FEE8084 value=0 cur=1, lr=00A2F44C), Fiber bleibt geparkt, Waker (A2F8B8/A2FAD0) feuert nie. Bild schlechter (black=99 %, ops=17 statt 158). Hypothese "RunFibers-Rueckkehr allein loest Fokus/Input" widerlegt.
- Offen: wer ruft A2F8B8/A2FAD0 auf (Timer/Event-Quelle fehlt vermutlich). WAITFLAG_LOG/WAITFLAG_CLEAR/WAITFLAG_REAL sind reine Diagnose-Schalter.

## Waker-Suche: Fiber-Thread-Klasse (2026-11-21)
- RPCS3-Log (tools/RPCS3/log/RPCS3.log): Thread 9qstY (= unser tid 31, Skript/UI) ruft cellMusicInitialize2, 12 ms spaeter cellMusicSetVolume2, danach erzeugt er CYYqg, AEIVZ, XyGIK, ZWAP (ZWAP pollt cellMusicGetPlaybackStatus2 ~14000x). RPCS3 legt 55 Threads an, wir 39 (es fehlen CYYqg, AEIVZ, ZWAP). Unser Lauf erreicht SetVolume2 nie (Aufrufer func_00888B20 aus 0x888F80/0x8898EC = Skript-Natives).
- Stubs ergaenzt (additiv): cellMusicGetPlaybackStatus2 (schreibt STOP=0), SetVolume2/Finalize2/Set+GetSelectionContext2/SetPlaybackCommand2/SelectContents2 -> CELL_OK. Bild unveraendert (ops=158), Schluessel ist also nicht der Rueckgabewert.
- Waker-Struktur: A2F8B8 (resume) und A2FAD0 (wake all) sind vtable-Slots 5/7 der Thread-Klasse bei 0x1489de0 (Slot2 A2F93C, Slot3 A2FC54 = create-thread mit Name). Einzige CheckFlags-Aufrufer: A2F8B8 und A2FAD0 (lr A2F8EC / A2FB38); einziger WaitFlag-Aufrufer: A2F410. Klasse wird einmal von func_00A14824 aufgebaut (A2F93C und A2FC54 je 1x per PS3_CALLTRACE_TO).
- Fiber-Body func_00A2F464: Schleife "A2F410 (schlafen) -> Task obj+0x28". Task = 0x568A0C (-> 0x568658, State-Machine), laeuft nur 4x (PS3_CALLTRACE_FROM=A2F464), danach schlaeft der Fiber dauerhaft.
- Offen: wer indirekt Slot 5 (+0x14) aufruft. Statische Suche nach `lwz r,0x14(r)`+bctrl liefert 453 Treffer (zu breit); Hook auf Slot-5-Aufrufe per PS3_CALLTRACE_TO=A2F8B8 feuert nie. Naechster Hebel: Task 0x568658 State-Machine lesen (welcher State schickt den Fiber schlafen), und per WWATCH auf obj+0x40 (Flag 7FEE8084) pruefen ob jemand nur schreibt statt resume zu rufen.

## Waker-Suche: WWATCH auf Fiber-Thread-Objekt (2026-11-21)
- Flag-Adresse variiert pro Lauf (7FEDA084 / 7FEDC084 / 7FEE8084), statisches PPU_WWATCH trifft daneben. Neu: `WAITFLAG_WW=<signed offset>` (mit WAITFLAG_LOG) schaltet den Write-Watch beim ersten WaitFlag dynamisch auf flag+offset scharf.
- Ergebnis: weder Flag (obj+0x40) noch Task-Feld/Umgebung (obj+0x24..0xA4, PPU_WWATCH_LEN=0x80) werden nach dem ersten Sleep je beschrieben (60 s). Fiber ist ein Idle-Worker, dem nach den 4 Task-Laeufen keine Arbeit mehr zugestellt wird. Waker-Suche ist damit Sackgasse: Ursache liegt davor (Job-Submitter / Skript-Thread kommt nicht weiter), nicht im fehlenden Resume.
- Naechster Hebel: Submitter des Tasks 0x568A0C (Schreiber auf obj+0x28 VOR dem ersten Sleep, Watch frueher scharf schalten, z.B. beim Create A2F93C) und Vergleich mit RPCS3-Threads CYYqg/AEIVZ/ZWAP.

## Fiber-Thread = "processEventLoop" (2026-11-21)
- Neu: `PS3_CALLTRACE_ARM=<off>` (+ `PS3_CALLTRACE_ARM_R4=1`) schaltet den Write-Watch beim ersten Treffer von `PS3_CALLTRACE_TO` auf r3/r4+off scharf; WAITFLAG_LOG dumpt das Thread-Objekt (0x80 Bytes) beim ersten WaitFlag.
- Erzeugung: func_00A14824+0x345 ruft slot2 A2F93C auf Manager 7FFBE280, +0x46D ruft A2FC54 (r3=Manager, r4=Objekt). Objekt-Adresse variiert (7FEDA044/7FEE6044/7FEE8044), Manager 7FFBE280 stabil.
- Objekt-Dump: vtable 0x1489E58, +4 Manager, +8 Name **"processEventLoop"**, +0x28 = 0x014BF800 (Tabelle, erster Eintrag opd 0x568A0C = Task), +0x40 Flag (=1 schlafend). Task 0x568A0C ist also die Event-Schleife, Fiber ist Event-Worker.
- Watch r4+0x28 ab A2FC54-Eintritt: danach KEIN Schreiber auf obj+0x1C..0x9C. Event-Worker wird nach Lauf 4 nie mehr gestupst (Flag/Task-Feld unveraendert).
- Hypothese: Wake kommt von einer Event-Quelle (Pad/Sysutil/Timer-Event -> Queue-Push -> Wake). Zu pruefen: welche Producer-Funktion in RPCS3 laeuft (Thread-/Syscall-Log), z.B. sys_event_queue_send / sys_timer / sys_event_flag in RPCS3.log vs unser Lauf.

## Event-Producer: RPCS3.log vs unser Lauf (2026-11-21)
- `cellFiberPpuCreateFiber` (NID 7C2F4034) wird im ganzen Lauf **einmal** gerufen (tid 1, func_00A14824+0x54 -> processEventLoop). Das ist bei uns kein Defekt: es gibt keine weiteren Fibers, die RPCS3 haette.
- PDIPFS-Install, savedata AutoLoad2 (PDI-Threads), Trophy-Init laufen bei uns wie in RPCS3 (Reihenfolge der .fdupm identisch, wir sind weiter als das RPCS3-Log).
- Abweichung gefunden: Netz-Init. RPCS3: `cellNetCtlGetInfo(0x15)` -> NOT_CONNECTED (0x80130108), danach legt das Spiel CYYqg/AEIVZ/XyGIK an. Bei uns lieferte GetInfo OK und `getsockname` -1 (Stub) -> CYYqg/AEIVZ fehlten. Fix: getsockname -> 0 + sockaddr_in (GETSOCKNAME_FAIL=1 = alt), GetInfo(HTTP_PROXY_CONFIG) offline -> NOT_CONNECTED (NETCTL_PROXY_OK=1 = alt). Jetzt entstehen CYYqg, AEIVZ, XyGIK wie in RPCS3.
- Weiter offen: ZWAP (Thread, pollt cellMusicGetPlaybackStatus2 alle ~75 ms, 14106 Calls in RPCS3) wird bei uns nie angelegt; `[PlaybackStatus]` 0 Calls. Dialog-Pad-Input unveraendert (noch nicht neu geprueft).
- Neues Tooling: PS3_SC_COUNT (Syscall-Zaehler), PS3_HLE_STACK=<nid-hex> (Gast-Stack der ersten 3 Calls). NID-Rechner: `third_party/ps3recomp/tools/nid_database.py compute_nid(name)`.

### ZWAP-Gate gefunden (2026-11-21)
- Ursache: cellMusicInitialize2-Callback bekam als arg2 den User-Pointer statt Zeiger auf s32 CELL_OK. Gast-Wait (func_008890A4/00889180) las 0x7FFE2000 als Fehler -> func_00889838 sprang am SetVolume2 vorbei -> ZWAP nie erzeugt.
- Fix (stubs.cpp): arg2 = Zeiger auf Null-Wort im Gast-Heap (g_sys_mem_bump_ptr). Jetzt: SetVolume2 aufgerufen, ZWAP tid=42 erzeugt wie in RPCS3.
- Offen: GetPlaybackStatus2 wird in 60 s noch nicht gepollt; Dialog/Pad/Focus nicht neu geprueft.

### Ergebnis nach ZWAP-Fix (2026-11-21)
- GetPlaybackStatus2 wird jetzt gepollt (HLE-Trace: NID 0x648B7611, lr 0x008888E8); SetVolume2 lr 0x00888B5C.
- Pad-Eingabe wirkt: `PAD_SCRIPT=0.1:0x4000` (CROSS) schliesst den Sprachdialog, Frame 2500 zeigt "Sony Computer Entertainment presents" (work/cap_zw2). Ohne Eingabe bleibt der Dialog (work/cap_zw1).
- Ursache der ignorierten Eingabe war also der fehlende Music-Init-Callback-Payload (Boot-Fortschritt), nicht der Pad-Pfad.
- Offen: Row-1-Hervorhebung im unbedienten Dialog fehlt weiterhin (visuell, RPCS3 zeigt sie); "Schliessen" dunkel.

### Dialog-Schleife nach Auswahl (2026-11-21)
- CROSS auf dem Sprachdialog (PAD_SCRIPT=20:0x4000) -> Frame 2500 "Sony Computer Entertainment presents", ~3000 Legal-Text (Polyphony-Logo, Fade), ~3300 Sprachdialog wieder da (identisch). Reproduzierbar (work/cap_zwq3000, cap_zwq3300).
- Pad wird die ganze Zeit gepollt (5602 cellPadGetData in 90 s, HLE-Trace). Frame-Zaehler != Wandzeit/Flips: PAD_CLOCK=flips taugt hier nicht, Wanduhr-Press funktioniert.
- stdout von run-gt6 geht bei Kill verloren (gepuffert): spaete Log-Zeilen ([cellPad] PAD_SCRIPT ..., [cellFs]) fehlen -> nicht als "Press nicht gefeuert" lesen. stderr (HLETRACE) ist verlaesslich.
- Hypothese: Sprachwahl wird nicht persistiert/uebernommen (Schreibpfad: Config/Savedata), daher fragt der Boot erneut. Naechster Schritt: stdout-Flush (setvbuf/PS3_*-Flag) und [cellFs]-Open/Write-Folge zwischen Press und Dialog 2 loggen; mit RPCS3.log (tools/RPCS3/log) vergleichen.

### Dialog-Schleife: Befunde (2026-11-21, spaet)
- Mehrfach-CROSS (alle 8 s ab 20 s, PAD_SCRIPT per Prozess-Env) -> Dialog bleibt bei Frame 4500 und 6000; jede Auswahl startet presents -> legal -> Dialog neu.
- Nach dem Press KEINE neuen Dateizugriffe ([fs]/pfs-Trace nur bis LanguageSelectRoot.gpb + PDIPFS K/CF) und kein Sprach-/Sysutil-HLE-Call (Fenster-Histogramm: nur lwmutex/lwcond/Spurs/Gcm/Pad). Die Schleife ist reine Gast-Logik: Sprachergebnis wird nirgends persistiert.
- Fresh userdb (richtiger Pfad work/gt6_hdd0/game/BCES01893/USRDIR/db/userdb0101.dat) aendert nichts.
- Tooling: GT6_UNBUF=1 (main.cpp) setzt stdout ungepuffert. cap-gt6.ps1 -Env splittet an Kommas -> PAD_SCRIPT mit mehreren Events als Prozess-Env setzen, nicht ueber -Env.
- Naechster Schritt: Gast-seitig verfolgen, was nach dem Dialog-Ergebnis gelesen wird (Callers von LanguageSelect-Result; WWATCH auf das Ergebnisfeld), bzw. ob das Ergebnis durch einen noch fehlenden Zustand (z.B. Sprachwert aus Profil/Param) verworfen wird.

## Dialog: Pad-Press skippt nur Logos, Polling-Vergleich (2026-11-21)
- Jeder Press (CROSS oder DOWN) fuehrt nur vom ersten Screen zur Logo-Sequenz (SCE presents ~2500, Legal ~3000); danach erscheint derselbe Dialog (~3300). Der Dialog selbst verbraucht kein Pad (Hauptbug offen). Nach dem Press: keine neuen fs-Opens, keine Sysutil/Language-HLE-Calls, keine userdb-Writes -> reine Gast-Logik.
- Polling-Vergleich: RPCS3 Haupt-Thread pollt `cellSysmoduleIsLoaded(0x38)` (~11000x, 16 ms) aus func_00F93860; unser Lauf ruft dieselbe Funktion (Aufrufer func_00A86B38, lr A86B64, ~33/s). Kein Unterschied -> kein Diskriminator. ZWAP pollt in beiden cellMusicGetPlaybackStatus2.
- RPCS3.log enthaelt keine Pad-/Kb-Aufrufe (nur Import-Tabelle) und endet am Dialog; keine Aussage zu Eingabe-Verhalten moeglich.
- Naechster Hebel: Draw-Seite (158 Ops, work/cap_zw1/manifest.txt; Highlight/Row-1 als Quad evtl. vorhanden aber nicht korrekt gerendert, Text via zeta/Stencil-Pass) und Widget-Fokus im Skript-VM.
- Linker Stick voll aus (PAD_STICK=255,255,128,128,15,1000) bewegt den Zeiger nicht (cap_stk2 == cap_zw1). cellMouseGetInfo/KbGetInfo/PadGetInfo2/KbRead werden je Frame gepollt (2487x), cellMouseGetData nie, auch nicht mit MOUSE_FAKE (Port 0 connected). Zeiger sitzt fest am rechten Rand von Row 1 (~830,340); Eingabequelle des Zeigers unbekannt.

## Dialog-Eingabepfad: Pad-Konsumenten (2026-11-21)
- cellPadGetData (NID 0x8B72CDA1) 1x/Frame aus tid-26-Kette A304D0->A3D114->A37E2C->A1C1F8->2F94F8->A21E40; schreibt len+button[] direkt nach Gast 0x165ADE0. Pad-Manager 0x165AD40, 7 Listener (Stride 0xE0, ab 0x165B1A8, vtable 0x148A128, Index bei +0x40, Erzeuger func_00A3938C).
- func_00A390E4 kopiert 0x80 Byte nach listener+0x54 (Button-Wort +0x58). Listener 0 bekommt Presses korrekt (+0x58=0x40 bei DOWN).
- func_00A395F0 (Decoder) nur aus func_00811370 (tid 29, pro Frame) mit Listener 6 (0x165B6E8, nie Daten) -> vermutlich Debug-/Tastensequenz-Detektor, NICHT der Dialog-Konsument. Hack "Listener 6 -> 0" aendert den Dialog nicht (cap_exp*, alle == cap_zw1).
- RWATCH auf Listener-0-State: waehrend der Dialogphase (100 s, DOWN alle 3 s) liest kein Gast-Code +0x40..0x58. Dialog-Eingabepfad bleibt unbekannt.
- Per-Frame-HLE-NIDs identifiziert: 0x5BAF30FB cellMouseGetInfo, 0x2F1774D5 cellKbGetInfo, 0xACEE8542 cellGcmSetFlipImmediate, 0x189A74DA cellSysutilCheckCallback, 0x1573DC3F sys_lwmutex_lock; 0xFF0A21B7 = Legacy-SDK-Stub. Nur Info-Polls, keine Datenabfrage.
- Zeitfalle: Dialog erscheint spaet (~Frame 3300); Press bei 3 s testet nur die Logo-Phase. cap-gt6: Name wird "cap_" vorangestellt, >=90 s fuer Frame 4500.
- Temp-Probes/Hack in ppu_recomp_018/023 zurueckgenommen (work/ppu018.bak, ppu023.bak), Build sauber.
- Naechster Schritt: Konsument ueber Draw-/Layout-Seite suchen (Fokus-Quad-Op in cap_zw1/manifest), oder Gast-Callgraph ab GPB-Widget-Update (LanguageSelectRoot) tracen.

## Menue-Run (autonom, Ergebnis: Hauptmenue NICHT erreicht)
- Baseline bestaetigt: Frame 4200 -> black 87.4 %, ops=158 (cap_base1).
- PAD_SCRIPT CIRCLE bei 130 s: Dialog unveraendert (cap_circ1).
- Erneut RWATCH/CALLTRACE: Pad-Rohdaten lesen nur A39CD8 (Mapper), A390E4/B90614 (Kopie nach Listener+0x54), A395F0 (Start). Kein skalarer Konsument in der Dialogphase; A39CD8 ohne indirekte Calls. RWATCH sieht lvx-Loads nicht -> Vektor-Konsument nicht ausgeschlossen.
- RPCS3-Orakel (tools/RPCS3, --no-gui): haengt >240 s auf "Precompiling shader interpreter variants" (leerer Balken); kein Dialog-Referenzablauf gewonnen. Verworfen.
- Naechster Schritt: Vektor-Load-Hook (lvx/lvlx) analog ppu_rwatch_hit bauen und Listener-State 0x165B1A8+0x54 beobachten; alternativ Draw-Seite (Fokus-Quad) tracen.
- PPU_RPAGE=<hex ea>[,len] (patches/gt6-rpage-probe.patch, Runtime, nur Diagnose): PAGE_NOACCESS-Lesewatch inkl. Vektor-Loads, loggt je (Art, Gast-Fn) 3 Treffer. Lauf 230 s auf 0x165B1A8,0x540 (Listener 0/1+): Leser nur A39CD8 (Mapper), A390E4/B90614 (Kopie), A3CE18 (memcpy-artiger 0xFC-Kopierer, einmalig im Boot) und HLE-memcpy (guest-fn 0). Kein Vektor-Konsument -> Hypothese "unsichtbarer lvx-Leser" widerlegt. Konsument liest nicht aus dem Listener-Block, sondern aus einer Kopie/Ableitung an anderer Stelle (oder Dialog laeuft nicht ueber diesen Pad-Pfad).
- Baseline nach Patch: cap_base2 Frame 4200 black=87.4% ops=158 (Lauf braucht auf lastigem Rechner >200 s: -Seconds 320 nehmen).

## Roadmap M2: Determinismus-Soak (2026-11-21)
- Neu: `scripts/soak-gt6-eu.ps1` (N Boots, Fingerprint = SHA-256 der geladenen Asset-Pfade; altes `soak-gt6.ps1` ist veraltet, stdout-Verlust ohne GT6_UNBUF). `scripts/hunt-menu-branch.ps1` (bricht Runs ab, sobald Dialog-Pfad erkannt).
- Soak 8 Boots: 7x 43 Assets (Dialog-Pfad), **1x (Run 3) 47 Assets ohne LanguageSelectRoot.gpb, stattdessen arcade/option/gtmode/garage/gtauto .mpackage** -> Boot nahm den Hauptmenue-Pfad. Soak 10 Boots: 10/10 identisch. Soak 5 Boots unter CPU-Last: 1x langsamer Lauf (42 Assets, Dialog noch nicht erreicht nach 100 s). Hunt: 40 Boots, 0 Menue-Pfad.
- Gleiche Gast-Eingaben bis nach SettingProject.gpb (Log-Diff: nur Thread-/SPU-Reihenfolge verschieden), also Race-Verzweigung im Gast, kein Dateizustand (userdb-Hash aendert sich jeden Lauf). Ursache offen; 1 von ~70 Boots, Log des Treffers wurde vom Folge-Soak ueberschrieben (Lehre: Soak-Logs pro Soak in eigenem Ordner halten).
- Syscall 327 (2x beim Boot, Stub OK): kein beobachteter Effekt.

## 2026-11-21 — sys_mempool + lgFF
- Hunt "menu path" hit was false positive (arcade.mpackage loads in every boot before LanguageSelectRoot).
- sys_mempool_create was ENOMEM stub (caller 0xA5E5D8). Implemented real pools; guest now creates event queue + "lgFF" thread + TM_FFB workers like RPCS3.
- Result: baseline intact (Frame 4200, ops=158, work/cap_mempool1), dialog still w/o row-1 highlight, pad ignored. Hypothesis "mempool failure starves processEventLoop" NOT confirmed.
- Next: real sys_usbd_initialize/get_device_list, sys_timer events, compare processEventLoop wake source.

## 2026-11-21 — nach mempool-Fix: Pad + Sprache (2 Versuche, beide ohne Effekt)
- PAD_SCRIPT "120:DOWN 124:CROSS" mit lgFF-Thread: Dialog bei Frame 4800 unveraendert (work/cap_lgff_pad, ops=155), Zeiger fehlt dort (Schleife press->presents->legal->Dialog, Zeitpunkt unklar).
- PS3_LANG=en-gb: Dialog erscheint weiterhin (englisch: "Select Language", "XMB Menu Setting (English)"), Zeile 1 ohne Highlight (work/cap_lang_engb, ops=138). Dialog ist also der Erststart-Sprachdialog, nicht von der Systemsprache abhaengig.
- Offen: Fokus/Highlight auf Zeile 1 wird nie gesetzt; Press fuehrt zu Logo-Schleife ohne Persistenz.
- KORREKTUR: der erste Pad-Test oben war ungueltig (PAD_SCRIPT kennt nur `<sek>:<hexmaske>`, keine Namen -> 256 Nullpresses). Gueltige Wiederholung: `PAD_SCRIPT="120:0x0040 126:0x4000"` (Log bestaetigt beide Presses) -> Dialog bei Frame 4800 unveraendert, ops=158 (work/cap_lgff_pad2). Kein AdjustScreenRoot, keine neuen Dateizugriffe.
- Kontext aus movie-sequence-trace: display_sequence_gt6 = presents -> save-gate -> sequence-gate -> optionales LanguageSelectRoot.open -> AdjustScreenRoot. Der Dialog sitzt also NACH den Logos; der Press muss ihn schliessen. Savedata BCJS37016-GAME6/BKUP6 liefern isNew=1/-4 (erwartet beim Erststart).

## Script-VM-Seite des Sprachdialogs (ADCH-Disassembly)

Quelle: `work/boot_adc.txt` (tools/adch_disasm.py auf boot.adc), Modul `LanguageSelectRoot`.

- `onFocusNotify(context,new_index,old_index)`: holt `getItemWidget(new_index)` und ruft `LanguageSelectRoot.setFocus(item)`.
- `onActivate(context)`: spielt `main.sound.play("ok")`, liest `item.language` des `focus_index`. Bei `SYSTEM`: Option zuruecksetzen, dann `LanguageSelectRoot.close(context)`. Sonst `DialogUtil.openConfirmDialog(DEFAULT_NO)`; bei Ja `pdistd.SetLanguage`, `LangUtil.apply`, danach `close`.
- Beide Handler werden nativ vom ListBox-Widget aufgerufen (Registrierung der Event-Namen `onVisibleNotify`/`onFocusNotify` bei EMAIN 0x600900..0x600A24, Widget-Felder +0x22c/+0x240/+0x24c). `onActivate` hat keine lis/addi-Referenz in EMAIN (Name wird anders geladen).
- Konsequenz: Fehlende Zeile-1-Hervorhebung = `onFocusNotify` kommt nie an (oder `focus_index` bleibt -1). Pad-Eingang wird vom Mapper geliefert (siehe oben), erreicht aber das ListBox-Fokussystem nicht.
- Offen: Aufrufer der Fokus-/Decide-Pfade in 0x600A50 (setzt +0x24c = +0x240, Fokus-Tauglichkeitspruefung) per `PS3_CALLTRACE_TO=600A50` + `PS3_CALLTRACE_AFTER=<sek>` tracen und pruefen, ob die Funktion nach Dialog-Erscheinen jemals laeuft.
- Neu: `PS3_CALLTRACE_AFTER=<sek>` (patches/gt6-calltrace-after.patch) schaltet den Calltrace erst nach N s Wandzeit scharf.

- Lauf ct_listbox (PS3_CALLTRACE_TO=600A50, _AFTER=150, 200 s, Dialog erreicht, usercmd #3584): 0 Trace-Zeilen. Calltrace erfasst nur indirekte Aufrufe; 0x600A50 wird per direktem bl erreicht -> Ergebnis NICHT aussagekraeftig. Naechster Schritt: PPU_CALLTRACE auf Lifter-Ebene fuer direkte Aufrufe (Funktions-Entry-Probe) oder PS3_CALLTRACE_FROM/Caller der Widget-Klasse (vtable) statt Zieladresse.

## 2026-11-21 — Entry-Probe 0x600A50 + Vtable-Befund
- Direkte Entry-Probe func_00600A50: 0 Aufrufe im vollen Lauf (Dialog-Phase erreicht, Baseline black 87.4 %, ops=158). Die ListBox-Fokuspruefung laeuft nie.
- 0x600A50 ist virtueller Slot +0x1F4 der Vtable 0x1460530 (Descriptor 0x14C4828). Ctors 0x601878/0x6019B8/0x6063B8 setzen den vptr. Probe: 0x6063B8 3x gebaut (r3=70255D40/7FEE4800/7FEE52A0), 0x601878 1x, 6019B8 0x.
- Naechster Schritt: Aufrufstellen des Slots +0x1F4 (lwz ...,0x1F4 + bctrl) finden, pruefen welche Objekte/Pfade ihn erreichen sollten. Details: work/MENU_RUN_NOTES.md, Log work/entryprobe2_run.err.

- 2026-11-22: Event-Dispatcher 5D9B68 (Slot +0x128, rekursiv ueber obj+0x30). Steady-State: 1 Event/Frame an Wurzelobjekt, Dialogbaum bekommt nur beim Bau Events (663). Heap-Adressen variieren pro Lauf. Details work/MENU_RUN_NOTES.md.

## sys_timer One-Shot Fix (2026-11-22)
- RPCS3-Abgleich (Warning-Log, log.yml wird von rpcs3 --no-gui NICHT beachtet; Pfad mit Leerzeichen muss in "..." im ArgumentList): Spiel erzeugt Timer (gFKsE/9qstY, Queue 0x8d033900) und startet sie.
- Bei uns: sys_timer_start(period=0, base=absolute Systemzeit us) -> EINVAL, Timer feuerte nie (~6700 Starts pro Lauf).
- Fix: period==0 = One-Shot bei absoluter Systemzeit (ps3_system_time_us exportiert aus ppu_sysprx.cpp, Backup work/_bk_ppu_sysprx.cpp, work/_bk_sys_timer.c; Kopie work/sys_timer_oneshot_fix.c).
- Ergebnis: Timer feuern jetzt, Dialog UNVERAENDERT (black 87.4 %, ops=158, cap_timer2, Pad-Script gedrueckt). Echter Bug, aber nicht die Dialog-Ursache.
- Offen: sys_event_queue/port- und Thread-Zaehler gegen RPCS3, Pad-Mapper-Ausgang, RPCS3-Trace per GUI-Log-Einstellung.

## Event-Queue-/Pad-Zaehler-Abgleich (2026-11-22)
- RPCS3 (Warning-Log, ab 12 s) legt 15 Event-Queues an, wir 9. Fehlend bei uns: sys_config-Queue size 32 (+Thread _cfg_evt_hndlr, kommt aus echter libio via sys_config_start), usbd-Queue 127 (sys_usbd_initialize), 2x size 42 und 1x size 32 (libsre/Spurs-Pfad), 1x size 127. Erklaerung: RPCS3 laeuft mit LLE-libio/usbd/Spurs, wir mit HLE -> kein Defekt per se.
- Pad-Zaehler (cellPad.c, [padcnt], Backup work/_bk_cellPad.c): Spiel ruft nur cellPadGetInfo2 + cellPadGetData (je >15000x, 1:1) und einmal ClearBuf; kein GetCapabilityInfo/SetActDirect/PressMode/SensorMode. Pad wird normal gepollt -> Pad-Datenquelle ok, Konsument ignoriert Eingabe.
- Naechster Schritt: Pad-Mapper-Ausgang (D00B2EF0 / 0x15708C0) per WWATCH/RWATCH; pruefen ob Mapper-Thread (tid=27) Daten ueberhaupt in Spiel-State schreibt.

## Pad-Mapper-Watch + PAD_SCRIPT-Oktal-Falle (2026-11-22)
- WWATCH/RWATCH 0x15708C0 (cap_padmap1): Objekt = Thread-Wrapper (Ctor A1C26C tid=1, Leser A1C130/A1C1F8 starten Thread-Body). KEIN Pad-Ausgang. Mapper-Ausgang liegt woanders (Schreibziele in A39CD8, gt6/generated/ppu_recomp_023.cpp).
- PAD_SCRIPT-Masken MUESSEN 0x-Praefix haben (strtoul base 0): "0040" = oktal 0x20 (press 0x0020). Lauf padreal1 mit 0x0040/0x4000 (log: press 0x0040 / 0x4000 bestaetigt): Dialog UNVERAENDERT (black 87.4 %, ops=158, Zeile 1 ohne Highlight, Mauszeiger sichtbar). Fruehere PAD_SCRIPT-Tests ohne 0x ggf. ungueltig, Ergebnis aber jetzt mit gueltiger Eingabe bestaetigt.
- cap-gt6 -Env trennt an Kommas: PPU_RWATCH=<hex>,<len> geht nicht (Laenge verloren).
- Naechster Schritt: A39CD8 lifted lesen, echte Schreibziele (Pad-Mapper-Ausgang) finden, dort WWATCH/RWATCH.

## Pad-Mapper-Gating + LEN-Konstanten (2026-11-22)
- A39CD8: r21 = Pad-Manager 0x165AD40; Ausgaenge manager+0xB08..0xB14 (0x165B848..). padnz2: Mapper liest 0x40 an 0x165ADE8/ADEA zur Presszeit -> Lieferung ok.
- Gating im Mapper: button[1] Low-Nibble*2 = r0; Stick/Sensor-Pfad (+0xB0E..B14) nur bei r0==0x18 (len 24). Wir lieferten len 28 -> Pfad tot.
- Ursache: cellPad.h CELL_PAD_LEN_CHANGE_PRESS_ON=24/SENSOR_ON=28; SDK: 20/24. Gefixt (Backup work/_bk_cellPad.h). Game setzt SetPortSetting(0, 0x6) -> len 24.
- Verifiziert (padw2): Mapper schreibt jetzt 0x200/0x18F (Sensor-Ruhewerte) nach 0x165B84E..B85E. padlen1/padw2/padr3: Dialog weiter unveraendert (black 87.4 %, ops=158).
- padr3: Listener-Records 0x165B1A8+ werden nur vom Mapper (Listenwalk), 0x03002F00 (Flag=1) und Decoder A395F0 (read2) gelesen. Naechster Schritt: Aufrufer/Konsument von A395F0 und Ausgabe nach dem Decoder.
- Diagnose im Code: [padpress] (cellPad.c, stderr nur bei PAD_SCRIPT-Druck), PPU_RWATCH_NZ (ppu_loader.cpp, env-gated). Riesige Watch-Caps machen Lauf zu langsam (>330 s).

## Zeitquellen-Check + Anim-Diff + Upstream + Xbox (2026-11-22)
- Anim-Diff Frame 3400 vs 4200: Dialog statisch, nur Cursor-Pixel differieren -> keine laufende Animation.
- Upstream ps3recomp: keine neuen Hinweise zu Pad/Dialog.
- Xbox-Pad (echtes XInput): keine Reaktion -> Problem nicht Eingabe-Backend.
- Zeitquellen statisch geprueft: ppu_timebase_now = QPC, 79.8 MHz, monoton, Anker bei Erstnutzung (ok). sys_time_get_system_time = QPC-Mikrosekunden seit Erstaufruf (ok, gleiche Hostuhr). sys_time_get_timebase_frequency = 79800000 (ok).
- Auffaellig (klein): sys_time_get_current_time liefert QPC-Uptime (sec seit Boot), nicht Epoch-Zeit wie LV2. Kann Datums-/Erststart-Logik beeinflussen. Nicht als Ursache bestaetigt.
- Fazit: keine Zeitquelle defekt. Offener Kandidat: Dialog-Open-Sequenz wartet auf Event/Callback (sysutil, Queue, Eventflag), nicht auf Zeit.
- Naechster Schritt: Thread-/Wait-Dump bei Frame ~3400 (wer blockiert worauf), plus Test current_time als Epoch.

- Epoch-Test (2026-11-22): sys_time_get_current_time liefert jetzt Unix-Epoch (GetSystemTimePreciseAsFileTime; Backup work/_bk_sys_timer.c). Capture cap_epoch1: black 87.4 %, ops=158 -> Dialog unveraendert. Zeit-Hypothese damit erledigt (Fix bleibt, da LV2-konform). Naechster Schritt: Wait-Dump aller Threads bei Frame 3400.

## Wait-Dump bei ~270/300 s (2026-11-22)
- Neu: env `PS3_WD_AT=<s1>,<s2>` (ppu_loader.cpp, Thread in lv2_syscall; gt6 hat keinen boot_main-Watchdog). Dumpt pro Guest-Thread lr/r3/sp, laufenden lv2-Syscall (g_sc_inflight) + HLE-inflight. Backup work/_bk_ppu_loader3.cpp. Logs work/wd2_run.log.err, work/evq1_run.log.err (PS3_EVQSTAT=300).
- Zustand (beide Samples identisch = statisch): ~20 Worker idle in sys_lwcond_wait (lr A4309C); tid1 (Fiber-Ctx) in cellFiberPpuWaitFlag, tid32 in cellFiberPpuRunFibers (lr A2FB4C); tid3 usleep 16 ms (lr A37464, Frame-Takt); tid27 Pad-Mapper usleep 12.5 ms; tid 5/36/37/42/43 lr A30550 ohne Syscall.
- Event-Queue-Waiter OHNE Timeout: q3 (tid15, lr A566C4), q4 (tid18, lr 82039C), q8 (tid22, lr 0), q9 (tid31, lr 7F9F6C). Mit Timeout: q1 (tid2), q6 (tid20), q7 (tid21). cond_wait 10 s: tid16/17/30.
- EVQSTAT: q3, q6, q8, q9 bekommen NIE einen Push. q4 size=1: 221 Pushes, stoppt nach Boot (~Event 1500). q1 ~15k, q5 ~61k (pending=4, kein Waiter), q7 ~61k (Timer). Ports: port2->q3 (name 0xD0A77), port3->q6, port4->q8; nur port1->q1 sendet (A466A4+0x742).
- Bewertung: Sender fuer q3/q8 (und q6/q9) feuern nie. Kandidat fuer fehlende Dialog-Fokus-/Open-Sequenz: Producer von port2/port4. Nicht bestaetigt.
- Naechster Schritt: Erzeuger/Sender von port2 (name 0xD0A77) und port4 per Caller-Trace auf sys_event_port_send (syscall 134) finden; Consumer q3 = func um A566C4, q8 = Thread-Entry tid22.

## Queue/Port-Zuordnung (2026-11-22, EVT_PUSHLOG=4, PS3_EVT_CREATE_STACK)
- Neu: env `PS3_EVT_CREATE_STACK=1` (sys_event.c, port_create); Stack-Dump blieb im Log leer (ppu_dump_guest_stack liefert nichts). Backup work/_bk_sys_event2.c. Logs work/pcs1_run.log.err, work/pl4_run.log.err.
- port2->q3 (name 0xD0A77) gehoert zum Thread tid15 "Spu Event Handler" (SPURS-Eventhandler, entry 14E14C0). Sender waere SPU-Seite (throw_event), nie aktiv.
- port3->q6: usbd-Kontext (cellUsbdSetThreadPriority2, tid20 pnZ). Sender = usbd-HLE, nie aktiv (Stub).
- port4->q8: mempool-Thread tid22 "lgFF" (unser sys_mempool). Sender fehlt.
- q4 (tid18 sgx-audio-thr, size=1) = SPURS-Queue, src=0xFFFFFFFF53505501 ('SPU\1') + d=0x701AC000/<wid 0..A>: ~200 Pushes im Boot, danach Stillstand -> SPURS-Workloads melden nichts mehr.
- q5/q7 = Audio-Notify (key 0x23A0 / 0x48DA6C685BCC82D), laufen (61k Pushes). Keine Audio-Ursache.
- q9 tid31 MEfYS: Sender unbekannt.
- Naechster Schritt: warum SPURS nach Boot keine Events mehr sendet (Spurs-Workload-Status 0x701AC000, Workload-Wakeups); usbd-Events (q6) gegen RPCS3 pruefen.

## SPURS-Check (2026-11-22, SPURS_KSTAT=20, PS3_EVT_CREATE_STACK=1; Lauf ks3 mit GT6_BUILD_DIR=gt6\build-clangcl)
- Korrektur: "Stack-Dump leer" (pcs1) war falsch; run-gt6.ps1 nutzt ohne `GT6_BUILD_DIR` das alte gt6\build\gt6.exe. Mit clangcl-Build liefert PS3_EVT_CREATE_STACK Stacks.
- Neu: `SPURS_KSTAT=<sek>` in cellSpurs.c (Kernel-Thread: Slots, je wid state/ready/sig/act/idle/runs). Backup work/_bk_cellSpurs2.c. Log work/ks3_run.log.err.
- Ergebnis: SPURS laeuft weiter. Beide Kernel-Threads loopen (loop#20000), wid0-7 state=2, runs steigen (wid5 12k->20k, wid7 9.8k->15k), alle Slots idle/ready 0. Stillstand-Hypothese SPURS widerlegt; q4-Stopp = Jobchain 0x701AC000 liefert keine Completion mehr (sgx-audio-Chain), nicht Kernel.
- Port-Ersteller (Guest): port1 func_00A47588 (PDI GFXS); port2 (->q3, Spu Event Handler) func_00A434FC/00A4259C; port3 (->q6) func_00274178 <- A37E58 <- B62864 <- 007D7340; port4 (->q8) func_00A5DE60+0x2A0 <- A2B94C <- A1C130.
- Naechster Schritt: Sender-Wrapper der Klassen von port3/port4 (analog port1 A466A4+0x742) finden und die Aufrufer per Entry-Probe/Calltrace pruefen; Consumer q6=tid20, q8=tid22.

## 2026-11-22 - Sprachdialog-Umgehung (boot.adc-Gates)
Siehe STATE.md "Umgehung Sprachdialog". Gates: 0x18924/0x196D6 (Sprache), 0x18A69 (Adjust), 0x18FDA (Tutorial). Ergebnis: gtmode laedt, dann Track-Sound-Schleife (338x 54 Files, tid 60-64 Entry 0x014E0898).
- Hyp. 16 Analyse: Leser-Thread 0x14E0898 = Stream-Reader (0x7E7C6C), Treiber 0x7D8308 (Sound-Player-Create, tid 33), Aufrufer offen. Details STATE.md.

## 2026-11-22 - Hyp. 17 (Aufrufer 7D8308)
7D8308 nur per Tail-Branch aus Vtable-Methoden 7D8B10/7D8DA8 (Slots 0x14775E4/E0). CALLTRACE_TO auf 7D8308, 7D8B10, 7D8DA8 (AFTER=200): jeweils 0 Treffer. Inkonklusiv; naechster Ansatz siehe STATE.md Hyp. 18.

## 2026-11-22 - Hyp. 18 (Worker-Thread-Entry)
tid 33 "p-OmN" (Entry 0x014E0898, Functor 0xF3D5F4 -> F3D150) hat 0 indirekte Calls (FROM=F3D150, AFTER=0/200). Sound-Manager-Singleton @0x1570A40 (Static-Init 0x11508: ctor 0x7D8CEC Player +0x18, Stream +0xB0). Nur Ctor/Dtor referenzieren die Adresse. Inkonklusiv -> Strategiewechsel Hyp. 19 (Umgehung/Vergleich). Hinweis: CALLTRACE-Ausgabe liegt in run.log.err, nicht run.log.

## 2026-11-22 - Hyp. 19 (Vergleich ohne Tutorial-Skip)
boot.adc.nodlg_noadjust (2 Laeufe, probe cmp_tut_*): Tutorial laedt (race_tutorial.mproject/.adc, Template.gpb), genau 1 Track (0449), dann Stillstand; 1/2 Laeufe mit mfc-REJECTED. Keine 27-Track-Schleife -> Schleife nur im gtmode-Pfad (Tutorial-Skip). boot.adc danach auf gepatchten Stand zurueck (Backup work/ARCHIV/boot.adc.patched_full, cmp identisch).

## 2026-11-22 - Hyp. 20 (7E90F0 fehlschlagen lassen)
Neuer Hook PS3_FAIL_ICALL=<hex> in ppu_loader.cpp (indirect call skip, r3=0); clang-cl neu gebaut (gt6\build-clangcl, 17:21). Lauf fail7e90f0: Hook feuert 1x, keine Track-Schleife, Boot stoppt weiter nach scene/misc/gl0019; Frame 4200 nie erreicht (4/4 gueltige Laeufe) -> keine Umgehung. Schleife ist Symptom. MinGW-Build (gt6\build) nicht neu gebaut: Hook nur Probe-Knob, Laeufe nutzen build-clangcl.

## 2026-11-22 - Hyp. 21 (Watchdog, Hauptthread-Wartepunkt)
probe wd21 (PS3_WD_AT=120,240; PS3_EVQSTAT=40; 2 gueltige Laeufe): tid 1 in cellFiberPpuWaitFlag (GT6-Stub stubs.cpp:1382; Yield-Schleife max 2 ms in Fiber, sonst 5 s), tid 32 in cellFiberPpuRunFibers, ~20 Threads in sys_lwcond_wait. Kein harter Deadlock: Guest dreht in Flag-Warteschleife, das Gegenueber (Flag loeschen + CheckFlags) kommt nie. Naechster Schritt Hyp. 22: haengendes Flag per Log im Stub bestimmen, Setzer suchen.

## 2026-11-22 - Hyp. 22 (WaitFlag-Quelle)
GT6_FLAGLOG (stubs.cpp): einziger WaitFlag-Aufrufer ist Fiber-Idle-Loop 0xA2F464 (flag obj+0x40, Wert 0; Waker indirekt 0xA2F8B8, CheckFlags). Stack-Scan zeigt nur A2F484. Fibers erben thread_id des Erzeugers (tid 1): Watchdog-Zeile 'tid 1 in WaitFlag' = Fiber, nicht Hauptthread. Hauptthread selbst wartet in sys_lwcond_wait-Wrapper (lr 0xA4309C, cond 0x7FEAE030) wie ~20 weitere Threads; Zeit real, Sleep-Loops enden. Hyp. 21-Deutung (Flag-Deadlock) damit korrigiert. Naechster Schritt Hyp. 23: lwcond-Signalverkehr loggen.

## 2026-11-22 - Hyp. 23 (lwcond-Verkehr)
PS3_LWCLOG (ppu_sysprx.cpp, gitignored, nur nach 90 s): reger Verkehr, lwcond-IDs ~0x4C0213xx..0x4C021Dxx (~139k create), Stack-lokale Conds; tid 1 signalisiert Sound-Manager-Conds 0x1570AB8/0x15DE688, tid 34/33 warten, Wiederholung. Boot haengt nicht idle, sondern dreht in der Track-Preload-Schleife. Naechster Schritt Hyp. 24: Abbruchbedingung der Schleife im aufrufenden Script/Native finden.

## 2026-11-22 - Hyp. 24 (Schleifen-Abbruchbedingung)
PS3_STACKSCAN/PS3_THRLOG (ppu_sysprx.cpp, Patch patches/ps3recomp-stackscan.patch). Hauptthread-Stack-Scan (tid 1, in lwc_signal nach 100 s) zeigt identischen Stack in 2 Samples: Schleife 0x568800..0x568858 (setjmp 0xB98168; Tick 0x5C406C ueber 3 Objekte bei r28+0x1d4 bis alle obj+0x91 != 0). Tick = Zustandsmaschine obj+0x88 0..5 via Methodentabelle 0x145D0D4. Handler 4 = 0x5B97A0 (Jobliste, vtable+0x120 == 3 -> Fortschritt), Handler 5 = 0x5A5BB0. obj+0x91 nur durch Exit-Request (0xA13644 liest Byte 0x164AB90; gesetzt in 0xA13804 via EXITGAME 0x101 aus 0x7F8F70) oder Finish 0x5C4824/0x5C3EC4. Global 0x15DE27C==1 ueberspringt Handler. Schluss: Loader-Jobs werden nie fertig; Ursache ist Zustand des Loader-Objekts, nicht der Schleifenrahmen.

## 2026-11-22 - Hyp. 25 (Zustand 3 im Loader-Objekt)
Handler-4-Objekte (Getter 0x640038 / 0x593E34) sind Task/Future-Wrapper. 0x640038 -> 3 nur bei Inner-State 2 (0x987ec8 via 0x987a28). State-Maschine 0x987180 func(obj,event): 0 init, 1 running, 2 done, 3 cancelled; neuer State = Event (Store 0x987544); Wrapper 0x987550 (ev1), 0x987558 (ev3), 0x9875A0 (cancel). [ST25]-Log Inner 0x4083F190: st=0 ev=1 (lr 9EC758) -> st=1 ev=1 -> st=1 ev=3 (lr 9875C8, Stack 9D3D70 9D3D08 987E5C 9E5AA4 987D80 9881FC 9794C8 ...) -> st=3 -> Restart (lr 987AC4), endlos. Event 2 nur von 0x9A5A38 (<- 986504/9866A0/98684C, Klasse mit OPD-Slots 0x14DA580: 986440/986568/986704/986860); 986568 aus 9C634C+0x2B1, 986440 nie gerufen. 986704/986860 ungetestet (Paralleldirektorien-Kollision). Offen: Grund des ersten Cancel in Wait-Fkt 987C2C..987E58. Patches: patches/ps3recomp-obj25.patch, patches/gt6-st25-statelog.patch (generated/ nach Backup zurueckgespielt, Build neu).

## 2026-11-22 - Hyp. 26/27 (Event-2-Sender, Eventverteilung)
Ein Build mit [H26]-Entry-Logs (986440/986568/986704/986860/9A5A38/987A28) und [E27]-Eventlog (alle Objekte, je 40 pro Event) in func_00987180, 3 Laeufe parallel (probe h26/h27). 986440/986568/986860 und 9A5A38 werden gerufen (986568/986440 lr 9C6390, 986860 lr 9791A4); Event 2 erreicht 40007C10/4083F390/4083F410. 40007A10/40007C90/40007990 (Task-Objekte der Handler-4-Schleife) sehen nur 0->1, 1->3 (Cancel lr 9875C8) -> Restart (lr 987AC4). Wait-Fkt (in func_00987A28, 0x987D00..0x987E58) cancelt bei leerer/kleiner Job-Liste (r22+4==0 oder end-begin+3<=6) oder obj+0x28==3. Naechster Schritt: Log der Listenwerte am Cancel-Zweig. Patch: patches/gt6-h26-h27-eventlog.patch; generated/ zurueckgespielt.

## 2026-11-22 - Hyp. 28 (Job-Liste am Cancel-Zweig)
[C28] in func_00987A28 @loc_00987E54 (Patch patches/gt6-h28-cancelzweig.patch). Alle Cancels: obj=r23=r25=r28 (40007A10/40007C90), obj+0x28=1, obj+0x30=0, g(0x15DE27C)=0, r22=obj+0x6c, begin(obj+0x70)==end(obj+0x74) -> Vektor leer, Kapazitaet begin+0x28 (Heap mit Alt-Strings). Wait-Schleife (0x987E34..0x987E50) wartet nur bei nicht-leerem Vektor. Naechster Schritt: Befueller des Vektors finden.

## 2026-11-22 - Baseline-Wechsel + Hyp. 29/30
boot.adc auf nodlg_noadjust (Kopie work/ARCHIV/boot.adc.nodlg_noadjust; vorheriger Vollpatch in work/ARCHIV/boot.adc.patched_full_*). 3 Laeufe 320 s: Tutorial-Rennen laedt (race.adc, race_tutorial, Template.gpb, nur sgb 0449), Frame 5000 GT-Logo-Ladebildschirm, keine Sound-Schleife; STACKSCAN-Hauptthread identisch zu Hyp. 24 -> gleiche Task-Wait-Ursache. Hyp. 29: 987A28 ruft vtable+0xdc des Executors (obj+0x34), der 1 Job in obj+0x70/74 pusht (v74=v70+4); Dispatch 98787C -> Poll 9EEA88 (Executor obj+0x68); Job-Ergebnis 0/1 nie 2, Vektor danach leer -> Cancel. Hyp. 30: Poll setzt o24=0 (Task-State 3) / 2 (State 2) / sonst fuehrt Job aus (ab 0x9EEB04). Patch: patches/gt6-h29-h30-joblog.patch.

## 2026-11-22 - Hyp. 31 (Job-Poll 9EEA88 pro Objekt)
[P31] vor/nach Handler-bctrl 0x9EEC3C in func_009EEA88 (Skript: patches/gt6-h31-polllog.py.txt, Python-Insert-Skript, kein Diff wegen CRLF). 2 Laeufe valid. Poll ist Script-VM: ip=[exec+0x1c] steigt +4/Opcode, Handler-Tabelle 0x1487660. Tasks 40007A10/40007C90/40007990 fuehren Opcodes aus (u.a. 0B,26,25,1D,32,33,0C,03,39,05,24,1C), o24 bleibt 5 -> VM laeuft normal. Einzige o24-Aenderung: Opcode 0x37 (Handler 9ED204, = Script-Return/Ende) setzt task+0x24 = 1 (bei 40007C90, ip 40295538/40295590/40387BF0). Ergebnis 1 statt 2 -> Done-Event nie, Cancel. 40007A10/40007990 erreichen im 60er-Limit kein 0x37.

## 2026-11-22 - Hyp. 32 (Opcode 0x37 Status-Wert)
Statisch: Handler 9ED204 (Script-Return): Skript-Instruktionen sind 8 Byte (w0=op<<24|operand, w1=Argument). Handler liest w1=[ip+4]; Werte 1..3 -> pop Ergebniswert vom VM-Stack in Promise task+0x20 (979290), dann task+0x24 = w1; sonst task+0x24 = w1 direkt. Dynamisch [P32] (patches/gt6-h32-op37log*.py.txt): op37 bei 40007990 hat immer w1=0 (80 Treffer, 2 Laeufe); bei 40007C90 war w1=1 (Hyp. 31). Jump-Tabelle 0x1419550 (Switch auf obj+0x24 in 98787C): 0->987914 (98604C Schritt, dann Schleife), 1->98792C (985FE0-Test + 98604C), 2,3->987A08 (RETURN Ergebnis = Done/Fail), 4,5->9878B8 (Poll wiederholen). Also: Return-Status 0/1 = "Schritt fertig, naechsten Job holen" (98604C), nur 2/3 beendet den Task. Der Task wartet auf weiteren Job/Schritt; Vektor (obj+0x70..0x74) wird nach dem einen Job leer -> Cancel.

## 2026-11-22 - Hyp. 33 (98604C / 985FE0 / Job-Stack)
Statisch: Vektor obj+0x70(begin)/0x74(end) ist ein **Stack von Job-Objekten** (4-Byte-Zeiger). 985FE0(obj) = peek: top=[end-4], ruft top.vtable+8 (Status). 98604C(obj) = pop: top.vtable+0xc und +4 aufrufen, end -= 4 (nur wenn >6 Bytes... Groessenpruefung). 9860D4-Wrapper: while status!=2 {pop; leer -> return 1}; status==2 -> pop + obj+0x68.vtable+0x18(arg) -> return 0 (Erfolg). Dynamisch [P33] (patches/gt6-h33-peeklog.py.txt, 2 Laeufe x 62 Treffer): top-Job hat immer vtable 0x14875B0 (enthaelt 0x9EEA88 = Poll an +0x14, d.h. Job-Objekt = VM/Executor-Klasse), vtable+8 -> 0x8A1BE8 = `li r3,0; blr` (Stub), Status immer 0, nie 2. Stack-Tiefen: 40007990 5 Eintraege, 40007A10/40007C90 1. Damit kann der Wrapper-Pfad nie Erfolg melden; Done muss ueber obj+0x24=2/3 (Script-Return-Opcode mit w1=2/3, oder anderer Handler) kommen.

## 2026-11-22 - Hyp. 34 (Handler die task+0x24 setzen)
Statischer Scan der Handler-Tabelle 0x1487660 (patches/gt6-h34-scan.py.txt): direkte Setter nur 0x37 (Return, o24=w1), 0x1F/0x28 (o24=3, Abbruch), 0x1B (o24=w1), 0x06/0x0F/0x2C/0x3E (o24=5 via 9F095C). Dynamisch [P34]/(patches/gt6-h34*-*.py.txt, 2 Laeufe): o24=2 WIRD erreicht (Opcode 0x37 mit w1=2, 21x bei 40007C90, 1x 40007C10, ip 403B22F0..403B2858) -> 2 ist Return aus verschachteltem Aufruf, nicht Task-Ende. Der dominante Zustand ist o24=4 durch Opcode 0x06 (Handler 9F0748, 251x 40007C90, ip 403A6628 allein 120x): 0x06 = Sub-Aufruf/Child-Job: submittet Child via Executor-vtable+0xdc (Args vom VM-Stack), Child-Future bei [sp+0x78]; ist child+0x24==1 -> setzt o24=5 (weiterlaufen), sonst bleibt o24=4 (Dispatch-Fall 4: Poll wiederholen, ip bleibt am Opcode, Child wird bei jedem Poll neu geprueft/submittet). Script haengt also in 0x06 an Child, dessen +0x24 nie 1 wird. Hauptmenue-Blocker = Child-Job (Ziel unbekannt).

## 2026-11-22 - Hyp. 35 (Child-Job bei Opcode 0x06)
[P35] in func_009F0748 (patches/gt6-h35*-submitlog.py.txt; Variante b filtert task 40007C90). Opcode 0x06 = **native Funktion aufrufen** ueber callee-Objekt (r3) mit callee.vtable+0xdc: Ziele 9B0918 (vt 01483EC8, Ergebnis sofort st=1 -> o24=5) und 9B89D8 (vt 01484968; Wrapper, delegiert an Objekt [callee+0x14] vtable+0x54, args r4=Result-Slot sp+0x78, r5=w1, r6=Argumente) sowie 9A0178 (vt 014851B0, st=1). Das Ergebnis-Objekt [sp+0x78] ist der Task selbst (child=40007C90); st=[task+0x24] nach dem Aufruf. **st=4 (pending, Poll wiederholen) tritt nur bei 9B89D8-Aufrufen auf** (callee 4037EC28, 4049AE20/AE80/AF28/AF10, 403AD8E0, ...), 9B0918-Aufrufe liefern st=1. Der in Hyp. 34 dominante Hang-ip 403A6628 lag ausserhalb des 120er-Logs (Cap zu fruh erschoepft). Ziel-Objekt [callee+0x14] und dessen vtable+0x54-Methode noch unbekannt.

## 2026-11-22 - Hyp. 36 (Snapshot-Werkzeug PS3_SNAP_AT)
Patch patches/gt6-snap-at.patch (ppu_loader.cpp Thread + runtime/diag/ps3_snapshot.c): nach N s alle committeten VM-Regionen (reg_<ea>.bin, regions.txt, ~1 GB), Thread-Regs/Stacks, Sync-Tabellen. Lauf snap2 (work/snap_run2, 200 s, notut) gueltig.
Befund: Threads 2-40 in lwcond_wait/Syscalls (130/141/107), Hauptthread in cellFiberPpuWaitFlag. Mutex: 10 aktiv, alle owner 0. Sem: 8 mit value=0 (max 1024), keine Waiter. evq5 (key 0x23A0 = cellAudio-Notify) cap4 count4 ohne Receiver (vermutl. Symptom, vgl. Hyp. 19/20).
Wrapper-Suche (find32 0x01484968): 111 Objekte, 110 mit vtable 0x1487348 -> Slot 0x54 = 0x9E5FC0: Bind-Trampolin, ruft 0x9880BC(*arg4, this+0x14, [this+0x14]+0x34 ...) -> [x+0xC].vtable+0x28. Zielfunktion noch offen.

## Hyp. 37 - Snapshot snap_run2 (200 s, notut): Script-Task und Ziel des Pending-Calls
- Poll 0x9EEA88 gehoert zu 12 Task-Knoten (vt 0x14875B0, Poll +0x14); State-Objekt (vt 0x14811E8) +0x24 Status, +0x28 Zustand. Aktiver Task 400DB544 (Parent 400C7F88), State 40007990 Status 5.
- Bytecode: task+0x1c = ip (Array von Record-Zeigern), Record byte0 = Opcode, Handlertabelle 0x1487660+24*opc+0x10. Letzter Record vor Yield: opc 0x06 (arg 0x9A), danach 0x36 (015DE7D8).
- Opcode 0x06 (0x9F0748): Stack task+0x20 (base[0], Top +0x1c) pop 2 -> Callee 4037A844 (vt 0x1483EC8, +0xdc=0x9B0918), Arg-Objekt 400E97F0 = String "gtmode".
- 0x9B0918 -> obj2 4009EFE8 (vt 0x1485B50) +0x54 = 0x9C625C -> +0x58 = 0x9C6184 -> Functor obj2+0x14 = OPD 014CD330 = 0x6C54DC = MGOM.start.
- Manager 7FF01FC4: +0x48 = 1 (pending), +0x50 = "gtmode" -> Request wird nie konsumiert. Siehe boot-presents-fix.md 2.3.

## Hyp. 38 (offline, snap_run2): warum Consumer nicht laeuft
- Hauptthread (tid 1) steht in menu_start_project: Stack 0x568CCC/6C54CC/6C558C, Wait-Kette A21D50 -> A21CBC -> A4305C (cond wait).
- Workers tid 28/35/43: lr=00A121F0 -> Rueckkehr aus A187CC (lwcond wait in Worker-Schleife 0xA12170). Tick-Hook sitzt bei loc_00A121AC (Schleifenanfang) und feuert nur nach Wakeup.
- Kein Thread mit 0x568658 auf dem Stack; Pump-Request-Hook (func_00568C94 Eintritt) ok, aber Tick wird nie getrieben.
- A21E04 (signal) -> A21D8C: ist Waiter-Flag +0x28 gesetzt -> A42FFC (signal), sonst +0x29=1 (pending). Pre-Signal bleibt erhalten.

## Hyp. 39 (probe_sync39_20261122_220806_1, notut, 220 s)
- Sync-Pump vor 568CC8: "boot" (state 1->3->4->done, `sync pump done state=0` L7829), danach "gtmode": project load gtmode.mproject, states 1,3,4,3,4...
- gtmode: `sync pump done state=4` (L29752) nach 4000 Iter; state_after=3 3729x, =4 3538x, flag4C=1 load4D=1 -> Sequenz wird getickt, wird nie fertig (+0x91).
- Patches: gt6/src/stubs.cpp gt6_menu_project_sync_pump; tools/apply_gt6_post_lift.py add_menu_sync_pump (backup work/_bk_h39/ppu_recomp_012.cpp).

## Hyp. 40 (snap_h40, PS3_SNAP_AT=100 im sync-pump-Build)
- Consumer 0x568658: state 3->4 CAS, tickt manager+0x1d4[0..2] via 5C406C, setzt state zurueck auf 3, solange +0x91==0; alle fertig -> state 5.
- 5C406C: pro Tick Handler[+0x88] aus Tabelle 145D0D4 (5C1B3C,5BD718,5A8218,5B80DC,5B97A0,5A5BB0), +0x88++; Ende wenn A13644()=1 (Byte 0x164AB90 unter Mutex 164AB50) -> +0x90=1 -> 5C3EC4.
- Snapshot: Objekte 7FF0B000/7FF0B800/7FEAC000: +0x88=0, +0x8C=5/5/A, +0x90/91=0; 0x164AB90=0.

## Hyp. 41 (2026-11-22): Fertig-Flag der Sequenz-Objekte
- Offline (snap_h40): einziger Setter von +0x90 im Sequenzcode = 5A3AC0 (Func 5A3AAC), Aufrufer: 5680FC (Consumer-Exit 0x56886C/0x5E6D78) und 5A7A10 (generischer weak-ref-Wrapper, von 5AB428 mit >20 Aufrufern). Kein Handler setzt es selbst.
- A13644 liest Byte 0x164AB90 = Objekt 164AB80 (vt 146FA48) +0x10 unter Mutex 0x164AB50. Getter vt+0x8 = 3C0E84 (lbz 0x10(r3)), Setter vt+0xC = C3FE14 (stb r4,0x10(r3)); keine direkten bl-Aufrufer -> nur indirekt.
- Probe probe_flag41_20261122_222528_1 (GT6_FORCE_LOADFLAG=1, Sync-Pump i==20 schreibt 0x164AB90=1): Pump-State -> 0, Boot laeuft weiter (cellMusicInitialize2, open game024.db). Danach NULL-Deref in A21D50/A21CBC (Rueckweg 568CC8, Waiter manager+0x18) -> exit-chain code=0xFFFFFFFF.
- Interferenz Worker-Hook vs Haupt-Pump: nicht separat gemessen (Hook feuert laut Hyp. 38 nie).

## Hyp. 42 (2026-11-22): Rueckweg nach Sync-Pump, Natur des Flags 0x164AB90
- A21D50 (bl bei 568CC8) nach Pump: r3=mgr+0x18 korrekt, aber nach A42DE8 (Lock) r29=0 -> A21CBC liest NULL+0x29. Lock/HLE (ppu_sysprx lwmutex, gcm_pump) klobbern r29 NICHT (Diagnose-Klammern probe_flag42d..i).
- Ursache: DRAIN_TRAMPOLINE nach dem Lock-Call fuehrt ein vom Sync-Pump hinterlassenes g_trampoline_fn aus (Cross-Fragment-Fallthrough aus func_00568658), das r3/r29 nullt.
- Fix: gt6_menu_project_tick drained g_trampoline_fn direkt nach func_00568658 (stubs.cpp). probe_flag42j: A21D50 after lock r29=7FEAC018, Boot laeuft weiter.
- Danach exit-chain code=-1 lr 7F9588 = func_007F9520 (ppu_recomp_018): wenn Byte +0x95E==0 und A13644()!=0 -> +0x95E=1, Zeit (A2F308) nach +0x960; spaeter (now-stamp > 0x97FDF) -> func_00F9A080(-1) = exit.
- Schluss: 0x164AB90 = Quit/Abbruch-Anforderung mit Grace-Timer, nicht "Projekt fertig". Die Sequenzobjekte beenden sich bei Quit; GT6_FORCE_LOADFLAG bleibt reines Diagnose-Werkzeug (erzeugt Shutdown).
- Echter Fertig-Setter fuer +0x91 weiter unbekannt -> Hyp. 43.

## Hyp. 43
5C3EC4 (Finalizer) setzt +0x91=1; Aufrufer: 5C406C (nur wenn +0x90 durch A13644/Quit) und Shutdown 5FBAF0. Schleife 568800 = Haupt-Game-Loop, endet nur bei Quit. Hang = kein Menue-Rendering im Tick, nicht fehlendes Done.

## Hyp. 44 (Game-Loop, Pump unbegrenzt)
- GT6_PUMP_ITERS=2000000: >15600 Iter, State 3/4, ~2193 Flips/320 s, frame_00 = Legal+Logo+Spinner (probe_pump44b). Kein Menue-Frame.
- Back-Trace Track-Opens (009F8E40, probe_bt44): 009F7204<-009F73D0<-009F7420<-009F79D8<-008C70C8/008C1540 (11/40); 009F418C<-009BB16C<-005F3FE8<-005FA4D0<-005FA730<-568784 (Consumer).
- Ursache Dauerschleife offen.

## Hyp. 45 (Teil)
- probe_bt44: 3754 soc-job Chains, 4062 GT.VOL-Opens, 5213 IsLoaded(NPN); Snapshot: Main-Thread lr=568CB4 (im Sync-Pump), Objekte 7FEAC000/7FF0B000/7FF0B800 +0x88=0. Einmal job 3 rc=-1. Ursache offen.

## Archiv aus STATE.md (Hyp. 109-116, verschoben 2026-11-23 Ueberwacher)
- Hyp. 109-111: statische Kette Wipe: 7D083C (Wrapper, Singleton 0x159FD890) > 7CD628 > 88B878 > bl A25C64 (je 1 Aufrufer, 7D083C ohne direkten). CALLTRACE_TO auf 7D083C/7CD628/88B878/88B8E0: 0 Treffer (Exit-Laeufe h110 4/4 mit CALLTRACE=200, 88B8E0 ist ein bl-Site).
- Hyp. 112: GSTACK im Exit-Lauf (run.log.err, h110): Worker tid32 "9qstY" (A304D0>7FB1F0>7FB090>7DF57C>7DFF44>7DF7DC>802004>1AE7CC>1AE5E4>1AE074>1AAC8C>7D083C>7CD628>88B878>A25C64). Unfiltered Calltrace: kein Exit (Heisenbug).
- 1AAC8C = Cleanup-Task (Obj+0x1F30: 7D0904,7D0DE8,7D0FC0,7D083C,7D08DC), einziger Aufrufer 1AE1E8 in 1AE074. Frage: warum laeuft Cleanup beim X-Press, Singleton-Vektor 71E4455C hat NULL-Element.
- Hyp. 113: A25C64 = Fill [begin,end-8] mit 0 (Vektor elem+0x2C: begin@+8, end@+0xC). Leer begin=end=0 -> end-8 wrap (unsigned) -> Fill 0..FFFFFFF8 = Wipe.
  Elem-Objekt unkonstruiert/genullt (race). Loop-Log: normale Laeufe 2 Elemente ok (7FFEE090/E0D8); 2. Exit-Typ: erster NULL-Write aus CAC2D4 (1AE074+0x488), nicht A25C64 -> generelle Race.
- Umgehung: Guard in func_00A25C64 (generated 023): end<8 -> return. Backups work/_bk_h113/. h114/h115 (10 Laeufe): 0 Exits, Guard feuert ~30% (Elem-Zeiger Muell/NULL).
- Hyp. 115: Guard-Survivor Frame 9000 (4x) = GT-Logo+Spinner. fs-Zugriffe enden frueh (kein IO-Wait). 2/4: A2FAD0 Ringlisten-Walk mit NULL-Knoten = Busyloop (3.7M null-writes).
- Befund: Teardown-Tasks (1AE074: +0x178 1AAC8C, +0x508 7CFDD0>88B928) laufen auf Singleton/Listen, die parallel genutzt/genullt sind = Use-after-free-Race. Ursache offen.
- Hyp. 116: TLS-TID-Cache (A3046C) liefert pro r13 eindeutige ids (1,2,5,9..34) -> TID-Duplikat widerlegt. 1AAC8C/1AAD14 laufen JEDEN Frame (kein Wait/Teardown-Trigger) = normal.

## Spinner-Zustand Watchdog + Calltrace (2026-11-23, probe wd2/ct, orig+X@100, build-v020)
- WD bei 200/320 s identisch: ~20 Worker in sys_lwcond_wait (lr A4309C), tid1/2/3/5 nur lr. EVQSTAT: q4 pushed=205k, q5 64k (pending=3), q7 64k, q1 17k, q9 21k; kein Waiter-Stau.
- NEU: `[null-write] wrote32 0 to NULL+0x40 by guest-fn A2FAD0` 4,55 Mio x in 340 s (~13k/s), dazu 2x NULL+0x18 by 88B450 beim Boot. A2FAD0 = "wake all" (vtable-Slot 7 Fiber-Thread-Klasse): Schleife ueber Listenknoten, stw 0,0x40(node->+8). Element-Pointer NULL -> Fiber-Liste hat NULL-Eintraege (verwandt mit Hyp. 83 NULL-Element).
- CALLTRACE_TO=A2FAD0: Aufrufer lr=567DA4 = func_00567D74+0x2A4, tid=32 (Fiber-Run-Thread), r3=0x7FFBE280 r31=0x7FFD8E88. 567D74 hat einen direkten Aufrufer (6D5230); Rest ueber vtable.

### Fiber-Liste Busyloop (2026-11-23, probes nwt/wk/ww2, build-v020 + Diag)
- null-write tick: ~78M NULL+0x40-Writes/s von tid32 in A2FAD0, konstant 180+ s (nwt) -> Schleife laeuft praktisch dauernd, nicht 13k Aufrufe/s mit kurzer Schleife.
- [WK]-Diag in Schleife: obj=7FFBE280 cnt=1, hdr(obj+0xC)=7FFFEDC0, hdr.next=0 -> r9=0, Null-Page liest 0, cmpw nie gleich -> Endlosschleife (PS3 wuerde crashen).
- Mit PPU_WWATCH (Inline-Stores aus, Timing anders): Sentinel EDC0 sauber init (A2F638, tid1), Knoten EDD0 via A2FC54, KEIN Busyloop. Snapshot-Laeufe: Sentinel EDB0 sane, tid32 in lwcond_wait.
- Fazit: Busyloop = Alloc/Race-abhaengiger Zusatzfehler (Sentinel nullt in manchen Laeufen); Spinner haengt auch in sauberem Regime -> NICHT Ursache der Ladephase.

## STATE-Archiv (2026-11-23, aus STATE.md verschoben)
## Erledigt / widerlegt (Einzeiler)
- Pad/Dialog-Kette (Hyp. 1-14): alles ohne Wirkung, durch Umgehung (15) hinfaellig. RPCS3 `--no-gui` als Orakel tot (Shader-Precompile).
- Plan B Pad-Replay: PAD_LOG=<pfad> (patches/gt6-v020-padlog.patch, build-v020 neu gebaut, getestet) + scripts/live-padlog.ps1: user spielt live, Log -> PAD_SCRIPT-Replay.
- SDK-Update ps3recomp v0.19 -> v0.20.0 (Klon third_party/ps3recomp-v020, lokale Patches gemergt, Build gt6\build-v020): Baseline noadj 220s/Frame 4200 identisch (GT-Logo+Spinner), Fortschritt gleich; Flips ~3x weniger (Pacing). Backend-Vergleich Vulkan vs D3D12 offen (PS3RECOMP_RSX_VULKAN + rsx_vulkan_backend_init).

- probe.ps1: -FreezeSec, -Seconds 0, END-Zeile, hdd0-Kopie/Lauf (-Parallel ok). PadScript nur Press-Tokens (0x0 verboten).
- Hyp. 78-80: REALFLAG (WaitFlagEx) = DEFAULT, Dialog rendert korrekt. noadj+REALFLAG: Exit ~52s (Race, Hyp. 81/82/86 pinned=deterministisch).
- Hyp. 83: Exit = A25C64 (vector.clear) aus 88B8E0, NULL-Element im Zeigervektor 71E4455C -> zeroed 14E4000..FFFFFFF0. Hyp. 84-89: Puffer/new/Lock nicht Ursache (Heisenbug).
- Hyp. 92: orig + PAD X (80-140s) -> Frame 9000 = GT-Logo+Spinner. AdjustScreen passiert.
- Hyp. 109-116 (Details in eu-boot-log.md "Archiv"): Wipe = A25C64 Fill end-8 wrap, Aufrufer Worker-Cleanup 1AAC8C; Guard (A25C64 end<8 return) stoppt Exit, Spinner bleibt -> Wipe ist NICHT Ursache der Ladephase.

## UEBERWACHER-FINDINGS (2026-11-23, Review Hyp. 1-116 gegen ps3recomp v0.20 + third_party/GT5P)
1. Kette Hyp. 83-117 (35 Hyp.) jagt Exit-Race = Symptom. Guard-Survivor zeigen: auch ohne Exit bleibt Logo+Spinner. Race-Jagd STOPPEN.
2. UNGETESTET, billig, je 1 Batch (-Parallel 4): `PS3_PRIO_START=1` (lv2-Prioritaetsstart, SYSCALLS.md; Race-Klasse "Thread laeuft vor Init"), `PPU_RESV_OFF=1` A/B (stwcx-Reservation), `SPU_LOCKSTEP_QUANTUM`.
3. Probe != Live: user sieht live Menue nach Testrace. Probe nutzt FRISCHE userdb pro Lauf (GT6_HDD0-Kopie ohne db), boot.adc-Patches, <=320 s. Spinner evtl. = Erststart-Setup (DB/Save-Aufbau), dauert real >10 min. Test: Live-Run mit users persistenter db + 15 min, Frame-Captures 4200/9000/20000/40000.
4. GT5P-Schwesterport (gleiche PDI-Engine, third_party/GT5P/docs/progress.md): Wurzeln waren Runtime-Schreiber ins Spiel-Heap (VM_HLE_INJECT_BASE, GT6 ok = 0x03000000) und HLE-Stub mit falscher Argzahl (cellDiscGame schrieb in OPD-Tabelle). -> HLE-Stubs auditieren, die in Gast-Zeiger schreiben (PPU_WWATCH auf Opfer-Adresse, Writer-Attribution 'host' vs 'guest-fn').
5. Messen mit `PS3_VERBOSE=0` (probe.ps1 setzt das): Logging serialisiert Threads = Heisenbug-Ursache (GT5P README).

ERGEBNISSE 2026-11-23 (probe.ps1 -KeepDb, RSX_CAP=start:count:stride via -Env, build-v020):
- Befund 3 WIDERLEGT: persistente db (-KeepDb), orig+X@100s, 900 s/100k Flips: Frame 4200 AdjustScreen, 7200..19200 stabil GT-Logo+Spinner. Fresh-db ist nicht die Ursache.
- Befund 2 NEGATIV: PRIO_START=1 / SPU_LOCKSTEP(Q1000) / Kontrolle: Frame 4200 identisch (AdjustScreen, 28,4% schwarz). PPU_RESV_OFF=1 schlechter: nur 6555 Flips/430 s, NP2-IsLoaded-Schleife.
- Befund 4 Audit (statisch, offen): Verdacht M-H cellSysutilGetBgmPlaybackStatus (cellSysutil.c ~507, memset 0x28 vs SDK-Struct), M sys_process_get_paramsfo memset 256, cellSync Barrier/Rwm Host-Layout. cellFs/SaveData nicht auditiert.
- Spinner-Zustand (wd2/ct): Waiter alle idle, keine Event-Staus. NEU: wake-all A2FAD0 ~13k/s von tid32 (func_00567D74+0x2A4), Fiber-Listenknoten mit NULL-Element (NULL+0x40-Writes, 4,5M). Details eu-boot-log.md.

- Fiber-Liste A/B (snap 200s, REALFLAG 0 vs 1): Obj 7FFBE280 count=1, Knoten-Payload nicht NULL, Struktur identisch -> NULL+0x40 kommt NICHT aus dieser Liste; REALFLAG ohne Einfluss.
- Fiber-Busyloop: A2FAD0 laeuft 78M NULL-Writes/s, Sentinel obj+0xC hat next=0 (nur in manchen Laeufen, Alloc/Race); Snapshot/WWATCH-Laeufe sauber, Spinner auch dort -> nicht Ursache.

Audit #1/#2 (BgmPlaybackStatus/paramsfo gegen SDK), dann RPCS3-Vergleich: welche Syscalls/Files nach AdjustScreen fehlen in unserem Lauf.

## PDIPFS-Orakel-Test (2026-11-23, probe pdi)
- fsv (PS3_VERBOSE=1, 140 s, normale hdd0): 118 PDIPFS-Opens ok, 0 fehlgeschlagen, kein Zugriff auf PDIPFS/59.
- pdi: hdd0 = Kopie RPCS3-USRDIR (14 GB, 17,5k Dateien, work/gt6_hdd0_rp; Originale unberuehrt), -KeepDb, orig, 300 s, X@100s: 18,8k Flips, 3,1M null-writes, 9,7k NPN-IsLoaded, kein Open PDIPFS/59, kein Pamf/Dmux/Vdec-Treffer im Err-Log. Identisch zum Standard-Spinner.
- Region: RPCS3-Daten JP (BCJS37016, Ordner GT6_1.N), unsere EU (GT6.N). Spinner-Zustand unabhaengig von PDIPFS-Inhalt -> Install/Daten-Hypothese verworfen.
