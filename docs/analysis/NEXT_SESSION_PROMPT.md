Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit b3fd79e Arbeit19: consumer-wait finding was artifact, game loop runs inline on m; PROGRESS: 2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
Next step: PDIPFS dup/install divergence: Oracle reads K/4D then installed PDIPFS/9/H4/MS (1.22 patch tree, boots from hdd0 EMAIN.SELF); ours reads K/4D then K/R2 and runs fdup disc->hdd0 loop (174 fdup files). Decode who picks the 9/ bucket from K/4D (index decrypt; ABC52C/B003EC are fdup cleanup/stat helpers, callers via ABB8C8 bdmark area). Check where ours hdd0 PDIPFS/K came from vs Oracle (does Oracle K/4D equal ours?). If 9/ tree is patch data: find how 1.22 update content is installed (TPPS-01.07), try Hdd0Src with it.
Do not repeat: consumer-wait 8A7AD0 / 8A88E8 chain (artifact); sys_memory log check (our runs log no [sys_memory])
Still running: nothing
Read: docs/analysis/eu-boot-log.md (tail: Arbeit19)
