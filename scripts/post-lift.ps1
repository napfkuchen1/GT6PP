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
& $P -I tools/guard_conswait.py gt6/generated/ppu_recomp_018.cpp
& $P -I tools/port_hooks.py gt6/generated
& $P -I tools/guard_ringzero.py gt6/generated
& $P -I tools/guard_heaplock.py gt6/generated
# TODO (PORT.md): script hooks (1.00 9BB020/9BB11C/9BAFE0 -> A67E1C/A67F60/A67DC4 unsure), FileDeviceHost flush guard, boot-presents, menu pump
