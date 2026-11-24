# Lessons from GT5P (sister port, same PDI engine)
Source: third_party/GT5P/docs/progress.md (phases 12-16). Facts only from there; "(assumption)" = not proven.

## Per phase: symptom -> cause -> evidence
- P16 (ps3recomp master): freelist damage + 4/7/108 asset scatter gone after re-lift. Which upstream fix did it: NOT proven. Check: `bash scripts/soak.sh 8 40`.
- P16 main hangs: `li r11,0x6B` = syscall 107 sys_cond_wait, timeout 0, nobody signals. Which cond / who signals: open (assumption: same class as P11).
- P15 longjmp: lifter turns `blr` in longjmp (func_00A0A57C) into `return;` -> control lands in the caller instead of the setjmp site -> LZ decoder loop runs 4 MB past the window.
  Fix: `scripts/setjmp_patch.py` (host setjmp per site, buffer stack). Re-apply after EVERY re-lift. Effect: assets 4 -> 108/7.
- P15 find site: `scripts/bbcount.py` (counter on every label of a function) -> hot loop 49.8 M hits; registers change without a writer in the loop => a call was the cause.
- P14 switch: find_functions only follows direct branches; `bctr` over jump table (246 tables, 1710 targets) stayed unlifted. Table sits behind bctr, entries = signed 32-bit offsets.
  Consequence: 4.4 M busy spins on queue 0 disappeared. Check: "unresolved indirect" = 0.
- P13 command line: argv is an array of 64-bit pointers (CRT reads stride 8, writes 4). `boot_from=gamedata` needed (bdvd looks for USRDIR/GT.VOL). argv[0] = "/dev_bdvd/PS3_GAME/USRDIR/EMAIN.SELF".
  Relative path `PDIPFS/K/4D` needs cellFs mapping. Afterwards PDIPFS mounted, sys_cond_signal 0 -> 36 per boot.
- P12 script: boot end calls `scripts/gt5p/Application` (lives in PDIPFS). Without mount: no attract object, no frame loop. `scripts/rtti.py`: 1442 vtables, 8314 virtuals (binary has RTTI).
- P12 idle deadlock: main in sys_cond_wait; worker loop func_00935690 waits on sys_event_queue_receive (queue 5: 1901 receives, 0 events); sys_cond_signal 0x called.
  Finding: no sender for queue 5 exists, because the code that creates it (PDIPFS mount/script) never ran.
- HLE writer: `cellDiscGameGetBootDiscInfo` declared with 3 instead of 1 parameter -> wrote "BLES00000" into OPD table (r4). Random crashes -> 6/6 clean boots after fix (ps3recomp#109).
- HLE writer 2: `VM_HLE_INJECT_BASE` (GCM labels/offset tables, 0x8000 B) lay on game heap 0x20000000 -> allocator size-class table overwritten with 0xFFFF -> livelock (ps3recomp#104).
  Finding: host stores do not see LBP_WW. `GT5P_CANARY=<addr>:<expected>` + `GT5P_CANARY_ARM=<call#>[:<page>]` (page guard) bracketed 0x20003000..0x20007000.
- Heap/OOM: alloc 264 B fails (calls=2155 zero=2000), freelist node +4 read as size = false conclusion; `[flcheck]` bad chains; cause was the runtime writer, not func_006A4400.
- Audit: `scripts/audit_cmp.py` (signedness/width/CR field per compare), `scripts/audit_branch.py` (branch decoding). Both green => lifter suspicion ruled out.

## Test rules for GT6
a) Idle deadlock: name the waiter (cond/queue ID, syscall no.), then find the sender: who posts this queue / calls sys_cond_signal? Counter per queue: receives vs. events.
   Never fake the wait (FLOW_CONDKICK) as a fix. Missing sender = upstream code did not run.
b) Game = script: are PDIPFS mount and script load (e.g. Application script) really called? Count the call first, then interpret follow-up symptoms.
c) Rule out runtime HLE writers first: argument count of each HLE stub vs. SDK; HLE base (VM_HLE_INJECT_BASE) vs. guest heap mappings; canary + page guard, LBP_WW is host-blind.
d) Lifter: setjmp/longjmp (`scripts/setjmp_patch.py`) and switch/bctr tables: guest libc longjmp present? Jump-table targets lifted? Unresolved-indirect counter = 0?
e) Per conclusion ONE command that refutes it (bbcount, audit_*, soak.sh, canary); without a run mark it as "hypothesis". Structural readings were often wrong, measurements rarely.
