Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Commit b7975e3+. Quit-Flag 0x1796DC8 nie gesetzt (LEDGER). Main (tid1) wartet bei 6 s in Init auf Job 0x7FFCEE70; Executor tid30 haengt in AD4294 (Listener-Notify, disp 0x7FFBE100) mit Listenknoten next=0 -> Endlos-NULL-read (HOTREAD cia=OPD 16377C0).
Naechster Schritt: Snapshot 6 s (snap_292013437 vorhanden): Liste des Dispatchers 0x7FFBE100 per `snap_walk.py <snap> obj` ablaufen (AD3DFC kopiert nach sp+0x70 im Frame D00CEA90), Knoten mit next=0 finden. Wenn Knoten freigegeben/genullt: PPU_WWATCH (Hits in run.log.err) auf den Knoten, Schreiber/Freigeber suchen (HLE-Writer zuerst ausschliessen). Wenn Liste ok: Guard-Patch AD4294 (next==0 -> abbrechen) und schauen ob Init weiterkommt.
Nicht wiederholen: Quit-Flag-Schreibersuche, savedata fileBuf (LEDGER 1.22).
Laeuft noch: nichts.
Lesen: STATE.md, dieser Prompt.
