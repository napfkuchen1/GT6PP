# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-22 abends. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`.
Regeln/Fallen: `CLAUDE.md`. Voller Verlauf Hyp. 1-35 mit allen Messwerten: `docs/analysis/STATE_full_2026-11-22.md` (nur nachschlagen). Details: `eu-boot-log.md`.
**Pflege:** je Erkenntnis EINE Zeile in "Aktive Kette" oder "Erledigt" + "Naechster Schritt" aendern. Zeilen <=200 Zeichen. Messwerte nach `eu-boot-log.md`.

## Ziel / Problem
Hauptmenue (gtmode) erreichen. Erststart-Dialoge (Sprache, AdjustScreen, Tutorial) sind per `boot.adc`-Gates umgehbar (Hyp. 15, `scripts/patch-boot-adc.py`). Danach bleibt der Ladebildschirm (GT-Logo + Spinner) ewig stehen.

## Baseline-Varianten (probe.ps1 `-Boot`)
`orig` = Original (Dialog haengt) | `noadj` = Dialog+Adjust uebersprungen, Tutorial-Rennen laeuft | `notut` = alles uebersprungen -> gtmode laedt, 27-Track-Schleife.
Beide Varianten haengen an derselben Ursache (Hyp. 29). Extrahierter Baum `work/gt6_vol` ist gepatcht; Originale in `work/ARCHIV/boot.adc.*`.
Standardlauf: `scripts\probe.ps1 -Name x -Boot notut -Seconds 320 -Parallel 2`. Boot bis Ladebildschirm ~100-150 s; Steady-State ab ~150 s.
Binary: `gt6\build-clangcl\gt6.exe`. Rebuild ~2 min.

## Aktive Kette (Ladebildschirm haengt)
Hauptloop 0x568800-0x568858 tickt 3 Sequenz-Objekte (r28+0x1d4) und wartet auf +0x91 (Fertig). Das kommt nie: Task wird gecancelt (Job-Vektor leer, Hyp. 24-28).
Task-Poll 0x9EEA88 = Script-VM (Opcodes laufen). Script endet nicht: Opcode 0x06 ruft per callee.vtable+0xdc einen Child-Job, Status bleibt 4 (pending), Poll wiederholt (Hyp. 31-35).
Pending kommt nur vom Wrapper 0x9B89D8 (vt 0x1484968) -> `[callee+0x14].vtable+0x54`. Callees: 4037EC28, 4049AE20/AE80/AF28/AF10, 403AD8E0. Hang-ip 403A6628 noch nicht erfasst.
Offene Frage: worauf wartet die Methode vtable+0x54 (Thread? SPU? Datei? Timer?) und wer soll sie fertig setzen.

## Erledigt / widerlegt (Einzeiler)
- Pad/Dialog-Kette (Hyp. 1-14): Maus, Analog, Xbox-Pad, Vektor-Leser, Queues, Timer, LEN-Konstanten, mempool, Fokus-Setter, Event-Dispatch: alles ohne Wirkung. Durch Umgehung (15) hinfaellig.
- RPCS3 `--no-gui` als Orakel: haengt im Shader-Precompile. Manueller GUI-Lauf waere moeglich (User).
- Race/Determinismus: 17/18 Boots identisch. Sound-Schleife = Symptom, nicht Ursache (Hyp. 19/20: 7E90F0 failen, Boot endet gleich).
- WaitFlag/Fiber-Idle, lwcond-Livelock (Hyp. 21-23): normales Worker-Verhalten, Hauptthread dreht in Track-Preload-Tick.
- SPU: 0 dispatch-MISS, 0 unresolved NID in den Hyp.-29-35-Laeufen -> kein fehlendes SPU-Image.
- Hyp. 36 Snapshot-Werkzeug (patches/gt6-snap-at.patch, scripts/snap_walk.py): geht. Workers alle in lwcond_wait, 0 Mutex-Owner, 0 Sem-Waiter, kein cancelled evq. Details eu-boot-log.md.
- Hyp. 37 Snapshot-Auswertung: haengender Script-Opcode 0x06 ruft Wrapper 4037A844 (vt 0x1483EC8+0xdc=9B0918) mit Arg "gtmode" -> 9C625C -> 9C6184 -> OPD 014CD330 = MGOM.start (6C54DC).
- MGOM.start("gtmode") ist nur Queue: manager 7FF01FC4 +0x48=1 (pending), +0x50="gtmode" noch bei 200 s. Der Engine-Consumer von manager+0x48 (-> Projekt-Loader 5FA338) laeuft nicht.
- Hyp. 38-40: Consumer processEventLoop 0x568658; Worker-Hook feuert nie. Sync-Pump (stubs.cpp, vor 568CC8) laedt gtmode (State 1->3->4), 3 Sequenz-Objekte (vt 145FAD8) ticken ohne +0x91.
- Hyp. 41: Fertig kommt aus A13644 = Byte 0x164AB90 (Objekt 164AB80+0x10, Setter C3FE14 nur per vtable+0xC). Flag forcieren (GT6_FORCE_LOADFLAG=1, probe_flag41): Projekte enden, Boot geht weiter.
- Hyp. 42: NULL-Crash in A21D50 war r29=0 durch pending g_trampoline_fn nach dem Sync-Pump (Tick drainte nicht). Fix in gt6_menu_project_tick (stubs.cpp). Rueckweg MGOM.start laeuft.
- Hyp. 42: danach exit(-1) aus 7F9520 (lr 7F9588): A13644-Flag gesetzt -> Zeitstempel +0x960, nach ~0x97FDF Ticks exit. 0x164AB90 ist ein QUIT/Abbruch-Flag, KEIN Load-Done. Force-Flag = Sackgasse.
- Hyp. 43: +0x91 setzt nur Finalizer 5C3EC4 (aus 5C406C bei +0x90, oder Shutdown 5FBAF0 Schleife). Das ist Quit-Pfad: 568800-Schleife ist die Haupt-Game-Loop, kein 'Warten auf Fertig'.

## Naechster Schritt (EINER)
**Hyp. 44: Was tut die Game-Loop pro Tick (5C406C State-Handler +0x88)?** Warum kein Menue-Frame: State-Handler der 3 Objekte + Render/Flip-Aufrufe (cellGcmSetFlip) im Tick zaehlen (loganalyze), Snapshot +0x88 pro Objekt lesen.

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
