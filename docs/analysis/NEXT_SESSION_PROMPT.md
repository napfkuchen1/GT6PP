Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 0fdffa6 Arbeit20: save-prefix rename test, F044 chain retrace; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Static first: xref callers of B40A28 (B3571C,B40B4C,B40C4C,B41750), decide terminate vs per-frame update; then ONE run PS3_CALLTRACE_TO=B40A28 PS3_CALLTRACE_AFTER=200 with rp+en-gb+saves. Oracle polls IsLoaded(0x38) 1857x, ours 1x. Chains F044/isOnline/Save-prefix already closed (eu-boot-log Arbeit20 lines).
Do not repeat: override-off; save rename GT6_1 (-3); F044/isOnline chain; 89C8C0 is progress loader
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail)
