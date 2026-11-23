Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: lokaler Commit nach 91dab4f (STATE/eu-boot-log Hyp. submit+npterm). sceNp Term = harmloser Wrapper-Cleanup (AF9780), KEIN Exit-Trigger. Job 0x7FFCEE70 = Script-VM-Task (Factory 7A05D8), endet normal -> Main (A52140) faehrt runter. Guards in ppu_recomp_023 (GT6_NO_NOTIFYGUARD/GT6_NO_FREEGUARD); gt6.exe enthaelt noch [RET]-Diagnose -> vor Baseline build-all.ps1.
Naechster Schritt: (1) Probe -Boot orig -Seconds 60 -Env "GT6_NO_NOTIFYGUARD=1;GT6_NO_FREEGUARD=1": Quit auch ohne Guards (~30 s)? Wenn JA: Job-Ende ist nicht der Trigger, Exit kommt aus anderem Pfad (xref Aufrufer 13FFC/14884, 'Mouse End' Aufrufer) ; wenn NEIN: Job muss laenger laufen (tid30 spinnt) -> Spin-Ursache (Kopie-Liste next=0) doch tiefer pruefen. (2) Script-Task 'initialize'/'finalize' (7A0900): welche startet?
Nicht wiederholen: Quit-Flag-Schreiber, savedata fileBuf, AD4294-Spin, obj+0x9d8, sceNpTerm (LEDGER 1.22).
Laeuft noch: nichts.
Lesen: STATE.md, dieser Prompt.
