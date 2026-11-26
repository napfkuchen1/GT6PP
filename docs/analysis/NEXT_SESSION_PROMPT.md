Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 9878d29 fix: let the on-screen keyboard stub answer with sysutil events so the n
Loop: I2 1/3, sessions 1/4, total without check-off 1/6, boxes done 15.
Next step: G8 first: log per flip in rsx_d3d12_backend.c (render_frame ~l.5647/5980: draws to rt_off 0, s_flush_bb, spu upload) and compare with shown frame; if partial batches are presented: keep one persistent display image. Then work/_a64/to_name.sh to finish name entry (I2).
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: A64: name-entry hang was the OSK stub (fixed 9878d29); pressing cross repeatedly on a stale frame proves nothing
Still running: nothing
Read: STATE.md, side-session note a64-handover.md
