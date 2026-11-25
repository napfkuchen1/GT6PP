Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 5c85812 fix: probe isolates savedata per run (shared save hid first-boot AdjustS; PROGRESS: 2026-11-25 | 5c85812 | vol | ok FAIL - - - - - | probe_a37ps_20261125_121949_2 | non-black=0%
Next step: Test: list at obj+0x2B0 (notify AD4294, copy AD3DFC) cyclic/corrupt and filling heap 017B4C78? Env-gated hook in AD3DFC: walk source list (next=+0, limit 1000). If cyclic/huge: find list insert/erase writers statically; else sample AD4294 rate on tid30 (1FA968/7B51B8) and what tid1 waits for in 6171D0 (post-save black).
Do not repeat: AdjustScreen 'regression' was shared savedata (fixed 5c85812, per-run saves); PPU_PRIO_MAP; heap AB-BA guarded; probe -Frame early-kills before late WD
Still running: nothing; gt6.exe carries uncommitted [A35OOM] log hook (gen 024, bk work/_bk_a35)
Read: STATE.md Arbeit37 lines; eu-boot-log.md Arbeit37
