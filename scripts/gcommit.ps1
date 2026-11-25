# Commit als napfkuchen1, ohne Trailer. Usage: pwsh -File scripts\gcommit.ps1 "msg" [-Push]
# Prueft vor -Push, dass keine verbotenen Autoren/Trailer in fork/eu-first-build..HEAD stehen.
param([Parameter(Mandatory)][string]$Msg, [switch]$Push)
$ErrorActionPreference = "Stop"
$ErrorActionPreference = "Continue"
git add -A -- . ":!work" 2>$null
git -c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com commit -m $Msg
if ($Push) {
  $bad = git log fork/eu-first-build..HEAD --format='%an <%ae>%n%b' | Select-String -Pattern "claude|co-authored|anthropic|einmalig" -SimpleMatch:$false
  if ($bad) { Write-Host "ABORT push, verbotene Treffer:"; $bad | Select -First 5; exit 2 }
  git push fork HEAD:eu-first-build
}
