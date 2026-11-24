Goal: Main menu (C6): boot script task B90 must run l100+ (initNetworkObjects, PDINetwork.initialize, trophy)
State: last commit 2c2805c docs: handover; PROGRESS: 2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
Next step: B90 flush dispose stack known: 683318 flush (MGOM.start tid1) releases temp list after F1AA3C/F1A5D4/F19D4C; check whether those containers copy with rc inc (our recompile bug?) via ww on B90+4 around 683318. Pin/NOFLUSH/POLL combos refuted. Hooks A28_* in gen022/013 (env-gated).
Do not repeat: A27_POLL polls freed B90; A28_NOFLUSH/A28_PIN/combo refuted; 6B7D0C loop tid1-only
Still running: nothing
Read: STATE.md (last 3 lines)
