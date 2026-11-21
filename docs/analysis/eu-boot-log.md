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
- Fix: a3-Arrays beim Format-Schreiben ignorieren (`rsx_commands.c`), col0 kommt dann aus VERTEX_DATA4F. Env `A3KEEP=1` stellt altes Verhalten her. Patch `patches/gt6-rsx-ignore-stale-a3.patch`. Ergebnis `eu-language-select-bg.png` (cap: 87 % schwarz, 0 % blau/weiß).
- Nebenwirkung: Titel weiß statt blau, Auswahlzeile ohne Hervorhebung, "Schließen" dunkel. Draw-Zeit-Variante (nur Panel-fps) scheitert, weil das Layout schon in set_vertex_attribs gebaut wird.
