Goal: Stabilize the main menu (GT Mode home) reached in Arbeit46.
State: last commit 4da0de7 fix: 32 MB host stack for guest context fibers (GT Mode menu renders), A; PROGRESS: 2026-11-25 | 4da0de7 | vol | ok ok FAIL FAIL ok FAIL - | probe_a46menu_20261125_191732_1 | non-black=81%
Next step: Main menu reached (a46menu, work/_a46/main_menu_home.png). Next if requested: fix black tiles + message ID in popup (GT003_GET_FIRST_CAR0), then X on popup -> car dealer; if black tiles persist after 300 s idle, check texture/file loads in the log
Do not repeat: DB size/corrupt fixes (f8ef048, faa32e5), fiber stack (4da0de7)
Still running: nothing
Read: STATE.md; eu-boot-log.md Arbeit46
