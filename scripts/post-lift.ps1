# 1.22 post-lift patches (address-relocated). Run after lift-ppu.ps1.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$P = "$env:USERPROFILE\AppData\Local\Programs\Python\Python313\python.exe"
& $P -I tools/ctor_walk_patch.py gt6/generated 0x1183C 0x11880
$env:GT6_SETJMP = "00C61F88"; $env:GT6_LONGJMP = "00C620AC"
& $P -I tools/setjmp_patch_gt6.py gt6/generated
Push-Location tools
& $P -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; import apply_gt6_post_lift as a; print('setjmp guards', a.add_setjmp_guards(Path('../gt6/generated')))"
Pop-Location
# TODO (PORT.md): script hooks, file-device guards, boot-presents hooks, menu pump, host-open wrapper, ADCH switch
