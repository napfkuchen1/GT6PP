Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: lokaler Commit nach 688d1d6 (guard_free.py, log_ret.py, Doku). tid30-Spin = Free-Loop AD4334 (Guard in gt6/generated/ppu_recomp_023.cpp, Backup work/_bk_g23); Symptom. Run-Methode 13D90 kehrt normal zurueck (A52140 ret 1), Main wartet in A7E6BC auf Task/Job 0x7FFCEE70, der endet -> Shutdown.
Naechster Schritt: snap_292013437: `snap_walk.py obj 0x7FEEC9D8` (= obj+0x9d8), vslot 0xC (`vt`), Ziel per gdis.py --fn lesen. Wenn Job sofort ret: Bedingungs-Flag per xref.py (Setter+Leser). Wenn nichts: Schwesterport third_party/GT5P/docs/progress.md vergleichen.
Nicht wiederholen: Quit-Flag-Schreibersuche, savedata fileBuf, AD4294-Spin (LEDGER 1.22; Spin = Symptom).
Laeuft noch: nichts. ppu_recomp_023 hat Guards (GT6_NO_NOTIFYGUARD / GT6_NO_FREEGUARD abschaltbar); 022 ist Original.
Lesen: STATE.md, dieser Prompt.
