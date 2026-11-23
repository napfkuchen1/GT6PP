# One pipeline, one build: decrypt -> function list -> PPU lift -> post-lift -> clang-cl/Ninja build.
# Game v1.22 + ps3recomp v0.20 are the only supported line. Idempotent: every stage is skipped if its output exists.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/build-all.ps1 [-Clean] [-Force] [-SkipLift]
#   -Clean    wipe gt6\build and reconfigure
#   -Force    redo decrypt/function-list/lift/post-lift even if outputs exist
#   -SkipLift only (re)build (default when gt6\generated exists)
# Stage inputs (not in repo): work/EMAIN_1.22.SELF (NPDRM SELF from the patched game) + klic via tools/self_decrypt_np.py,
#   or a ready work/bin/EMAIN.elf (sha256 pinned in scripts/inputs.json).
param([switch]$Clean, [switch]$Force, [switch]$SkipLift)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
function Step($t, [scriptblock]$b) { Write-Host "== $t" -ForegroundColor Cyan; & $b; if ($LASTEXITCODE -ne 0) { throw "$t failed ($LASTEXITCODE)" } }

# 1. decrypt (only if ELF missing; needs SELF + keys, see docs/analysis/PORT.md)
$Elf = Join-Path $Root "work\bin\EMAIN.elf"
if (-not (Test-Path $Elf)) { throw "work\bin\EMAIN.elf missing. Decrypt 1.22 EMAIN.SELF with tools\self_decrypt_np.py (see LEDGER section 7)." }
& (Join-Path $PSScriptRoot "verify-inputs.ps1") -Files "work/bin/EMAIN.elf"

# 2-4. function list -> lift -> post-lift
$Gen = Join-Path $Root "gt6\generated"
$haveLift = (Test-Path (Join-Path $Gen "ppu_recomp.h")) -and -not $Force
if (-not $SkipLift -and -not $haveLift) {
    $fc = Join-Path $Root "work\analysis\emain\functions_corrected.json"
    if ($Force -or -not (Test-Path $fc)) { Step "function list" { & (Join-Path $PSScriptRoot "gen-functions.ps1") } }
    Step "PPU lift"  { & (Join-Path $PSScriptRoot "lift-ppu.ps1") }
    Step "post-lift" { & (Join-Path $PSScriptRoot "post-lift.ps1") }
} else { Write-Host "== lift skipped (gt6\generated present; -Force to redo)" }

# 5. build (clang-cl + Ninja, Release, SPU on, all cores)
$vw = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vw)) { throw "vswhere not found: install VS 2022 Build Tools (C++ + Clang)" }
$vs = & $vw -latest -products * -property installationPath
$vcvars = Join-Path $vs "VC\Auxiliary\Build\vcvars64.bat"
$build = Join-Path $Root "gt6\build"
if ($Clean -and (Test-Path $build)) {
    $arch = Join-Path $Root ("ARCHIV\builds\build_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    New-Item -ItemType Directory -Force (Split-Path $arch) | Out-Null
    Move-Item $build $arch
}
$sdk = (Resolve-Path (Join-Path $Root "third_party\ps3recomp-v020")).Path.Replace([string][char]92, '/')
$src = Join-Path $Root "gt6"
$cmd = "`"$vcvars`" >nul && cmake -S `"$src`" -B `"$build`" -G Ninja -DCMAKE_BUILD_TYPE=Release " +
       "-DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DPS3RECOMP_DIR=`"$sdk`" " +
       "&& cmake --build `"$build`" -j $([Environment]::ProcessorCount)"
Step "build" { cmd /c $cmd }
if (-not (Test-Path (Join-Path $build "gt6.exe"))) { throw "gt6.exe missing after build" }
Write-Host ("Built: {0} ({1:N0} B)" -f "$build\gt6.exe", (Get-Item "$build\gt6.exe").Length) -ForegroundColor Green
