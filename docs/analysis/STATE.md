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
- Alte Callee-Adressen 4037EC28 u.a. aus Hyp. 35 sind lauf-spezifisch/stale; im Snapshot 110 Bind-Wrapper (vt 0x1484968) mit vtable+0x54 = 0x9E5FC0 (Bind-Trampolin -> 0x9880BC).
- Hyp. 37 Snapshot-Auswertung: haengender Script-Opcode 0x06 ruft Wrapper 4037A844 (vt 0x1483EC8+0xdc=9B0918) mit Arg "gtmode" -> 9C625C -> 9C6184 -> OPD 014CD330 = MGOM.start (6C54DC).
- MGOM.start("gtmode") ist nur Queue: manager 7FF01FC4 +0x48=1 (pending), +0x50="gtmode" noch bei 200 s. Der Engine-Consumer von manager+0x48 (-> Projekt-Loader 5FA338) laeuft nicht.
- Nebenspuren, nicht verfolgt: `[mfc] REJECTED malformed transfer` (ea=0x7FFFFFFF, img=19, pc=0xF0C) in ~1/3 Laeufen; blauer Block auf AdjustScreen (M3).
- Hyp. 38 (offline): Consumer = processEventLoop 0x568658 (OPD 014BF800), signalisiert Waiter manager+0x18 (0xA21E04@5689D8). Hauptthread blockt in MGOM.start (568CC8 bl A21D50).
- Kein Thread hat 0x568658 auf dem Stack. Vorhandener Pump (gt6_menu_project_tick) laeuft nur pro Worker-Schleife 0xA12170, Worker schlafen aber in A187CC/lwcond_wait -> Hook feuert nie.
- Signal vor Wait geht nicht verloren (A21D8C setzt +0x29=1) -> synchroner Pump vor 568CC8 im Hauptthread ist zulaessig.

## Naechster Schritt (EINER)
**Hyp. 39: synchroner Pump im Hauptthread.** Vor `bl 0xA21D50` (568CC8, func_00568C94) `func_00568658` bis manager+0x48==0 aufrufen (Limit ~2000, Sleep 1 ms), per apply_gt6_post_lift.py.
Probe: probe.ps1 -Boot notut -Seconds 220; erwarte gtmode-Projektload (5FA338) + Ende des Ladebildschirms. Failt das: Zustand 3/5 im Consumer pruefen.

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
