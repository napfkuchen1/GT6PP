Goal: Main menu (C6): boot script task B90 must run l100+ (initNetworkObjects, PDINetwork.initialize, trophy)
State: last commit 44cdbb4 docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Forced polls (A27_POLL=1) show B90: poll1 4 natives, polls2-7 no natives, then ended (A2F290 ret 3). Trace VM ops in exec loop A2F0AC (after SET_STATE 2 at boot.adc 0x16D33) to see why script returns instead of calling initNetworkObjects (l102); candidates: op dispatch hitting error/return, wrong VM state resume. Probe: probe.ps1 -Boot notut -Env A22_BLOCK=1;A27_POLL=1;A27_ALLN=1
Do not repeat: 6B7D0C loop tid1-only; 616C80 busy-spin idle; poll problem solved by A27_POLL but script ends early (STATE Arbeit27)
Still running: nothing
Read: docs/analysis/STATE.md
