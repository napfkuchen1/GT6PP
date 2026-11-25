Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 717ae2d docs: handover ledger and progress; PROGRESS: 2026-11-25 | 717ae2d | vol | ok FAIL - - - - - | probe_a38list_20261125_123210_2 | non-black=0%
Next step: Log buffer size at CB3BB4 (env-gated: r3, r29, *(r31+0x20)) and find the SPU job image doing the 16 KB DMA at ea 6FFFE8F0 (SPU_DMA_RANGE=6FFFE920-6FFFE980). Block < 16 KB: fix size/count source; else check use-after-free of that block.
Do not repeat: List-corrupt hypothesis is confirmed (a38); not audio port, not pfs override (A38OV saw no hit on list); corruption hits ~1 of 6-10 runs, StopOn A38LIST.*bad=1
Still running: nothing; gt6.exe carries env-gated hooks GT6_A38LIST/GT6_A38DUMP (gen 023, bk work/_bk_a38) and [A35OOM] (gen 024)
Read: STATE.md Arbeit38 lines; eu-boot-log.md Arbeit38
