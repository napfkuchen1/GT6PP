# Repeated A/B boot runs: variants alternate, 2 parallel runs per batch, one probe.ps1 at a time.
#   scripts\boot-batch.ps1 -Name a33x -Variants "base|resv=PPU_RESV_STORE=1|one=@1" -Batches 2
# Variant: tag[=ENV=V;ENV2=V][@affinitymask]
param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Variants,
      [int]$Batches = 2, [int]$Seconds = 100, [string]$BaseEnv = "GT6_VOL_ROOT=work/gt6_vol_a32;A29_JMP=1")
$Root = Split-Path -Parent $PSScriptRoot
$probe = Join-Path $PSScriptRoot "probe.ps1"
for ($b = 1; $b -le $Batches; $b++) {
    foreach ($v in ($Variants -split "\|")) {
        $spec, $mask = $v -split "@", 2
        $tag, $extra = $spec -split "=", 2
        $p = @{ Name = "$Name$tag$b"; Parallel = 2; Seconds = $Seconds; Env = (@($BaseEnv, $extra) | Where-Object { $_ }) -join ";" }
        if ($mask) { $p.Affinity = [long]$mask }
        try { & $probe @p *> $null } catch { Write-Host "probe $($p.Name): $_" }
    }
}
python -I (Join-Path $PSScriptRoot "boot-outcome.py") (Join-Path $Root "work\probe_${Name}*")
