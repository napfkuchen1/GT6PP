# One entry point for GT6 probe / capture / soak runs. Replaces ad-hoc run-gt6/cap-gt6/soak calls.
# - uses gt6\build\gt6.exe (single build), warns if sources newer than exe
# - validates env + PAD_SCRIPT up front (fails loud instead of running an invalid test)
# - archives userdb (never deletes), writes each run to work\probe_<Name>_<ts>_<i>\
# - runs N instances in parallel, then checks the expected probe lines in every log
#
# Usage:
#   powershell -File scripts\probe.ps1 -Name base -Seconds 320 -Frame 4200
#   powershell -File scripts\probe.ps1 -Name pad -Env "PS3_CALLTRACE_AFTER=200;PS3_CALLTRACE=500" -Expect "CALLTRACE" -PadScript "120:0x4000"
#   powershell -File scripts\probe.ps1 -Name soak -Parallel 4 -Seconds 320
# -Env      : "K=V;K2=V2" (separator ';', values must not contain ';')
# -Expect   : regexes that MUST appear in stdout/stderr, else the run is INVALID (not "hypothesis refuted")
# -Frame    : >0 enables RSX capture at that frame (windowed run, PS3_HEADLESS removed) + pixel stats
# -FreezeSec: STALLED kill when SetPrepareFlip heartbeat unchanged this long after arming (log size ignored); writes STALLED@<s> to boot.txt. -1 = off
# -StopOn   : regex, early kill when it appears in the log. With -Frame: early kill once capture frames exist + pad done + -Expect met.
# -Seconds  : 0 (default) = derive from -PadScript (last key + 60) else 220
# -KeepDb   : keep the persistent userdb in the per-run hdd0 copy (default: fresh db). Shared work\gt6_hdd0 is never modified.
# -Boot     : orig|noadj|notut - which boot.adc variant is installed (from work\ARCHIV\boot.adc.*); omitted = keep current.
#             The active variant is always detected by hash, printed and written to <rundir>\boot.txt.
param(
    [Parameter(Mandatory)][string]$Name,
    [int]$Seconds = 0,          # 0 = derive: PadScript -> last key + 60 s, else 220 (steady-state)
    [int]$FreezeSec = 30,       # STALLED: kill if the SetPrepareFlip heartbeat (not log size) is unchanged this long after arming; -1 = off
    [string]$StopOn = "",       # regex: early kill as soon as it appears in the log (e.g. PDIPFS/59/FI)
    [int]$Parallel = 1,
    [string]$Env = "",
    [string[]]$Expect = @(),
    [string]$PadScript = "",
    [int]$Frame = 0,
    [switch]$KeepDb,
    [string]$Hdd0Src = "",
    [long]$Affinity = 0,       # >0: host CPU mask for gt6.exe (race experiments)
    [ValidateSet("", "orig", "noadj", "notut")][string]$Boot = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"

# --- build selection -------------------------------------------------------
# Single build: gt6\build\gt6.exe (ps3recomp v0.20 + game v1.22).
$Exe = Get-Item (Join-Path $Root "gt6\build\gt6.exe") -ErrorAction SilentlyContinue
if (-not $Exe) { throw "No gt6\build\gt6.exe. Build first (scripts\build-all.ps1)." }
$Elf = Join-Path $Root "work\bin\EMAIN.elf"
if (-not (Test-Path $Elf)) { throw "Missing $Elf." }
$srcNewest = Get-ChildItem -Path (Join-Path $Root "gt6\src"), (Join-Path $Root "third_party\ps3recomp-v020\runtime"), (Join-Path $Root "third_party\ps3recomp-v020\libs") `
    -Recurse -Include *.c, *.cpp, *.h -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\gen\\' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host ("EXE: {0}  ({1})" -f $Exe.FullName, $Exe.LastWriteTime)
if ($srcNewest -and $srcNewest.LastWriteTime -gt $Exe.LastWriteTime) {
    Write-Warning ("Source newer than exe: {0} ({1}). Rebuild first or new probes stay silent." -f $srcNewest.Name, $srcNewest.LastWriteTime)
}

# --- env validation --------------------------------------------------------
$pairs = [ordered]@{}
foreach ($p in ($Env -split ";" | Where-Object { $_ })) {
    $kv = $p -split "=", 2
    if ($kv.Count -ne 2 -or $kv[0] -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { throw "Bad -Env entry '$p' (need K=V)." }
    if ($kv[0] -eq "PS3_HEADLESS") { throw "PS3_HEADLESS is a presence flag (even '0'); never pass it. Headless is set automatically when -Frame is 0." }
    $pairs[$kv[0]] = $kv[1]
}
if ($PadScript) {
    foreach ($tok in ($PadScript -split "\s+" | Where-Object { $_ })) {
        if ($tok -notmatch '^\d+(\.\d+)?:0x[0-9A-Fa-f]+$') { throw "Bad PAD_SCRIPT token '$tok' (need <sek>:0x<hex>, e.g. 120:0x4000)." }
        if ([Convert]::ToInt32(($tok -split ":0x")[1], 16) -eq 0) { throw "PAD_SCRIPT token '$tok' has mask 0." }
    }
    $pairs["PAD_SCRIPT"] = $PadScript
    $Expect += "press 0x[0-9A-Fa-f]*[1-9A-Fa-f]"
}
if ($Seconds -le 0) {
    $Seconds = 220
    if ($PadScript) { $last = ($PadScript -split "\s+" | Where-Object { $_ } | ForEach-Object { [double](($_ -split ":")[0]) } | Measure-Object -Maximum).Maximum; $Seconds = [int]([math]::Ceiling($last) + 60) }
    Write-Host "Seconds (derived): $Seconds"
}
# earliest time after which a silent log means FROZEN (timed events must be through)
$armAt = 20
if ($PadScript) { $armAt = [math]::Max($armAt, $last + 5) }
foreach ($k in "PS3_SNAP_AT", "PS3_CALLTRACE_AFTER") { if ($pairs.Contains($k)) { $armAt = [math]::Max($armAt, [double](($pairs[$k] -split "[;,]")[-1]) + 5) } }
$pairs["GT6_UNBUF"] = "1"
if (-not $pairs.Contains("PS3_VERBOSE")) { $pairs["PS3_VERBOSE"] = "0" }
if ($pairs.Contains("PS3_CALLTRACE") -and -not $pairs.Contains("PS3_CALLTRACE_AFTER")) {
    Write-Warning "PS3_CALLTRACE without PS3_CALLTRACE_AFTER fills the budget during boot. Use PS3_CALLTRACE_AFTER=200."
}

# --- boot.adc variant (baseline) --------------------------------------------
# -Env GT6_VOL_ROOT=<dir> selects another tree (e.g. the 1.22 overlay); the 1.00 boot variants never apply to it.
$defVol = [IO.Path]::GetFullPath((Join-Path $Root "work\gt6_vol"))
$volRoot = if ($pairs.Contains("GT6_VOL_ROOT")) { $pairs["GT6_VOL_ROOT"] } else { $env:GT6_VOL_ROOT }
if (-not $volRoot) { $volRoot = $defVol } elseif (-not [IO.Path]::IsPathRooted($volRoot)) { $volRoot = Join-Path $Root $volRoot }
$volRoot = [IO.Path]::GetFullPath($volRoot).TrimEnd('\', '/')
$customVol = $volRoot -ne $defVol
if ($customVol -and $Boot) { throw "-Boot patches the 1.00 boot.adc in work\gt6_vol; do not combine it with GT6_VOL_ROOT." }
$bootFile = Join-Path $volRoot "projects\gt6\boot\boot.adc"
$variants = [ordered]@{ orig = "boot.adc.orig"; noadj = "boot.adc.nodlg_noadjust"; notut = "boot.adc.nodlg_noadjust_notut" }
if (-not (Test-Path $bootFile)) { throw "Missing $bootFile (run scripts\extract-gtvol.ps1)." }
if ($Boot) {
    $src = Join-Path $Root ("work\ARCHIV\" + $variants[$Boot])
    if (-not (Test-Path $src)) { throw "Variant file missing: $src" }
    if ((Get-FileHash $src).Hash -ne (Get-FileHash $bootFile).Hash) {
        $known = $variants.Values | ForEach-Object { Join-Path $Root "work\ARCHIV\$_" } | Where-Object { Test-Path $_ } | ForEach-Object { (Get-FileHash $_).Hash }
        if ((Get-FileHash $bootFile).Hash -notin $known) {
            Copy-Item $bootFile (Join-Path $Root ("work\ARCHIV\boot.adc.unknown_{0}" -f $Ts)); Write-Warning "Unknown boot.adc saved to ARCHIV before switching."
        }
        Copy-Item $src $bootFile -Force
    }
}
$curHash = (Get-FileHash $bootFile).Hash
$BootName = "unknown"
foreach ($k in $variants.Keys) { $f = Join-Path $Root ("work\ARCHIV\" + $variants[$k]); if ((Test-Path $f) -and (Get-FileHash $f).Hash -eq $curHash) { $BootName = $k } }
if ($customVol) { $BootName = "vol:" + (Split-Path -Leaf $volRoot) }
Write-Host "BOOT variant: $BootName"

# --- toolchain DLLs --------------------------------------------------------
$mingw = Get-ChildItem -Path (Join-Path $Root "tools\llvm-mingw") -Directory -ErrorAction SilentlyContinue |
    ForEach-Object { Join-Path $_.FullName "bin\clang.exe" } | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($mingw) { $env:PATH = "$(Split-Path -Parent $mingw);$env:PATH" }

# --- userdb archive (never delete) -----------------------------------------
if (-not $KeepDb -and $false) {  # replaced by per-run hdd0 copy (GT6_HDD0): no shared userdb, no lock
    # wait up to ~30 s for a still running gt6.exe (holds the userdb lock); never kill it
    $waited = 0
    while ((Get-Process gt6 -ErrorAction SilentlyContinue) -and $waited -lt 30) { Start-Sleep -Seconds 1; $waited++ }
    if (Get-Process gt6 -ErrorAction SilentlyContinue) { Write-Host "ABORT: gt6.exe still running after 30 s (userdb locked). Not killing it. Retry later."; exit 2 }
    $dbDir = Join-Path $Root "work\gt6_hdd0\game\BCES01893\USRDIR\db"
    $arch = Join-Path $Root "work\ARCHIV"; New-Item -ItemType Directory -Force -Path $arch | Out-Null
    Get-ChildItem $dbDir -Filter "userdb*.dat" -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item $_.FullName (Join-Path $arch ("{0}_{1}.dat" -f $_.BaseName, $Ts)) -Force
        Write-Host "userdb archived: $($_.Name)"
    }
}

# --- per-run hdd0: junctions to big read-only parts, small parts copied (gate < 200 MB) ---
function New-RunHdd0([string]$Src, [string]$Dst) {
    $usr = "game\BCES01893\USRDIR"
    New-Item -ItemType Directory -Force -Path (Join-Path $Dst $usr) | Out-Null
    Get-ChildItem $Src -Force | Where-Object { $_.Name -ne "game" } | ForEach-Object {
        if ($_.PSIsContainer) { cmd /c mklink /J "$Dst\$($_.Name)" "$($_.FullName)" | Out-Null } else { Copy-Item $_.FullName $Dst -Force }
    }
    Get-ChildItem (Join-Path $Src "game") -Force | Where-Object { $_.Name -ne "BCES01893" } | ForEach-Object {
        if ($_.PSIsContainer) { cmd /c mklink /J "$Dst\game\$($_.Name)" "$($_.FullName)" | Out-Null } else { Copy-Item $_.FullName (Join-Path $Dst "game") -Force }
    }
    Get-ChildItem (Join-Path $Src "game\BCES01893") -Force | Where-Object { $_.Name -ne "USRDIR" } | ForEach-Object {
        if ($_.PSIsContainer) { cmd /c mklink /J "$Dst\game\BCES01893\$($_.Name)" "$($_.FullName)" | Out-Null } else { Copy-Item $_.FullName (Join-Path $Dst "game\BCES01893") -Force }
    }
    Get-ChildItem (Join-Path $Src $usr) -Force | ForEach-Object {
        $t = Join-Path $Dst "$usr\$($_.Name)"
        if ($_.PSIsContainer -and $_.Name -in @("db","replay","savedata","PDIPFS")) { Copy-Item $_.FullName $t -Recurse -Force }
        elseif ($_.PSIsContainer) { cmd /c mklink /J "$t" "$($_.FullName)" | Out-Null }
        else { Copy-Item $_.FullName $t -Force }
    }
    # gate: real (non-junction) size must stay small
    $sz = 0; Get-ChildItem $Dst -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } | ForEach-Object { $sz += $_.Length }
    if ($sz -gt 200MB) { throw "run hdd0 too big: $([int]($sz/1MB)) MB (gate 200 MB)" }
}
function Remove-RunHdd0([string]$Dst) {
    if (-not (Test-Path $Dst)) { return }
    # junctions first via rmdir (never recursive into source), then remaining small copy
    Get-ChildItem $Dst -Recurse -Force -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint } | Sort-Object { $_.FullName.Length } -Descending | ForEach-Object { cmd /c rmdir "$($_.FullName)" | Out-Null }
    Remove-Item $Dst -Recurse -Force -ErrorAction SilentlyContinue
}
$free = (Get-PSDrive C).Free / 1GB
if ($free -lt 100) { Write-Host ("ABORT: C: only {0:N0} GB free (<100 GB)" -f $free); exit 2 }
if ($Parallel -gt 2) { Write-Host "Parallel capped to 2"; $Parallel = 2 }
# --- launch ----------------------------------------------------------------
foreach ($k in $pairs.Keys) { Set-Item "Env:$k" $pairs[$k] }
if ($Frame -le 0) { $env:PS3_HEADLESS = "1" } else { Remove-Item Env:PS3_HEADLESS -ErrorAction SilentlyContinue }
$runs = @()
try {
    for ($i = 1; $i -le $Parallel; $i++) {
        $dir = Join-Path $Root ("work\probe_{0}_{1}_{2}" -f $Name, $Ts, $i)
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        if ($Frame -gt 0) { if (-not $pairs.Contains("RSX_CAP")) { $env:RSX_CAP = "${Frame}:1" }; $env:RSX_CAP_DIR = $dir }
        $log = Join-Path $dir "run.log"
        # per-run hdd0 copy without userdb (fresh db); shared work\gt6_hdd0 stays untouched
        $hd = Join-Path $dir "hdd0"
        $src0 = if ($Hdd0Src) { $Hdd0Src } else { Join-Path $Root "work\gt6_hdd0" }
        New-RunHdd0 $src0 $hd
        if (-not $KeepDb) { Get-ChildItem (Join-Path $hd "game\BCES01893\USRDIR\db") -Filter "userdb*.dat" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue }
        $env:GT6_HDD0 = $hd
        # per-run empty cache partition: a stale game024.db from an earlier run changes the boot
        if (-not $pairs.Contains("GT6_HDD1")) { $h1 = Join-Path $dir "hdd1"; New-Item -ItemType Directory -Force -Path $h1 | Out-Null; $env:GT6_HDD1 = $h1 }
        Set-Content (Join-Path $dir "boot.txt") ("boot={0} exe={1} env={2}" -f $BootName, $Exe.FullName, (($pairs.Keys | ForEach-Object { "$_=$($pairs[$_])" }) -join ";"))
        $proc = Start-Process -FilePath $Exe.FullName -ArgumentList @($Elf) -WorkingDirectory $Root `
            -NoNewWindow -PassThru -RedirectStandardOutput $log -RedirectStandardError "$log.err"
        if ($Affinity -gt 0) { $proc.ProcessorAffinity = [IntPtr]$Affinity }
        $null = $proc.Handle   # cache the handle, otherwise ExitCode is empty after exit
        $runs += [pscustomobject]@{ I = $i; Dir = $dir; Log = $log; Proc = $proc }
        Start-Sleep -Seconds 2
    }
} finally {
    foreach ($k in $pairs.Keys) { Remove-Item "Env:$k" -ErrorAction SilentlyContinue }
    Remove-Item Env:RSX_CAP, Env:RSX_CAP_DIR, Env:PS3_HEADLESS, Env:GT6_HDD0, Env:GT6_HDD1 -ErrorAction SilentlyContinue
}
Write-Host "Started $Parallel run(s), waiting up to ${Seconds}s ..."
$t0 = Get-Date; $deadline = $t0.AddSeconds($Seconds)
foreach ($r in $runs) { $r | Add-Member -NotePropertyMembers @{ Pos = @{}; Flips = 0; LastBeat = $t0.AddSeconds($armAt); End = ""; EndT = 0 } }
$capCount = 1
if ($pairs.Contains("RSX_CAP")) { $pp = ($pairs["RSX_CAP"] -split ":"); if ($pp.Count -ge 2) { $capCount = [int]$pp[1] } }
$padDone = 0; if ($PadScript) { $padDone = $last + 5 }
while ((Get-Date) -lt $deadline -and ($runs | Where-Object { -not $_.Proc.HasExited -and -not $_.End })) {
    Start-Sleep -Seconds 2
    $now = Get-Date; $el = ($now - $t0).TotalSeconds
    foreach ($r in $runs) {
        if ($r.Proc.HasExited -or $r.End) { continue }
        # heartbeat: count only SetPrepareFlip lines in NEW log bytes (log spam does not count)
        $newFlips = 0; $newText = ""
        foreach ($f in @($r.Log, "$($r.Log).err")) {
            if (-not (Test-Path $f)) { continue }
            try {
                $fs = [IO.File]::Open($f, 'Open', 'Read', 'ReadWrite')
                $pos = if ($r.Pos.ContainsKey($f)) { $r.Pos[$f] } else { 0L }
                if ($fs.Length -gt $pos) {
                    $buf = New-Object byte[] ($fs.Length - $pos); [void]$fs.Seek($pos, 'Begin'); [void]$fs.Read($buf, 0, $buf.Length)
                    $r.Pos[$f] = $fs.Length
                    $t = [Text.Encoding]::ASCII.GetString($buf)
                    $newFlips += ([regex]::Matches($t, "SetPrepareFlip")).Count
                    if ($StopOn) { $newText += $t }
                }
                $fs.Close()
            } catch {}
        }
        if ($newFlips -gt 0) { $r.Flips += $newFlips; $r.LastBeat = $now }
        if ($FreezeSec -gt 0 -and $el -gt $armAt -and ($now - $r.LastBeat).TotalSeconds -ge $FreezeSec) {
            $r.End = "STALLED"; $r.EndT = [int]$el
        }
        elseif ($StopOn -and $newText -match $StopOn) { $r.End = "EARLY(StopOn)"; $r.EndT = [int]$el }
        elseif ($Frame -gt 0 -and $el -gt $padDone) {
            # early kill: all expected outputs exist (capture frames written, pad done, -Expect satisfied)
            $capOk = $true
            for ($ci = 0; $ci -lt $capCount; $ci++) { if (-not (Test-Path (Join-Path $r.Dir ("frame_{0:D2}\backbuffer.bmp" -f $ci)))) { $capOk = $false } }
            if ($capOk) {
                $txt = ""; foreach ($f in @($r.Log, "$($r.Log).err")) { if (Test-Path $f) { $txt += (Get-Content $f -Raw -ErrorAction SilentlyContinue) } }
                $allx = $true; foreach ($rx in $Expect) { if ($txt -notmatch $rx) { $allx = $false } }
                if ($allx) { $r.End = "EARLY(outputs)"; $r.EndT = [int]$el }
            }
        }
        if ($r.End) { try { $r.Proc.Kill($true) } catch { try { $r.Proc.Kill() } catch {} }; try { & taskkill.exe /F /T /PID $r.Proc.Id 2>&1 | Out-Null } catch {} }
    }
}
foreach ($r in $runs) {
    $el = [int]((Get-Date) - $t0).TotalSeconds
    if (-not $r.End) { if ($r.Proc.HasExited) { $r.End = "RUN DONE"; $r.EndT = $el } else { $r.End = "TIMEOUT"; $r.EndT = $Seconds; try { $r.Proc.Kill() } catch {}; try { & taskkill.exe /F /T /PID $r.Proc.Id 2>&1 | Out-Null } catch {} } }
    try { [void]$r.Proc.WaitForExit(5000) } catch {}
    $line = if ($r.End -eq "STALLED") { "STALLED@$($r.EndT)s flips=$($r.Flips) (heartbeat unchanged ${FreezeSec}s)" } else { "$($r.End) $($r.EndT)s flips=$($r.Flips)" }
    try { if ($r.Proc.HasExited) { $line += (" exit=0x{0:X8}" -f $r.Proc.ExitCode) } } catch {}
    Add-Content (Join-Path $r.Dir "boot.txt") $line
    Write-Host ("run {0}: END {1}" -f $r.I, $line)
}
# no gt6 may survive the probe: sweep our own PIDs (process trees)
foreach ($r in $runs) { try { if (-not $r.Proc.HasExited) { $r.Proc.Kill($true) } } catch {} }
Start-Sleep -Milliseconds 500
$left = @(Get-Process gt6 -ErrorAction SilentlyContinue)
Write-Host ("gt6 processes left after probe: {0}" -f $left.Count)
foreach ($r in $runs) { Remove-RunHdd0 (Join-Path $r.Dir 'hdd0') }
Start-Sleep -Milliseconds 500

# --- verify ----------------------------------------------------------------
$bad = 0
foreach ($r in $runs) {
    $text = ""
    foreach ($f in @($r.Log, "$($r.Log).err")) { if (Test-Path $f) { $text += (Get-Content $f -Raw -ErrorAction SilentlyContinue) } }
    $status = "OK"; $why = @()
    if ($text.Length -lt 1000) { $status = "INVALID"; $why += "log nearly empty ($($text.Length) bytes)" }
    foreach ($rx in $Expect) { if ($text -notmatch $rx) { $status = "INVALID"; $why += "missing expected /$rx/" } }
    $unres = ([regex]::Matches($text, "unresolved NID")).Count
    $dlg = if ($text -match 'LanguageSelectRoot') { "langdlg" } else { "no-langdlg" }
    $stat = ""
    if ($Frame -gt 0) {
        $bmp = Join-Path $r.Dir "frame_00\backbuffer.bmp"
        if (Test-Path $bmp) {
            Add-Type -AssemblyName System.Drawing
            $img = [System.Drawing.Bitmap]::FromFile($bmp); $n = 0; $blk = 0
            for ($y = 0; $y -lt $img.Height; $y += 4) { for ($x = 0; $x -lt $img.Width; $x += 4) {
                $c = $img.GetPixel($x, $y); $n++; if ($c.R -lt 16 -and $c.G -lt 16 -and $c.B -lt 16) { $blk++ } } }
            $img.Save((Join-Path $r.Dir "frame_00\backbuffer.png"), [System.Drawing.Imaging.ImageFormat]::Png); $img.Dispose()
            $stat = " black={0:P1}" -f ($blk / $n)
        } else { $status = "INVALID"; $why += "frame $Frame not captured (not reached in ${Seconds}s)" }
    }
    if ($status -ne "OK") { $bad++ }
    Write-Host ("run {0}: {1} boot={7} unresolved={2} {3}{4} {5}  -> {6}" -f $r.I, $status, $unres, $dlg, $stat, ($why -join "; "), $r.Dir, $BootName)
}
$PyExe = Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python313\python.exe"
foreach ($r in $runs) { if (Test-Path $PyExe) { & $PyExe -I (Join-Path $PSScriptRoot "checkpoints.py") $r.Dir } }
if ($bad) { Write-Host "WARNING: $bad run(s) INVALID - do not draw conclusions from them."; exit 1 }
Write-Host "All runs valid. Logs: work\probe_${Name}_${Ts}_*"
