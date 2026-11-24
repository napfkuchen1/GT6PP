# Vor Turn-Ende: verwaiste gt6.exe (> MaxSec) melden, mit -Kill beenden. Ueberwacher musste das 1x manuell tun (400 s).
param([int]$MaxSec = 120, [switch]$Kill)
Get-Process gt6 -ErrorAction SilentlyContinue | ForEach-Object {
  $age = [int]((Get-Date) - $_.StartTime).TotalSeconds
  Write-Host ("gt6 pid {0} age {1}s" -f $_.Id, $age)
  if ($Kill -and $age -gt $MaxSec) { Stop-Process -Id $_.Id -Force; Write-Host "killed" }
}
