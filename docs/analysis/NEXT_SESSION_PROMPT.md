Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit fbad759 docs: English-only rule for repo content; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: tid30 '9qstY' = game-loop thread (body via AF0B94 bctrl AF0C28); on the Oracle it runs NetStartDialog/Music/Trophy/Sockets after AutoLoad, on ours it does not. Compare tid30 stack/PC at 60 s via snapshot (snap_walk.py) with the Oracle equivalent: where does it hang/loop (8A7AD0 consumer wait? 616C80 loop?). If it waits in 8A7AD0: check counter 0x1d8/0x240 + tid29 producer 8A88E8; otherwise check tick handler 68FF84 handler table 0x15B242C one by one for return values.
Do not repeat: Save/Term/NP/network_available; forcing main loop 146E8 (before AutoLoad, A15_LOOP ineffective); 798C1C state force.
Still running: nothing
Read: docs/analysis/eu-boot-log.md (Arbeit15 + Arbeit7 wait analysis)
