# Verify that the decrypted EMAIN.elf (and optionally derived function lists)
# match the SHA-256 values in scripts/inputs.json (EU disc BCES01893).
# Usage: powershell -File scripts/verify-inputs.ps1 [-Strict] [-Files work/bin/EMAIN.elf]
#   default: only EMAIN.elf is mandatory; lists are checked if present (warn on mismatch).
#   -Strict: every listed file must exist and match.
param([switch]$Strict, [string[]]$Files, [string]$Inputs = "scripts/inputs.json")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$exp = Get-Content (Join-Path $Root "scripts\inputs.json") -Raw | ConvertFrom-Json
$names = $exp.PSObject.Properties.Name | Where-Object { $_ -notlike "_*" }
if ($Files) { $names = $names | Where-Object { $Files -contains $_ } }
$bad = 0
foreach ($n in $names) {
    $p = Join-Path $Root $n
    $must = $Strict -or ($n -eq "work/bin/EMAIN.elf")
    if (-not (Test-Path $p)) {
        if ($must) { Write-Host "MISSING  $n" -ForegroundColor Red; $bad++ } else { Write-Host "absent   $n (skipped)" }
        continue
    }
    $h = (Get-FileHash -Algorithm SHA256 $p).Hash
    if ($h -eq $exp.$n) { Write-Host "OK       $n" -ForegroundColor Green }
    elseif ($must) { Write-Host "MISMATCH $n`n  got      $h`n  expected $($exp.$n)" -ForegroundColor Red; $bad++ }
    else { Write-Host "WARN     $n differs (regenerate with scripts/gen-functions.ps1)" -ForegroundColor Yellow }
}
if ($bad) { throw "Input verification failed ($bad). Wrong disc/region or stale decrypt." }
