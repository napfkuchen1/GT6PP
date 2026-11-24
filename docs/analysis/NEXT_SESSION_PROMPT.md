Goal: Main menu (C6): boot script task B90 must run l100+ (initNetworkObjects, PDINetwork.initialize, trophy)
State: last commit ceea71f docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: B90 dies by node-start flush 683318>A1EAD0>A30578 (A2ED74 terminate, st2 ev3) while in timed sleep (A4FBE8); pin of refcount did not help. Find why flush hits B90: read 683318 flush list (node +0x50/54/58), who adds B90 there and when vs script start (A7BA60 create at ~1.1s tid30 6D4938). Probe: -Env A22_BLOCK=1;A28_OP=1 (hooks A28L/A28R/A28P in gen022, A28_NOFLUSH skips A30578 at st1/2)
Do not repeat: A27_POLL polls freed B90 (bogus); A28_NOFLUSH/A28_PIN refuted; 6B7D0C loop tid1-only
Still running: nothing
Read: STATE.md (last 3 lines)
