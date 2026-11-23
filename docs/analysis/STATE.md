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
- Plan B Pad-Replay: PAD_LOG=<pfad> (patches/gt6-v020-padlog.patch, build-v020 neu gebaut, getestet) + scripts/live-padlog.ps1: user spielt live, Log -> PAD_SCRIPT-Replay.
- SDK-Update ps3recomp v0.19 -> v0.20.0 (Klon third_party/ps3recomp-v020, lokale Patches gemergt, Build gt6\build-v020): Baseline noadj 220s/Frame 4200 identisch (GT-Logo+Spinner), Fortschritt gleich; Flips ~3x weniger (Pacing). Backend-Vergleich Vulkan vs D3D12 offen (PS3RECOMP_RSX_VULKAN + rsx_vulkan_backend_init). Alt-SDK third_party/ps3recomp bleibt unveraendert.
- Vulkan-Probe (build-v020-vk, GT6_BACKEND=vulkan, patches/gt6-v020-vulkan-win-now.patch): Init OK (RTX 2080), aber nur vtable-Pfad, glslang fehlt -> keine Gast-Shader; Capture (Frame-Zaehler) D3D12-only. Kein Menue-Vergleich moeglich; ohne glslang-Build zurueckgestellt.

- Hyp. 59: Pressure-Bytes OK (cellPad.c setzt 255 bei Digital-Bit, PRESS_ON, len 0x18). Pad-Datenpfad bis Padobj verifiziert; Konsument im AdjustScreen unbekannt.
- Hyp. 60: Per-Frame-Walker A1C1F8 ruft je Frame 8B2C28 (2x, leere Listener-Liste), A3B384, A39CD8 (Pad), A2CD98, A2ADA8, 1138C, 1136C. Kein UI-Pad-Leser unter den Callbacks.
- Hyp. 61: orig ohne Pad: Frame 10500/13000/18000 in 300/330/420 s NICHT erreicht (9000 war ~162 s) = Flip-Rate bricht nach ~9000 ein oder Stall. Zeitpunkt unklar.
- Hyp. 62: Frame 9000 ~159 s reproduzierbar, 9600 in 260 s NICHT. Spiellogik tickt weiter (padcnt GetData #15000 @300 s ~50/s) = RSX-Render-Frames stagnieren, kein Gesamt-Stall.
- Hyp. 63: WD 120/200 s (probe_h63b): Haupt-tid 1 steht in lwcond_wait (func_00A21CBC<-A21D50<-568C94+0x38, cond 0x7FEAC030/obj 0x7FEAC018), gleiche Stelle bei 120+200 s = Hauptthread blockt auf Worker/Job. Wer signalt?
- Hyp. 64: Wait=A21D50 (Event obj 0x7FEAC018: +0x28 wait=1, +0x29 signaled=0, auch im Snapshot h55), Signal=A21D8C (7 Aufrufer: 6BFDE0,7D8124,7FD0AC/D4,A350D0). Owner 0x7FEAC000 vt 145FC88. Aufrufer 6C5478<-6C54DC<-9C6184 (Script-VM). Signal kommt nie.
- probe.ps1: -FreezeSec (45) bricht stilles Log ab (FROZEN@s in boot.txt, getestet via Suspend), -Seconds 0 = Skript+60/220, END-Zeile RUN DONE|FROZEN|TIMEOUT. Separate userdb/Lauf offen (hdd0 fest in main.cpp:722).

## Naechster Schritt (EINER)
**Hyp. 65:** Wer haette 0x7FEAC018 signalen muessen? Signal-Aufrufer (6BFDE0 etc.) per xref/gdis einordnen, Worker-tids (WD: tid 27/32) pruefen; Flag +0x48 Setter 6C0A14.

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
