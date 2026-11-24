Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20
State: last commit c0ec557 docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Boot task B90 resumes once after load then yields at next wait; find the yield instruction after l94 loadEveryWhereForGame in boot_sequence_common (tools/adch_disasm.py on boot.adc / main.adc SaveDataUtilGT6.ad l797) and who re-ticks that wait type; no more project-update/poll-forcing (A26_UPD, A26_TP refuted).
Do not repeat: A25_POLL; A26_UPD per-frame 6A68C0; A26_TP direct A2ED74; skip-load; HMonitor wake
Still running: nothing
Read: docs/analysis/STATE.md
