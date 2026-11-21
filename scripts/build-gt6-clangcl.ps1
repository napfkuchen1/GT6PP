# Build GT6PP with clang-cl (Visual Studio 2022 Build Tools, "C++ Clang tools").
# Same sources and CMake as scripts/build-gt6.ps1; separate build dir gt6\build-clangcl.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/build-gt6-clangcl.ps1 [-Clean]
param([switch]$Clean)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$vw = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vw)) { throw "vswhere not found: install VS 2022 Build Tools (C++ workload + Clang)" }
$vs = & $vw -latest -products * -property installationPath
$vcvars = Join-Path $vs "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path $vcvars)) { throw "vcvars64.bat not found under $vs" }
$build = Join-Path $Root "gt6\build-clangcl"
if ($Clean -and (Test-Path $build)) { Remove-Item -Recurse -Force $build }
$sdk = (Resolve-Path (Join-Path $Root "third_party/ps3recomp")).Path.Replace([string][char]92, '/')
$src = (Resolve-Path (Join-Path $Root "gt6")).Path
$cmd = "`"$vcvars`" >nul && cmake -S `"$src`" -B `"$build`" -G Ninja -DCMAKE_BUILD_TYPE=Release " +
       "-DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DGT6_ENABLE_SPU=ON -DPS3RECOMP_DIR=`"$sdk`" " +
       "&& cmake --build `"$build`""
cmd /c $cmd
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Built: $build\gt6.exe" -ForegroundColor Green
