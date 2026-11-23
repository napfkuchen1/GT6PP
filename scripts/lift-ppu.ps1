# PPU lift of work/bin/EMAIN.elf (1.22) into gt6/generated.
# Raw lift only; post-lift patches: scripts/post-lift.ps1 (see docs/analysis/PORT.md).
param([int]$Jobs = 8, [int]$Chunks = 40)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Elf = Join-Path $Root "work\bin\EMAIN.elf"
$A = Join-Path $Root "work\analysis\emain"
$Generated = Join-Path $Root "gt6-122\generated"
$Sdk = Join-Path $Root "third_party\ps3recomp-v020"
$Gt5p = Join-Path $Root "third_party\GT5P"
$env:PYTHONPATH = Join-Path $Sdk "tools"   # gen_hle_stubs.py imports elf_parser (old path third_party/ps3recomp is archived)
& (Join-Path $PSScriptRoot "verify-inputs.ps1") -Inputs "scripts\inputs.json" -Files "work/bin/EMAIN.elf"
if (-not (Test-Path (Join-Path $A "functions_corrected.json"))) { & (Join-Path $PSScriptRoot "gen-functions.ps1"); if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
New-Item -ItemType Directory -Force -Path $Generated | Out-Null
Write-Host "[1/3] HLE stub map"
python (Join-Path $Gt5p "scripts\gen_hle_stubs.py") $Elf (Join-Path $A "hle_stubs.json")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[2/3] PPU lift"
python (Join-Path $Sdk "tools\ppu_lifter.py") $Elf --functions (Join-Path $A "functions_corrected.json") --hle-stubs (Join-Path $A "hle_stubs.json") --output $Generated --code-end 0x10B8154 --header-name ppu_recomp.h --source-name ppu_recomp.c --chunks $Chunks --jobs $Jobs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[3/3] setjmp patch skipped (1.00 addresses); see PORT.md" 
Write-Host "Lift 1.22 raw complete." -ForegroundColor Green
