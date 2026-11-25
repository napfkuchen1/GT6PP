Goal: Main menu (C6), EU 1.22 data overlay work/gt6_vol_a32 (env GT6_VOL_ROOT + A29_JMP=1, no -Boot).
State: last commit f04215a docs: Arbeit32 handover findings (1.22 overlay boots to presents, boot r; PROGRESS: 2026-11-25 | 4093277 | vol | ok FAIL - - - - - | probe_a32see_20261125_095738_1 | non-black=1%
Next step: Boot race: ABA suspect. Run >=4x (probe -Parallel 2 twice, 100 s) with PPU_RESV_STORE=1 vs default, count stall (HOTREAD 6D2BC0)/too long/purecall. If STORE clearly better: make it default and find non-vm_write writers (SPU DMA, HLE, atomics); else audit ldarx/lwmutex. Also: why savedata loads 3x (boot restarts before/after Presents).
Do not repeat: -Affinity 5 (still stalls); PPU_RESV_OFF (worse); PPU_WWATCH 0x6FFFF610 silent; Arbeit31 guest PFS line dropped.
Still running: nothing
Read: STATE.md (Arbeit32 lines); eu-boot-log.md 'Arbeit32'
