Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 4bc89af fix: movie audio decode (ATRAC3plus), stream time stamps and larger vide; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: I1 0/3, total without check-off 0/6, boxes done 13.
Next step: I1b: movie freezes at picture 199, video ring full. Trace cellAudioGetPortTimestamp/GetPortBlockTag + port 1 read index during work/_a61/movie.sh; clock frozen -> fix cellAudio, else read release condition of frame ring consumer (STATE Next step)
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: A61: freeze cause is not picture PTS 29.97 vs 59.94, not a blocked cellAdec callback (LEDGER §4)
Still running: nothing
Read: STATE.md
