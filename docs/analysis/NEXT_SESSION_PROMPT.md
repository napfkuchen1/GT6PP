Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit d8b9897 docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: Log A2FFCC loop: A2F290 ret + task+0x28 per iter for B90 (script call via A7BA60, tid1); if ret 0/1 while st=2 find why A2F290 skips A4F938 wait (A2F2E0 state==2 branch, +0x64 sched null skips wait at A2F300)
Do not repeat: 68FDB4 chain = list clear + remove_if (B90 not flagged in 683318), not a list builder
Still running: nothing
Read: STATE.md (last 3 lines)
