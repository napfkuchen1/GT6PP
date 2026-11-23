Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: letzter Commit siehe git log. Quit (~30 s) direkt nach "LOAD complete GAME6" (SaveDataUtil.load AUTO -> ProgressDialog.open -> _autoLoad). userdb-Hyp. widerlegt (initUserDB nie erreicht). VM-Task endet dort still.
Naechster Schritt: 1.22-Script-VM-Poll/Handler-Tabelle finden (Hyp.-31-Adressen 9EEA88/9F0748 sind 1.00, 0 Calls), CALLTRACE_FROM darauf mit AFTER=3, letzte Opcodes vor Quit lesen. Wenn letzter Opcode ein Native-Call: Ziel pruefen/HLE fixen; sonst ProgressDialog.open/DialogFrame.appear-Pfad.
Nicht wiederholen: Quit-Flag 0x1796DC8, savedata Rueckgabe, sceNp Term, Task-State 0x28, userdb/abortDiskFull (LEDGER 1.22, STATE).
Laeuft noch: nichts. gt6/generated/ppu_recomp_022/023.cpp tragen [SETST]/[WAITST]/[QCHK]-Diagnose (Backups work/_bk_022, _bk_023); vor Baseline zurueckspielen + build-all.ps1.
Lesen: STATE.md, dieser Prompt.
