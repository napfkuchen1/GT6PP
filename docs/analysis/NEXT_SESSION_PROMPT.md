Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 1912a14 diag: trace the post-process job inputs and readback misses; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: G6 0/3, total without check-off 0/6, boxes done 12.
Next step: G6d: SPURS image 5 post-process output is white because its input 0x60579000 (480x270, NV3089 from RT 0x022C0000/8192) is white (work/_a57/bloom.png). Dump what d3d12_rt_readback returns for 0x022C0000 at blit time (and the RT pool entry); if the RT itself is white, trace its draws/clears before the blit in an RSX capture; if the RT is right, fix the readback/NV3089 path. Repro work/_a57/repro_in.sh in foreground, then play.py quit.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: LEDGER A57: showroom is not fixed by RT readback/FP regs/NV0039 alone; white SPU output is not accumulation in guest buffers
Still running: nothing
Read: STATE.md, LEDGER.md (grep A57), patches/gt6-a57-spu-fb.patch
