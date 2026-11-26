Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 5abcdf3 fix: sample sub-ranges of linear render targets through region views; fi; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: G6 0/3, total without check-off 0/6, boxes done 9.
Next step: G6b: RT readback for NV3089. In nv3089_blit (libs/video/cellGcmSys.c ~1479): local source inside a D3D12 offscreen RT (0x01F00000) -> flush batch without present, copy region to guest memory as A,R,G,B, then blit. Verify with work/_a56/repro.sh (car visible?). If flush breaks frames, read back at batch end. FP 0x04D0BC01 compile fail (G5) may matter.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: LEDGER A56: sub-range RT views alone do not make the showroom visible
Still running: nothing
Read: STATE.md, LEDGER.md (grep A56)
