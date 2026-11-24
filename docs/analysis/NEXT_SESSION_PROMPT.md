Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 82b2c05 Arbeit20: update/data audit, override-off refuted; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: Update audit DONE (data complete in rp; override-off refuted). New strategy needed, chain Save/Term locked: (1) snapshot diff ours(rp,en-gb) vs oracle expectations is impossible, so do opendiff+HLE-call-sequence diff (scripts/oracle_seq.py, PS3_HLE_TRACE_ARM) AFTER 9/7N/XG: oracle does 3x AutoLoad2 GAME6 (-4) then sysmodule 0xF044+NpTrophyInit; ours goes straight to sceNp Term. Find what in ours makes Term be chosen (script state after AutoLoad2 result), static xref before any run. (2) Source of save prefix GT6_1 vs GT6 (decrypted PDIPFS/script data) is open.
Do not repeat: override-off (GT6_PFS_OVERRIDE=0) worse; data completeness (rp = full 1.22 tree); VMPageFile/page faults = consequence (Arbeit11)
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail)
