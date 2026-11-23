# 1.22 line (additive, 1.00 untouched): ppu_loader -> find_functions -> boundary_audit -> computed entries.
# In:  work/bin122/EMAIN.elf   Out: work/analysis/emain122/functions_corrected.json
# Usage: powershell -File scripts/gen-functions-gt6-122.ps1 [-Strict]
param([switch]$Strict)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Elf = Join-Path $Root "work\bin122\EMAIN.elf"
$A = Join-Path $Root "work\analysis\emain122"
$Sdk = Join-Path $Root "third_party\ps3recomp-v020\tools"
$CodeEnd = "0x10B8154"
& (Join-Path $PSScriptRoot "verify-inputs.ps1") -Inputs "scripts\inputs122.json" -Files "work/bin122/EMAIN.elf"
New-Item -ItemType Directory -Force -Path $A | Out-Null
function Step($t, [scriptblock]$b) { Write-Host $t; & $b; if ($LASTEXITCODE -ne 0) { throw "$t failed ($LASTEXITCODE)" } }
Step "[1/4] ppu_loader (OPD list)" { python (Join-Path $Sdk "ppu_loader.py") $Elf -o $A }
Step "[2/4] find_functions" { python (Join-Path $Sdk "find_functions.py") $Elf --seed-json (Join-Path $A "EMAIN.functions.json") --output (Join-Path $A "functions_found.json") }
Step "[3/4] boundary_audit" { python (Join-Path $Root "tools\boundary_audit.py") --elf $Elf --functions (Join-Path $A "functions_found.json") --opd (Join-Path $A "EMAIN.functions.json") --code-end $CodeEnd --out-functions (Join-Path $A "functions_corrected.json") --out-report (Join-Path $A "boundary-audit.md") }
Step "[4/4] computed-jump entries" { python (Join-Path $Root "tools\add_computed_entries.py") (Join-Path $A "functions_corrected.json") "122" }
if ($Strict) { & (Join-Path $PSScriptRoot "verify-inputs.ps1") -Inputs "scripts\inputs122.json" -Files "work/analysis/emain122/functions_found.json","work/analysis/emain122/functions_corrected.json" -Strict }
Write-Host "1.22 function list done (hashes not yet pinned unless -Strict)." -ForegroundColor Green
