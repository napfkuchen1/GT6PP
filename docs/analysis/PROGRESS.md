# GT6PP PROGRESS - checkpoint table. ONLY place for "what is running". Line: only game 1.22 + ps3recomp v0.20.0.
Rule: after each probe batch ONE line (checkpoints.py), never without an evidence run, additions only. Unmeasured runs (no capture) get no line.
Why: state "AdjustScreen + input works" (user, 23.11. early, old line) was lost on switching to 1.22 without being noted.

## Checkpoints (ascending; a run counts up to the first FAIL)
C0 Start: boot.txt ok, unresolved=0, no crash up to 60 s
C1 Image: frame capture at ~60-90 s NOT black (non-black share >5 %)
C2 AdjustScreen: capture shows screen adjust (boot variant `orig`)
C3 Input: PAD_SCRIPT-X is accepted -> scene changes (capture afterwards != C2)
C4 Spinner: GT logo + spinner (known hang)
C5 Movie: open `PDIPFS/59/FI` in FS log (oracle path)
C6 Menu: gtmode main-menu frame
Oracle RPCS3 (game 1.22) reaches C6. Our 1.22 runs: so far all FAIL at C1.

## Run table (newest at bottom; date | commit | boot | C0 C1 C2 C3 C4 C5 C6 | run folder | note)
2026-11-23 | ee62bbc | orig | ok FAIL - - - - - | probe_pump122_20261123_161949_1 | non-black=0%
2026-11-23 | 86302b5 | orig | ok FAIL - - - - - | probe_pump5_20261123_163320_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | FAIL - - - - - - | probe_lax_20261123_163545_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | FAIL - - - - - - | probe_lst_20261123_165151_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | FAIL - - - - - - | probe_ct_20261123_165727_1 | non-black=0% lang=en-gb
2026-11-23 | 86302b5 | orig | ok FAIL - - - - - | probe_ev_20261123_170710_1 | non-black=0% lang=en-gb

2026-11-23 | 3e76e25 | orig | ok FAIL - - - - - | probe_ctxf_20261123_172901_1 | non-black=0% lang=en-gb
2026-11-23 | 3e76e25 | orig | ok FAIL - - - - - | probe_ctxf2_20261123_173240_1 | non-black=0% lang=en-gb
2026-11-23 | c9a73e1 | notut | ok FAIL - - - - - | probe_fdfcap_20261123_200537_1 | non-black=0%
2026-11-23 | 0b8601d | notut | ok FAIL - - - - - | probe_a7snap_20261123_232734_1 | non-black=0%
2026-11-23 | d95be11 | notut | ok FAIL - - - - - | probe_a7base_20261123_233943_1 | non-black=0%
2026-11-23 | d95be11 | notut | ok FAIL - - - - - | probe_a7nowait_20261123_234129_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8hdd_20261123_235046_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8s50_20261123_235312_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8emptyok_20261123_235811_1 | non-black=0%
2026-11-23 | 1e49628 | notut | ok FAIL - - - - - | probe_a8nodata_20261123_235811_1 | non-black=0%
2026-11-24 | 1e49628 | notut | ok FAIL - - - - - | probe_a8cbres_20261124_000147_1 | non-black=0%
2026-11-24 | 5225c7f | notut | ok FAIL - - - - - | probe_a8ct1_20261124_003117_1 | non-black=0%
2026-11-24 | 5225c7f | notut | ok FAIL - - - - - | probe_a8ct2_20261124_003117_1 | non-black=0%
2026-11-24 | 5aa66da | notut | ok FAIL - - - - - | probe_a10_draw_20261124_011603_1 | non-black=0%
2026-11-24 | a579033 | notut | ok FAIL - - - - - | probe_a11_force2_20261124_014036_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_wd_20261124_014439_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n3_20261124_014851_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n6_20261124_014851_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n12_20261124_014851_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n19_20261124_014852_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n15_20261124_015110_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n17_20261124_015110_1 | non-black=0%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n20_20261124_015110_1 | non-black=1%
2026-11-24 | 01a35b2 | notut | ok FAIL - - - - - | probe_a11_n21_20261124_015110_1 | non-black=0%
2026-11-24 | e77a4f5 | notut | ok FAIL - - - - - | probe_a11_a5c_20261124_015532_1 | non-black=0%
2026-11-24 | e77a4f5 | notut | ok FAIL - - - - - | probe_a11_step_20261124_015800_1 | non-black=0%
2026-11-24 | e77a4f5 | notut | ok FAIL - - - - - | probe_a11_nat_20261124_020107_1 | non-black=0%
2026-11-24 | 89fd15f | notut | ok FAIL - - - - - | probe_a11_ret_20261124_020532_1 | non-black=0%
2026-11-24 | 89fd15f | notut | ok FAIL - - - - - | probe_a11_skipfin_20261124_020814_1 | non-black=0%
2026-11-24 | a74a4f6 | notut | ok FAIL - - - - - | probe_a11_rpdata_20261124_021457_1 | non-black=0%
2026-11-24 | a74a4f6 | notut | ok FAIL - - - - - | probe_a11_rplang_20261124_021730_1 | non-black=0% lang=en-gb
2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15net1500_20261124_105550_1 | non-black=0% lang=en-gb
2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15net3000_20261124_105551_1 | non-black=0% lang=en-gb
2026-11-24 | fbad759 | notut | ok FAIL - - - - - | probe_a15loop_20261124_110206_1 | non-black=0% lang=en-gb
2026-11-24 | a7fcfc0 | notut | ok FAIL - - - - - | probe_a22cap_20261124_171454_1 | non-black=1%
2026-11-24 | 94997a5 | notut | ok FAIL - - - - - | probe_a22long_20261124_171742_1 | non-black=1%
2026-11-24 | 94997a5 | notut | ok FAIL - - - - - | probe_a22c1_20261124_172347_1 | non-black=1%
2026-11-24 | 60b588c | notut | ok FAIL - - - - - | probe_a22pad_20261124_174006_1 | non-black=1%
2026-11-24 | bffd68b | notut | ok FAIL - - - - - | probe_a23act_20261124_182010_1 | non-black=1%
2026-11-24 | 321886f | orig | ok FAIL - - - - - | probe_a30font_20261124_233313_1 | non-black=0%
2026-11-25 | 886ec9f | vol | ok ok FAIL FAIL ok FAIL - | probe_a32vol_20261125_093727_1 | non-black=5%
2026-11-25 | 4093277 | vol | ok FAIL - - - - - | probe_a32see_20261125_095738_1 | non-black=1%
2026-11-25 | 61bb488 | vol | ok ok FAIL FAIL ok FAIL - | probe_a34cap_20261125_110401_2 | non-black=5%
2026-11-25 | 2046258 | vol | ok ok FAIL FAIL ok FAIL - | probe_a35cb_20261125_111806_1 | non-black=81%
2026-11-25 | 69db5d6 | vol | ok ok FAIL FAIL ok FAIL - | probe_a35pad_20261125_112132_2 | non-black=71%
2026-11-25 | 69db5d6 | vol | ok FAIL - - - - - | probe_a35pad3_20261125_112834_2 | non-black=0%
2026-11-25 | a080c1b | vol | ok ok FAIL FAIL ok FAIL - | probe_a35wd_20261125_113422_1 | non-black=5%
2026-11-25 | 5c85812 | vol | ok ok FAIL FAIL ok FAIL - | probe_a37sv_20261125_121629_1 | non-black=5%
2026-11-25 | 5c85812 | vol | ok FAIL - - - - - | probe_a37sv_20261125_121629_2 | non-black=0%
