Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit 7399749 fix: queue RSX user commands, per-wait acquire timeout, cache rejected s; PROGRESS: 2026-11-26 | c3b8665 | vol | ok ok FAIL FAIL ok FAIL - | probe_a51jt_20261126_022701_2 | non-black=81%
Loop: C2 1/3, total without check-off 1/6, boxes done 3.
Next step: Name the draw that hangs the GPU: env D3D12_DRED -> DRED auto breadcrumbs before D3D12CreateDevice in rsx_d3d12_backend.c, report in d3d_check_removed, per-frame draw records. Repro: play.py start --env GCM_PARKTRACE=1; work/_a53/to_home2.sh; work/_a53/dealer.py. Shader loop -> fix FP decompiler, else check draw args.
Tool: scripts/play.py (start/press/wait/shot/status/dump/quit) for menu questions, not timed probes.
Do not repeat: LEDGER A54: car view black = device removed 0x887A0006, not a lost semaphore/user cmd (fixed); debug layer unavailable on this host.
Still running: nothing
Read: STATE.md, LEDGER.md (grep A54)
