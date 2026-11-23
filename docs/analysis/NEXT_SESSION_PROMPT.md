Ziel: Hauptmenue (C6), GT6 EU, Game 1.22 + ps3recomp v0.20.0 (einzige Linie).
Stand: Commit 37aac68+. cellFiberPpuContext-HLE (`gt6/src/gt6_ctxfiber.cpp`) + `tools/guard_notify.py` (Guard AD4294) im Baum; Guard-Build `gt6\build\gt6.exe` fertig (17:53, work/build_guard.txt). Noch KEINE Probe damit. C1 FAIL bisher.
Naechster Schritt: `.\scripts\probe.ps1 -Name guard -Boot orig -Seconds 90 -StopOn <Zeile> -Frame 4200`. Wenn Spinner/Null-Call-Sturm weg -> naechsten Blocker analysieren; sonst Ursache Listenkopf=0 (Heap-Ueberlapp 0x7FFFEB70, Allocator-Vtable 0x1637F80 bei AE73BC) per `scripts/snap_walk.py`.
Nicht wiederholen: LEDGER §4, mempool-HLE (kein Writer).
Offen (Ueberwacher): (1) Doku-Reste README/ROADMAP/docs/STATUS/BOOT/HANDOFF/TOOLING auf EU BCES01893 + 1.22, STATE.md-Pfade pruefen; (2) probe.ps1 Stall-Kill: Fortschrittszaehler (neue FS-Opens/HLE-Typen) 30 s, Flip-Heartbeat reicht nicht, FreezeSec>=60, kurze -Seconds (60-90), nach Lauf Get-Process gt6 leer.
Laeuft noch: nichts (Build fertig). Prozess-Check: Get-Process gt6.
Lesen: NEXT_SESSION_PROMPT, STATE.md; LEDGER nur grep. Caveman ultra. Kontext: ctxwatch alle ~15 Calls, Handoff bei 180k.
