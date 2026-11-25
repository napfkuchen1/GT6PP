Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit f93bf65 debug: env-gated backtrace for large DB reads; SPECDB key path found (Fi; PROGRESS: 2026-11-25 | 58d9306 | vol | ok ok FAIL FAIL ok FAIL - | probe_a42full_20261125_153650_1 | non-black=71%
Next step: gdis AAF720-AAF774 (reader of FileObject+0x9C) + callers: find guest DB decrypt routine; apply it to override-served bytes when file+0x9C != 0 (stubs.cpp stream read override, keep p4 cache fill). 90 s probe GT6_A42SQL=1: expect [A42N] page1 'SQLite format 3', no rc=26
Do not repeat: stream+0x48 filter defer; GT6_NO_CACHEFILL=1 (pager gives zeros); size at FileObject+0xC8
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit43
