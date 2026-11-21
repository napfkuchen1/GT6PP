# M2 exit check for the EU disc: boot GT6PP N times headless and compare the
# set of loaded assets. A run's fingerprint is the SHA-256 of the sorted, unique
# "[GT6] script/pfs override" paths (guest addresses stripped). Identical
# fingerprints across all runs = deterministic asset load.
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts/soak-gt6-eu.ps1 [-Runs 8] [-Seconds 90]
param(
    [int]$Runs = 8,
    [int]$Seconds = 90
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BuildDir = if ($env:GT6_BUILD_DIR) { $env:GT6_BUILD_DIR } else { "gt6\build" }
$Exe = Join-Path $Root "$BuildDir\gt6.exe"
$Elf = Join-Path $Root "work\bin\EMAIN.elf"
$OutDir = Join-Path $Root ("work\soak_eu_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (-not (Test-Path $Exe)) { throw "Missing $Exe. Build first." }

$mingw = Get-ChildItem -Path (Join-Path $Root "tools\llvm-mingw") -Directory -ErrorAction SilentlyContinue |
    ForEach-Object { Join-Path $_.FullName "bin\clang.exe" } |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($mingw) { $env:PATH = "$(Split-Path -Parent $mingw);$env:PATH" }
$env:PS3_HEADLESS = "1"
$env:GT6_UNBUF = "1"
if (-not $env:PS3_VERBOSE) { $env:PS3_VERBOSE = "0" }

$rows = @()
for ($i = 1; $i -le $Runs; $i++) {
    $log = Join-Path $OutDir "run$i.log"
    Remove-Item $log, "$log.err" -ErrorAction SilentlyContinue
    $udb = Join-Path $Root "work\gt6_hdd0\game\BCES01893\USRDIR\db\userdb0101.dat"
    $pre = if (Test-Path $udb) { (Get-FileHash $udb -Algorithm SHA256).Hash.Substring(0, 12) } else { "-" }
    $p = Start-Process -FilePath $Exe -ArgumentList @($Elf) -WorkingDirectory $Root `
        -RedirectStandardOutput $log -RedirectStandardError "$log.err" -NoNewWindow -PassThru
    if (-not $p.WaitForExit($Seconds * 1000)) {
        try { $p.Kill() } catch {}
        Start-Sleep -Milliseconds 300
    }
    $text = ""
    foreach ($f in @($log, "$log.err")) {
        if (Test-Path $f) { $text += (Get-Content $f -Raw -ErrorAction SilentlyContinue) }
    }
    $assets = [regex]::Matches($text, 'serving (?:decrypted |plaintext )?(\S+) \(') |
        ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
    $bytes = [Text.Encoding]::UTF8.GetBytes(($assets -join "`n"))
    $hash = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '').Substring(0, 16)
    $unres = ([regex]::Matches($text, "unresolved NID")).Count
    $dlg = if ($text -match 'LanguageSelectRoot') { 1 } else { 0 }
    $rows += [pscustomobject]@{ Run = $i; Assets = $assets.Count; Fingerprint = $hash; UserdbPre = $pre; UnresolvedNID = $unres; LangDialogGpb = $dlg }
    Write-Host ("run {0}: assets={1} fp={2} udbpre=$pre unresolved={3} langdlg={4}" -f $i, $assets.Count, $hash, $unres, $dlg)
}
$rows | Format-Table -AutoSize
$uniq = ($rows | Select-Object -ExpandProperty Fingerprint | Sort-Object -Unique).Count
if ($uniq -eq 1 -and ($rows[0].Assets -gt 0)) { Write-Host "DETERMINISTIC: $Runs/$Runs identical asset sets." }
else { Write-Host "NOT identical: $uniq distinct fingerprints (or no assets loaded)." }
