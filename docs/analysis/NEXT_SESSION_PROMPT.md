Goal: M1: complete, correct main menu (intro plays, controllable, no gfx/text errors, live run + pad); then M2 first race.
State: last commit a181bdd docs: handover goal M1 definition and checklist; PROGRESS: 2026-11-25 | 4da0de7 | vol | ok ok FAIL FAIL ok FAIL - | probe_a46menu_20261125_191732_1 | non-black=81%
Next step: T1: DE.rt2 read truncated (383244/580744, confirmed). Find size source: log r3/r4 in AAE51C (work/_a47/opensize_hook.patch), vt+0x48 at A01A40; 90 s probe -StopOn rt2read (rt2 log: work/_a47/rt2_probe_and_infohook.patch). Fix -> verify popup text, then G1
Do not repeat: info getter AAC240 hook (0 calls); DB size fixes; fiber stack
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit47
