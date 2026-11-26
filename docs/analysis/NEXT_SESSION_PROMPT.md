Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 8f22612 fix: deliver cellVdec callbacks on a decoder thread (movie deadlock); PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: I1 1/3, total without check-off 1/6, boxes done 12.
Next step: I1: sh work/_a60/movie.sh with --env VDEC_TRACE=1;DMUX_TRACE=1: count video DecodeAu/GetPicture and find the stall (audio stops at DecodeAu 57); if cellAdec callback blocks, thread it like cellVdec
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: A60: movie lwmutex inversion = sync cellVdec callback, fixed in 8f22612 (patch gt6-a60-vdec-cbthread)
Still running: nothing
Read: STATE.md
