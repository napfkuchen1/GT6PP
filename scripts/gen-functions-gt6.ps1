# Regenerate the PPU function list deterministically from work/bin/EMAIN.elf:
#   ppu_loader (OPD) -> find_functions (seeded) -> boundary_audit -> add_computed_entries
# Output: work/analysis/emain/functions_corrected.json (consumed by relift-gt6.ps1).
# Usage: powershell -File scripts/gen-functions-gt6.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Elf = Join-Path $Root "work\bin\EMAIN.elf"
$A = Join-Path $Root "work\analysis\emain"
$Sdk = Join-Path $Root "third_party\ps3recomp\tools"
& (Join-Path $PSScriptRoot "verify-inputs.ps1") -Files "work/bin/EMAIN.elf"
New-Item -ItemType Directory -Force -Path $A | Out-Null
function Step($t, [scriptblock]$b) { Write-Host $t; & $b; if ($LASTEXITCODE -ne 0) { throw "$t failed ($LASTEXITCODE)" } }
Step "[1/4] ppu_loader (OPD list)" { python (Join-Path $Sdk "ppu_loader.py") $Elf -o $A }
Step "[2/4] find_functions" { python (Join-Path $Sdk "find_functions.py") $Elf --seed-json (Join-Path $A "EMAIN.functions.json") --output (Join-Path $A "functions_found.json") }
Step "[3/4] boundary_audit" { python (Join-Path $Root "tools\boundary_audit.py") --elf $Elf --functions (Join-Path $A "functions_found.json") --opd (Join-Path $A "EMAIN.functions.json") --out-functions (Join-Path $A "functions_corrected.json") --out-report (Join-Path $A "boundary-audit.md") }
Step "[4/4] computed-jump entries" { python (Join-Path $Root "tools\add_computed_entries.py") (Join-Path $A "functions_corrected.json") }
& (Join-Path $PSScriptRoot "verify-inputs.ps1") -Files "work/analysis/emain/functions_found.json","work/analysis/emain/functions_corrected.json" -Strict
Write-Host "Function list reproduced and hash-verified." -ForegroundColor Green
