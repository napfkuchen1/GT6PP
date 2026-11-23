# Live-Lauf mit Pad-Aufzeichnung: spielen, Menue erreichen, Fenster schliessen.
# Ergebnis: work\padlog_<ts>.txt (Zeilen "<sek>:0x<maske>", direkt als PAD_SCRIPT nutzbar).
$Root = Split-Path -Parent $PSScriptRoot
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$env:GT6_BUILD_DIR = 'gt6\build'
$env:PAD_LOG = Join-Path $Root "work\padlog_$ts.txt"
Write-Host "Pad-Log: $env:PAD_LOG"
& (Join-Path $PSScriptRoot 'run-gt6.ps1') -Windowed -Seconds 3600
