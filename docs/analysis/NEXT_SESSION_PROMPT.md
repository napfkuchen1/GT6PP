Goal: Main menu (C6): boot script task B90 must run l100+ (initNetworkObjects, PDINetwork.initialize, trophy)
State: last commit f5debae docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Poll workaround A27_POLL shows B90 script ends after 4 natives (A6C8A4,809D40,A6C8A4,A6C8A4) and ret=0. Name these natives (grep registration of 809D40 in boot.adc natives table via tools/adch_disasm.py) and find why script exits before l100 initNetworkObjects: check native return values (A6C8A4 = HBool?), VM op after l94. Run: probe.ps1 -Boot notut -Env A22_BLOCK=1;A27_POLL=1;A27_ALLN=1
Do not repeat: 6B7D0C loop tid1-only; 616C80 busy-spin is idle (flags done); do not chase polls: forced poll works but script ends early (STATE Arbeit27)
Still running: nothing
Read: docs/analysis/STATE.md
