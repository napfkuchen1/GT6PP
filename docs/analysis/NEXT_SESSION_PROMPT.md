Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 71dad47 fix: execute NV0039 buffer copies bound to subchannel 1; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: G6 0/3, total without check-off 0/6, boxes done 11.
Next step: G6c: find who consumes main 0x602A0000/0x60579000 and who writes 0xC36C0000 / exposure LUT 0x04BC0C00: trace SPU DMA on these addresses (third_party/ps3recomp-v020/docs/DIAGNOSTICS.md); if no SPU access, dump --snap and search guest pointers. Repro work/_a57/repro.sh in foreground, then play.py quit. Also recheck Home screen with A57 patches.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: LEDGER A57: RT readback, FP regs 64 and NV0039 copies do not make the showroom visible
Still running: nothing
Read: STATE.md, LEDGER.md (grep A57)
