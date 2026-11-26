Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit e1a6f6d fix: keep one host render target per offset and surface format; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: G6 0/3, total without check-off 0/6, boxes done 12.
Next step: I1 (G6d parked): add the unregistered cellDmuxOpenEx/QueryAttr/QueryEsAttr/ResetEs and 5 cellPamf imports (LEDGER grep A58), then a real PAMF demux in libs/codec/cellDmux.c; verify with sh work/_a58/movie.sh. If cellVdec lacks FFmpeg headers: blank-picture decoder as recorded bypass.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: A58: format-keyed RT slots alone do not fix the washed-out showroom (G6d)
Still running: nothing
Read: STATE.md, side-session note arbeit58-handover.md, libs/codec/cellDmux.c
