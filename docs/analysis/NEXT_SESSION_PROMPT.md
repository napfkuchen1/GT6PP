Goal: Main menu (C6), EU 1.22 + ps3recomp v0.20.
State: last commit 99352d0 fix: probe.ps1 derives -Frame from RSX_CAP so captures are not dropped b; PROGRESS: 2026-11-25 | 58d9306 | vol | ok ok FAIL FAIL ok FAIL - | probe_a42full_20261125_153650_1 | non-black=71%
Next step: Find the missing SPECDB decrypt: DB0106 reaches SQLite raw (rc=26 NOTADB). Disassemble loader 0x59F4A0/0x5A2928 and SQLite VFS xRead; compare full-read buffer with [A42N] page1. If a flag/size from our host open skips decrypt, fix that; if SPU/crypto job, trace it
Do not repeat: stream+0x48 filter defer refuted (DB0106 has none, boot stalls); size at FileObject+0xC8; toInt site (confirmed getGTModeFirstCarPP l376)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit42
