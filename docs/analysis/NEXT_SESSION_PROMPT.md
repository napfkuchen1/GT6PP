Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: lokaler Commit nach 181402a. tid30-Spin = Symptom (Free-Loop AD4334, Guards in ppu_recomp_023). Run-Methode A52140 kehrt normal (ret 1); Job 0x7FFCEE70 = AD4294-Notify + No-op (obj+0x9d8=0), endet normal -> Main wartet fertig -> Shutdown. Listener = Thread-Obj "processEventLoop" 0x701F80F0.
Naechster Schritt: Wer submitted Job 0x7FFCEE70/Task 0x7FFCEE90 (xref.py --call um 7B5208) und sollte statt dessen ein langlaufender Game-Main-Thread entstehen? ppu_thread_create-Namen loggen (HLE-Log, Env), erwarteten Thread (z.B. Game-Main/processEventLoop) suchen. Wenn fehlend: Erzeuger-Pfad per gdis.py. Alternativ GT5P-Port vergleichen.
Nicht wiederholen: Quit-Flag-Schreibersuche, savedata fileBuf, AD4294-Spin, obj+0x9d8 (LEDGER 1.22).
Laeuft noch: nichts. 023 hat Guards (GT6_NO_NOTIFYGUARD/GT6_NO_FREEGUARD), 022 Original.
Lesen: STATE.md, dieser Prompt.
