Ziel: Hauptmenue (C6), GT6 EU, Game 1.22 + ps3recomp v0.20.0 (einzige Linie).
Stand: lokaler HEAD (nach 01251cd). Savedata-fileBuf kein Overlap mit Flag 0x1796DC8. Snaps 6/8/9/10/15/21/26/40 s: Flag stets 0; Main (tid1) bei 6 s noch in Init-Wait (Task 0x7FFCEE90), ab 8 s Shutdown.
Naechster Schritt: Produzent des Tasks 0x7FFCEE90 (Vtable 0x15C3888/Future 0x15C4360; xref Ctor, Stack A30028<-A7E6CC<-A521CC<-13D94) + warum der Wait bei ~7 s endet: Snap 7 s (PS3_SNAP_AT=7), snap_walk stack 1; tid30 (lr AD4344) null-call-Notify AD4294. Wenn Wait per Timeout/Fehler endet -> Fehlerpfad statt Quit-Flag jagen.
Nicht wiederholen: LEDGER 4, mempool-HLE, AFDFC0/0x1798F00, Quit-Flag-Writer-Suche (Flag nie != 0 in Snaps), Savedata-fileBuf.
Laeuft noch: nichts.
Lesen: STATE.md, NEXT_SESSION_PROMPT.md. Caveman ultra.
