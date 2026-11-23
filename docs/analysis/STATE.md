# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-23. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`.
Regeln/Fallen: `CLAUDE.md`. Voller Verlauf Hyp. 1-35: `docs/analysis/STATE_full_2026-11-22.md`. Details/Messwerte: `eu-boot-log.md`.
**Pflege:** je Erkenntnis EINE Zeile in "Aktive Kette" oder "Erledigt" + "Naechster Schritt" aendern. Zeilen <=200 Zeichen.

## Ziel / Problem
Hauptmenue (gtmode) erreichen. Erststart-Dialoge sind per `boot.adc`-Gates umgehbar (Hyp. 15, `scripts/patch-boot-adc.py`).
user sieht im laufenden gt6.exe das Menue nach dem ersten Testrace, aber unvollstaendig/fehlerhaft -> "Haengt" evtl. falsch.

## Baseline-Varianten (probe.ps1 `-Boot`)
`orig` = Original | `noadj` = Dialog+Adjust uebersprungen, Tutorial-Rennen laeuft | `notut` = alles uebersprungen, 27-Track-Schleife.
Varianten aendern `work/gt6_vol/.../boot.adc` -> NIE parallel starten. Originale in `work/ARCHIV/boot.adc.*`.
Standard: `scripts\probe.ps1 -Name x -Boot notut -Seconds 320`. Frame-Capture: `-Frame N` (Frame 4200 ~320-420 s).
Binary: `gt6\build-clangcl\gt6.exe`. Rebuild ~2 min.

## Aktive Kette
Hauptloop 0x568800 = Game-Loop (kein Warten auf Fertig, Hyp. 43). Script-VM (Poll 0x9EEA88) ruft MGOM.start("gtmode"), gtmode laedt, BGM-Playlist laeuft.
Capture Frame 4200: orig = AdjustScreen-Dialog mit Render-Bug (grosses blaues Rechteck oben rechts, Ecken fehlen). noadj = nur dunkles GT-Logo + Spinner (black 99,5 %).
Offen: wann erscheint das Menue (Frame 6000/9000?), was fehlt darin.

## Erledigt / widerlegt (Einzeiler)
- Pad/Dialog-Kette (Hyp. 1-14): alles ohne Wirkung, durch Umgehung (15) hinfaellig. RPCS3 `--no-gui` als Orakel tot (Shader-Precompile).
- Race/Determinismus: 17/18 Boots identisch. Hyp. 21-23: WaitFlag/lwcond-Livelock = normal. SPU: 0 dispatch-MISS, 0 unresolved NID.
- Hyp. 36-37 Snapshot-Werkzeug (patches/gt6-snap-at.patch, scripts/snap_walk.py): Script-Opcode 0x06 -> MGOM.start("gtmode") (6C54DC).
- Hyp. 38-40: Consumer processEventLoop 0x568658; Sync-Pump (stubs.cpp) laedt gtmode. 3 Sequenz-Objekte (vt 145FAD8) ticken.
- Hyp. 41/42: Byte 0x164AB90 = QUIT-Flag, kein Load-Done; Force-Flag = Sackgasse. NULL-Crash A21D50 gefixt (gt6_menu_project_tick).
- Hyp. 43: +0x91 setzt nur Finalizer 5C3EC4 (Quit-Pfad). Hyp. 44: Pump-Limit weg, ~2193 Flips/320 s, Bild Legal/Logo.
- Hyp. 45/46 FIX (patches/gt6-h46-spurs-jc-gen.patch, cellSpurs.c): SPURS-Chain gen+alive, Shutdown stoppt Walker, Join wartet. q4 Pushes 226 -> 187k.
- Hyp. 47: 27-Track-Schleife = BGM-Playlist (soc-job = Audio-Decode), Symptom. Frame 1500 notut = Legal+Logo+Spinner.
- Hyp. 48a: Captures: noadj 4200+9000 = dunkles Logo+Spinner, orig 4200+6000(+CROSS-Pad) = AdjustScreen, Pad bleibt wirkungslos. orig erreicht Frame 9000 nicht in 600 s.
- Hyp. 48c: AdjustScreen-Blaurechteck = obere rechte Quadrant 480-912x27-270 (960er Bild), Farbe wie Ecken-Marker. SCREEN_AS_TEX=0 (probe_h49nosct) aendert nichts -> Screen-Copy-Hijack widerlegt.
- Hyp. 49: v0.20-SDK (build-v020, orig 4200, probe_h49v020orig) rendert AdjustScreen FEHLERFREI (4 Eck-Marker, Pfeile, kein Blaurechteck) = Render-Bug war SDK-Backend, in v0.20 behoben.
- Hyp. 50 (wiederholt h52pad, gueltig): Presses 75-115 s UP/DOWN/CROSS, Capture Frame 9000 bei ~162 s = weiter AdjustScreen, Marker unbewegt. Pad feuert, Screen reagiert nicht. userdb irrelevant.
- Hyp. 51: einziger Guest-Aufrufer cellPadGetData = A39F00 (Pad-Manager, Poll-Funktion ab ~A39EE0, Puffer r21+0xa0+port*0x84). Validitaetscheck button[1]>>4==7 passt (Runtime setzt 0x70|len/2).
- SDK-Update ps3recomp v0.19 -> v0.20.0 (Klon third_party/ps3recomp-v020, lokale Patches gemergt, Build gt6\build-v020): Baseline noadj 220s/Frame 4200 identisch (GT-Logo+Spinner), Fortschritt gleich; Flips ~3x weniger (Pacing). Backend-Vergleich Vulkan vs D3D12 offen (PS3RECOMP_RSX_VULKAN + rsx_vulkan_backend_init). Alt-SDK third_party/ps3recomp bleibt unveraendert.
- Vulkan-Probe (build-v020-vk, GT6_BACKEND=vulkan, patches/gt6-v020-vulkan-win-now.patch): Init OK (RTX 2080), aber nur vtable-Pfad, glslang fehlt -> keine Gast-Shader; Capture (Frame-Zaehler) D3D12-only. Kein Menue-Vergleich moeglich; ohne glslang-Build zurueckgestellt.

## Naechster Schritt (EINER)
**Hyp. 52:** Wer verarbeitet Pad-Puffer r22+8/+0xa (DIGITAL1/2) nach A39F70 -> A3A004? Statisch (gdis/xref) Folge der Pad-Manager-Ausgabe bis AdjustScreen-Handler; Snapshot nur falls noetig.

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
