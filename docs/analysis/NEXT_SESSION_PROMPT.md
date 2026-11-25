Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 3af844d fix: heap lock order guard (B04CD8) and allocation-failure findings; PROGRESS: 2026-11-25 | a080c1b | vol | ok ok FAIL FAIL ok FAIL - | probe_a35wd_20261125_113422_1 | non-black=5%
Next step: Main heap 017B4C78 full or corrupt? (a36ch_2: 12-byte allocs fail on tid30). Static: free-size query B0A3B4/B0A6AC (callers 9FE1EC/9FE274), log free bytes + count AD4294; monotonic growth = leak/queue (tid1 blocked in A0498C), sudden = corruption/garbage size (a36hl_2 161 MB). Then post-SAVE black screen (WD dump).
Do not repeat: PPU_PRIO_MAP (no fix for SettingProject stall); heap AB-BA guarded (tools/guard_heaplock.py); probe.ps1 caps -Parallel at 2
Still running: nothing; gt6.exe carries uncommitted [A35OOM] log hook (gen 024)
Read: STATE.md Arbeit36 lines; eu-boot-log.md Arbeit36
