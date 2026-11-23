Arbeite im Haupt-Checkout (Branch eu-first-build). Lies CLAUDE.md und docs/analysis/STATE.md.
Stand: user sieht im laufenden gt6.exe nach dem ersten Testrace das Menue (unvollstaendig/fehlerhaft). Probe-Captures zeigen nur: noadj 4200/9000 = dunkles Logo+Spinner; orig 4200/6000 = AdjustScreen mit Blaurechteck (Render-Bug), Pad-Presses (CROSS) wirkungslos.
Offen: (1) Hyp. 49 Blaurechteck: Ops fp 0F8FFD41 vs=4 (probe_h48origpad_20261123_011048_1/frame_00/manifest.txt) -> Vertex/VS-Konstanten pruefen; SCREEN_AS_TEX ist NICHT die Ursache. (2) user fragen/ableiten, wie er Dialoge+Testrace passiert (run-gt6.ps1 mit echtem Pad?), dann diesen Weg per probe.ps1 nachbilden und Frame-Capture des Menues machen. (3) Definieren "Menue sichtbar/fehlerfrei".
Hinweis: probe.ps1 scheitert mit Move-Item-Lock, wenn ein fremdes gt6.exe laeuft (user/andere Session) - nicht killen, warten.
Update: Blaurechteck in v0.20 (build-v020) behoben; Arbeits-Build ist build-v020 (GT6_BUILD_DIR setzen). Naechstes: Hyp. 50 siehe STATE.md.
Update 2: Hyp. 50/51 siehe STATE.md. Pad-Script feuert, AdjustScreen reagiert nicht; einziger Pad-Reader A39F00. Naechstes: Hyp. 52 (Snapshot des Pad-Managers, Antwort der Peer-Session zu users Dialog-Weg beachten).

Update 3: Hyp. 52 statisch fertig, siehe STATE.md. Naechstes: Hyp. 55 Snapshot-Check (PS3_SNAP_DIR explizit setzen).

Update 4 (Hyp. 56-59): A395F0 (padobj vt+8) wird jeden Frame nur vom Combo-Checker func_00811370 gerufen; padobj vt+0/+4/+C, Listener-Objekt 0x165F340 (vt 148A250) nie. Poll A39CD8 laeuft (Aufrufer A1C1F8, tid 27). Pad-Datenpfad bis Padobj OK, UI-Konsument im AdjustScreen unbekannt. PS3_CALLTRACE_AFTER ist in Sekunden (<Lauf-Dauer!). Naechster Schritt: STATE.md Hyp. 60.

## Update 5 (Hyp. 60-65, 2026-11-23)
- Hyp. 60: Per-Frame-Walker A1C1F8 (tid 27) ruft nur Pad-Poll A39CD8, A3B384 (Pad-Slot-Tabelle 0x165F1AC), A2CD98, A2ADA8, 8B2C28 (leer). Kein UI-Pad-Leser.
- Hyp. 61/62: RSX-Capture-Frame (RSX_CAP, -Frame) stagniert nach ~9000 (~159 s); Spiellogik tickt weiter (padcnt ~50/s). -Frame ueberschreibt RSX_CAP-Env.
- Hyp. 63 (KERN): WD-Dump (PS3_WD_AT=120,200) zeigt Haupt-tid 1 in lwcond_wait: Event 0x7FEAC018 (Wait A21D50, Signal A21D8C), Aufrufkette 568C94<-6C5478<-6C54DC<-9C6184<-9C625C<-9B0918<-9F0748 (Script-VM). Snapshot h55: signaled-Byte +0x29 = 0, wait-Byte +0x28 = 1. Hauptthread blockt dauerhaft -> UI/Pad ohne Wirkung erklaert.
- Hyp. 65 (naechster Schritt): Wer signalt 0x7FEAC018? Signal-Aufrufer 6BFDE0, 7D8124, 7FD0AC/D4, A350D0 (generisches Event-Send mit Wert +0x40/+0x44), A21DE4/E20. Worker-tid finden (WD tid-Liste), pruefen ob dessen Thread/Job nie laeuft (z.B. fehlendes SPU/Fiber/Callback-Ergebnis, Setter +0x48 bei 6C0A14).
