# Hunt the rare nondeterministic boot branch that skips the language dialog and
# loads the menu packages (arcade/gtmode/garage/option .mpackage) instead of
# LanguageSelectRoot.gpb. Each run is killed as soon as it takes the dialog path;
# on the menu path it waits for an RSX capture at -Frame and stops.
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts/hunt-menu-branch.ps1 [-MaxRuns 40] [-Frame 4000]
param(
    [int]$MaxRuns = 40,
    [int]$Frame = 4000,
    [int]$WaitSeconds = 240
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BuildDir = if ($env:GT6_BUILD_DIR) { $env:GT6_BUILD_DIR } else { "gt6\build" }
$Exe = Join-Path $Root "$BuildDir\gt6.exe"
$Elf = Join-Path $Root "work\bin\EMAIN.elf"
$Out = Join-Path $Root "work\hunt"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$mingw = Get-ChildItem -Path (Join-Path $Root "tools\llvm-mingw") -Directory -ErrorAction SilentlyContinue |
    ForEach-Object { Join-Path $_.FullName "bin\clang.exe" } | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($mingw) { $env:PATH = "$(Split-Path -Parent $mingw);$env:PATH" }
$env:PS3_HEADLESS = "1"; $env:GT6_UNBUF = "1"; $env:PS3_VERBOSE = "0"
for ($i = 1; $i -le $MaxRuns; $i++) {
    $cap = Join-Path $Out "cap$i"
    $env:RSX_CAP = "${Frame}:1"; $env:RSX_CAP_DIR = $cap
    $log = Join-Path $Out "run$i.log"
    Remove-Item $log, "$log.err" -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $Exe -ArgumentList @($Elf) -WorkingDirectory $Root `
        -RedirectStandardOutput $log -RedirectStandardError "$log.err" -NoNewWindow -PassThru
    $t0 = Get-Date; $verdict = "timeout"
    while (((Get-Date) - $t0).TotalSeconds -lt 150 -and -not $p.HasExited) {
        Start-Sleep -Seconds 4
        $t = Get-Content "$log.err" -Raw -ErrorAction SilentlyContinue
        if ($t -match 'LanguageSelectRoot') { $verdict = "dialog"; break }
        if ($t -match 'arcade\.mpackage') { $verdict = "MENU"; break }
    }
    if ($verdict -eq "MENU") {
        $t1 = Get-Date
        while (((Get-Date) - $t1).TotalSeconds -lt $WaitSeconds -and -not (Test-Path (Join-Path $cap "frame_00\backbuffer.bmp"))) { Start-Sleep -Seconds 5 }
    }
    try { $p.Kill() } catch {}
    Start-Sleep -Milliseconds 500
    Write-Host ("run {0}: {1}" -f $i, $verdict)
    if ($verdict -eq "MENU") { Write-Host "MENU BRANCH HIT: $log.err  cap=$cap"; break }
}
