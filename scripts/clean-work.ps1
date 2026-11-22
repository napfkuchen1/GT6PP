# Archive old work\probe_* run folders and work\snap_* snapshots. Never deletes: moves to work\ARCHIV\runs\.
# Keeps the newest -KeepLast of each kind in place. Default is a dry run; pass -Apply to move.
#   powershell -File scripts\clean-work.ps1 -KeepLast 10          (dry run)
#   powershell -File scripts\clean-work.ps1 -KeepLast 10 -Apply
param(
    [int]$KeepLast = 10,
    [switch]$Apply
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Work = Join-Path $Root "work"
$Dest = Join-Path $Work "ARCHIV\runs"
foreach ($pat in @("probe_*", "snap_*")) {
    $all = Get-ChildItem $Work -Directory -Filter $pat | Sort-Object LastWriteTime -Descending
    $old = @($all | Select-Object -Skip $KeepLast)
    $bytes = 0
    foreach ($d in $old) { $bytes += (Get-ChildItem $d.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum }
    Write-Host ("{0}: {1} total, keep {2}, archive {3} ({4:N1} GB)" -f $pat, $all.Count, [Math]::Min($KeepLast, $all.Count), $old.Count, ($bytes / 1GB))
    if ($Apply -and $old.Count) {
        New-Item -ItemType Directory -Force -Path $Dest | Out-Null
        foreach ($d in $old) { Move-Item $d.FullName (Join-Path $Dest $d.Name) -Force }
    }
}
if (-not $Apply) { Write-Host "Dry run. Add -Apply to move folders to work\ARCHIV\runs." }
