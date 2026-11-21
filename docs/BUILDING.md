# Building GT6PP

Paths are relative to the project root. Nothing here downloads or distributes
game data. Target disc: EU `BCES01893` (the dump folder may be labelled "USA";
the runtime reads the title id from `PARAM.SFO`).

## 1. Prerequisites

| Tool | Version used | Notes |
|---|---|---|
| Windows | 10/11 x64 | |
| Python | 3.11+ | `pip install cmake ninja pyelftools capstone` |
| CMake | 3.20+ | `python -m cmake` works |
| Ninja | 1.10+ | `python -m ninja` works |
| LLVM-MinGW | 20261020 (Clang 23.1.4, UCRT) | portable; extract to `tools/llvm-mingw/` |
| ps3recomp | v0.19.0, pin `ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5` | clone to `third_party/ps3recomp`, then apply `patches/ps3recomp-v0.19.0-gt6-eu-all.patch` |
| GT5P | `65c75d61ade58efb4f6af5f099c3b78b64c0a8e6` | reference sibling port; clone to `third_party/GT5P` (only `scripts/gen_hle_stubs.py` is used) |
| GTToolsSharp | 5.3.5 | volume extractor |
| RPCS3 | 0.0.43+ | only for offline SELF decryption here |

The port also builds with Visual Studio 2022 + clang-cl, which is what the
upstream GT5P uses. The instructions below use the portable LLVM-MinGW
toolchain because it needs no Visual Studio install.

```powershell
git clone https://github.com/sp00nznet/ps3recomp.git third_party/ps3recomp
git -C third_party/ps3recomp checkout ae92407bb1d899e3d32143e360fe6e6d4d8fa1b5
git -C third_party/ps3recomp apply ..\..\patches\ps3recomp-v0.19.0-gt6-eu-all.patch

git clone https://github.com/sp00nznet/GT5P.git third_party/GT5P
git -C third_party/GT5P checkout 65c75d61ade58efb4f6af5f099c3b78b64c0a8e6
```

The consolidated patch covers the MinGW SEH fixes and the functional EU/GT6
changes (see [docs/PATCHES.md](PATCHES.md)); it works for both toolchains.

## 2. Decrypt the executables

The retail `EBOOT.BIN` and `EMAIN.SELF` are encrypted SCE SELFs. RPCS3's offline
decryptor works without booting the game:

```powershell
# Use a copy; do not modify the dump in place.
Copy-Item "PS3-Version\Gran Turismo 6 (USA) (En,Ja,Fr)\PS3_GAME\USRDIR\EBOOT.BIN" work\bin\EBOOT.BIN
Copy-Item "PS3-Version\Gran Turismo 6 (USA) (En,Ja,Fr)\PS3_GAME\USRDIR\EMAIN.SELF" work\bin\EMAIN.SELF

tools\RPCS3\rpcs3.exe --decrypt work\bin\EBOOT.BIN
tools\RPCS3\rpcs3.exe --decrypt work\bin\EMAIN.SELF
```

Expected: `EBOOT.elf` (143,064 bytes) and `EMAIN.elf` (22,371,400 bytes,
SHA-256 `ACB00C19...A47A9B`, full value in `scripts/inputs.json`). Verify with
`powershell -File scripts/verify-inputs.ps1` (also run by the lift scripts; a
wrong region or stale decrypt fails here, not after a 30-minute lift). The
first four bytes of each are `7F 45 4C 46` (`\x7fELF`). The decryptor also
writes `boot.elf` into RPCS3's data directory; ignore it.

## 3. Extract `GT.VOL` (for inspection; optional at runtime)

The port serves the original `GT.VOL` through the VFS, so extraction is only for
asset research. GTToolsSharp:

```powershell
# Download the win-x64 release zip, extract to tools/GTToolsSharp/
tools\GTToolsSharp\win-x64\GTToolsSharp.exe unpack `
  --input "PS3-Version\Gran Turismo 6 (USA) (En,Ja,Fr)\PS3_GAME\USRDIR\GT.VOL" `
  --output "work\gt6_vol" --no-print --log "work\gt6_unpack.log"
```

On first run it creates `key.json` with the built-in keys. Expected: 4,207 TOC
entries, 32,591 files, ~25.1 GB. Keep `work/` out of git.

## 4. Analyse the PPU executable

```powershell
python third_party/ps3recomp/tools/ppu_loader.py work/bin/EMAIN.elf -o work/analysis/emain
```

Expected summary:

```
entry (OPD)      : 0x148e2e0 -> code 0x10230, toc 0x14ed560
OPD descriptors  : 44626
unique functions : 33091
firmware imports : 747 across 46 libraries
```

Filter the OPD list to executable addresses. The last OPD entry points at
`0xF908C4`, the start of `.rodata`, and must not be lifted as code:

```powershell
python -c "import json; f=json.load(open('work/analysis/emain/EMAIN.functions.json')); g=[x for x in f if int(x['start'],16)<0xF908C4]; json.dump(g,open('work/analysis/emain/functions_code.json','w'),indent=1); print(len(f),'->',len(g))"
```

Generate the HLE stub map from the ELF's own import descriptors:

```powershell
python third_party/GT5P/scripts/gen_hle_stubs.py work/bin/EMAIN.elf work/analysis/emain/hle_stubs.json
```

Expected: 747 stubs, 533 named, 214 unknown. The named list is informative; the
lifter only needs `stub` and `nid`.

## 5. Lift the PPU code

```powershell
python third_party/ps3recomp/tools/ppu_lifter.py work/bin/EMAIN.elf `
  --functions work/analysis/emain/functions_code.json `
  --hle-stubs work/analysis/emain/hle_stubs.json `
  --output gt6/generated `
  --code-end 0xF908C4 `
  --header-name ppu_recomp.h `
  --source-name ppu_recomp.c `
  --chunks 32 `
  --jobs 8
```

This writes `gt6/generated/ppu_recomp.h`, 32 `ppu_recomp_*.cpp` chunks, and a
function table. It is CPU-heavy and can take a long time for 33k functions.

The lift list is **not** the raw OPD table. It is generated reproducibly:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/gen-functions-gt6.ps1
```

Pipeline: `ppu_loader` (OPD) -> `find_functions` (seeded with the OPD list) ->
`tools/boundary_audit.py` -> `tools/add_computed_entries.py` ->
`work/analysis/emain/functions_corrected.json` (70,870 functions). The script
checks the intermediate and final lists against the SHA-256 values in
`scripts/inputs.json`, so a different result is caught immediately.
`scripts/relift-gt6.ps1` runs it automatically when the list is missing and
applies all post-lift patches (including `tools/b5b260_cache_fill_patch.py`,
which fills the file cache so an existing userdb loads; it fails loudly if its
anchors disappear). Prefer `relift-gt6.ps1` over the manual lifter call above.

`relift-gt6.ps1` also lifts all SPU images, so a fresh relift links without
restoring anything: step 8a extracts the four embedded SPU ELFs from `EMAIN.elf`
(`extract_spu_images.py`) and lifts them (`build_spu_workloads.py`, image ids 1-4,
`gt6/src/gen/spu_workloads.c`), 8b runs `scripts/lift-spu-jobs.ps1` for the raw
SPURS job images (ids 6+, `gt6/src/gen/spu_workloads_jobs.c`), 8c lifts the WWS
job-manager PM (id 5). The job images are cut from `EMAIN.elf` by
`tools/extract_spu_jobs.py` using `scripts/spu-jobs-manifest.json` (offset, size,
FNV-1a-64 per image; a mismatch fails) into `work/spu_jobs/dump/`, and
`lift-spu-jobs.ps1` re-checks every filename against the bytes. A previous `spu_lifted/jobs` tree is moved to
`work/ARCHIV/`, never deleted.
The lists are not committed because they are derived from the game binary.

Do not blindly lift every branch target above `0xF908C4`; the R-X segment runs
into read-only data.

## 6. Generate the HLE NID table

```powershell
python third_party/ps3recomp/tools/gen_hle_nids.py --all --out gt6/src/gen/ppu_hle_nids.cpp
```

Expected: ~1,200 handlers from ~93 modules. The table only includes handlers the
runtime actually implements; unknown NIDs fall through to a diagnostic.

## 7. Build

The included `scripts/build-gt6.ps1` sets up LLVM-MinGW, CMake, and Ninja:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-gt6.ps1
```

Manual equivalent:

```powershell
$mingw = (Resolve-Path "tools\llvm-mingw\llvm-mingw-20261020-ucrt-x86_64\bin").Path
$env:PATH = "$mingw;$env:PATH"
$env:CC = "$mingw\clang.exe"
$env:CXX = "$mingw\clang++.exe"

python -m cmake -S gt6 -B gt6/build -G Ninja `
  -DCMAKE_BUILD_TYPE=Release `
  -DPS3RECOMP_DIR="$((Resolve-Path third_party/ps3recomp).Path -replace '\\','/')" `
  -DCMAKE_C_FLAGS="-D_WIN32_WINNT=0x0A00" `
  -DCMAKE_CXX_FLAGS="-D_WIN32_WINNT=0x0A00"

python -m cmake --build gt6/build -j 8
```

Expected: `gt6/build/gt6.exe`. The first build compiles 32 large generated
translation units; it is the slowest build. Subsequent builds only rebuild
changed chunks.

### 7b. Alternative: clang-cl (VS 2022 Build Tools)

Standard toolchain of the ps3recomp ecosystem. Needs VS 2022 Build Tools with
the "C++ Clang tools for Windows" component
(`winget install Microsoft.VisualStudio.2022.BuildTools`, add the C++ workload + Clang).

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-gt6-clangcl.ps1
```

Output: `gt6/build-clangcl/gt6.exe` (separate build dir, MinGW build untouched).
No MinGW-specific SEH patch is needed. Run it with
`$env:GT6_BUILD_DIR="gt6\build-clangcl"` before `scripts/run-gt6.ps1` / `cap-gt6.ps1`.
Verified: boots to the language dialog, 158 ops at frame 2500 (same as MinGW).

## 8. Run

```powershell
# Windowed D3D12
gt6\build\gt6.exe work\bin\EMAIN.elf

# Headless: same vblank/flip clock and FIFO drain, no window
$env:PS3_HEADLESS="1"
gt6\build\gt6.exe work\bin\EMAIN.elf
```

Useful environment variables:

| Variable | Effect |
|---|---|
| `PS3_HEADLESS=1` | no window; ticker/FIFO still run |
| `PS3_VERBOSE=0` | less logging (important when timing matters) |
| `GT6_ARGS=...` | override the guest argv (default `boot_from=bdvd`) |
| `GT6_MAINSTACK=30` | after 30 s, print the main thread's guest location |
| `GT6_THREADS=1` | print per-PPU-thread state every 2 s |
| `GT6_NO_PRESENT=1` | do not start the present thread |
| `GT6_NO_FAULT_COMMIT=1` | let guest page faults crash instead of committing |
| `PS3_VFS_ROOT=...` | override the root for relative guest paths |
| `GT6_GAME_ROOT=...` | disc folder (default: `PS3-Version/Gran Turismo 6 (USA) (En,Ja,Fr)`; else the first `PS3-Version/<dir>` with `PS3_GAME/PARAM.SFO`) |

## Troubleshooting

**`GetCurrentThreadStackLimits` undeclared.** Set `_WIN32_WINNT=0x0A00` for the
runtime and the port (the provided CMake does this; the manual command above
also passes it).

**`__try` / `__except` undeclared, or `ppu_resv_break` linkage error.** Apply
`patches/ps3recomp-v0.19.0-gt6-eu-all.patch` to `third_party/ps3recomp` (see
[docs/PATCHES.md](PATCHES.md)). These are MSVC-only constructs that MinGW/Clang
does not parse.

**D3D12 link errors.** MinGW ignores `#pragma comment(lib, ...)`. The port's
CMake links `d3d12 dxgi dxguid d3dcompiler ws2_32 xinput ole32 bcrypt`
explicitly. If you add a backend, add its libraries too.

**Lifter output is huge / compiler runs out of memory.** Increase `--chunks`
(e.g. 64) or lower `--chunk-lines`; each chunk is a separate translation unit.

**`entry 0x... is not in the lifted function table`.** The entry OPD was
filtered out, or the function list is stale. Re-run `ppu_loader.py` and check
`EMAIN.loader.json`.

**Boot stops in `sys_cond_wait`.** This is expected until the missing signaller
is identified. Use `GT6_MAINSTACK=30` and compare the call chain with GT5P's
`docs/progress.md` Phase 16.

**Volume reader spins or corrupts memory.** Check the `setjmp`/`longjmp`
situation. GT5P required a host-side `setjmp` patch for its LZ decoder; GT6's
equivalent has not been located yet.

## What is not committed

`gt6/generated/`, `gt6/build/`, `work/`, `PS3-Version/`, `third_party/`, the
decrypted ELFs, `GT.VOL`, and `key.json` are all ignored. The repository contains
only the port's own source and documentation.
