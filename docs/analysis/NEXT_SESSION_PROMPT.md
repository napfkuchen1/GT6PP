Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 886ec9f docs: handover; Arbeit32 running: 1.22 tree extracted by disc owner to work/gt6_vol_122+ (boot.adc 158255 B, scripts/gt6/main.adc 988307 B, sha256 1CE3993C...A69B).
Next step: Overlay 1.22 tree on a COPY of work/gt6_vol (hardlinks/junctions; never modify gt6_vol or gt6_vol_122+), GT6_VOL_ROOT=copy, boot via probe.ps1 without 1.00 boot.adc patches. If no MMuseum2 NameError -> follow next blocker to menu; if route fails -> guest PFS deadlock line (STATE Arbeit30).
Do not repeat: never run GTToolsSharp/PDTools; 1.00 scripts mismatch 1.22 ELF; A22 Save/Term/NP/Quit chains refuted
Still running: nothing
Read: STATE.md (Arbeit29/30 lines at end)
