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

- probe.ps1: -FreezeSec (45) bricht stilles Log ab (FROZEN@s in boot.txt, getestet via Suspend), -Seconds 0 = Skript+60/220, END-Zeile RUN DONE|FROZEN|TIMEOUT. Separate hdd0-Kopie/Lauf (GT6_HDD0, main.cpp, build-v020 neu): -Parallel ohne Lock, getestet 2x.


- Hyp. 59-64: Pad-Pfad ok; Frames stagnieren ab ~9000 (162 s); tid 1 haengt in Event-Wait 568C94->A21D50 (obj 0x7FEAC018), Signal A21D8C kommt nie. Details: work/ARCHIV/STATE_pre_h69_2026-11-23.md.

- Hyp. 65-70: tid 1 Dauer-Haenger. Servicer 568A0C (thunk -> 568658, Zustand obj+0x48 1>2>3>4>5>6) laeuft als FIBER (A14824: CreateFiber A2FC54, Entry A2F464); PS3_FIBERLOG=1 (patches/gt6-v020-fiberlog.patch).
- Hyp. 71/72: gt6_cellFiberPpuWaitFlag (stubs.cpp) yieldet READY, gibt nach 2 ms auf -> RunFibers (A2FAD0) kehrt nie zurueck. GT6_REALFLAG=1 (SDK WaitFlagEx) -> A2FAD0 wiederholt, tid 1 haengt trotzdem.
- Hyp. 73/74/75: Servicer ruft 7FEAC000 wiederholt; Snapshot(REALFLAG,100s): obj+0x48=3 = Pollschleife 3>4>3: Kinder obj+0x1D8/1DC +0x91==0 -> 5C406C, State bleibt 3. Weck-Schleife OK (Node in Liste).

- Hyp. 77: PS3_FIBERRATE=1 (fiberlog.patch): Original = Fiber-Resume-Busyspin (~6 Mio/s, CPU-Burn); REALFLAG = nur ~60 Resumes/s gesamt (Wake A2FAD0 ~60 Hz). Frames/Flips beide stagnierend.

- Hyp. 78-80: Tick-Fn 6D51xx ruft pro Frame A2FAD0 (60 Hz ok). REALFLAG (WaitFlagEx statt Spin) = DEFAULT in stubs.cpp (GT6_REALFLAG=0 = alt). orig/Frame4200: Dialog rendert KORREKT (4 Ecken, Bug weg).
- Hyp. 80: noadj + REALFLAG: Prozess endet nach ~52 s (exit-chain code=0x1, Threads 2/31 exit) - mit REALFLAG=0 kein Exit (black 99,5 %). Das Spiel quittet nun selbst.

## Naechster Schritt (EINER)
**Hyp. 81:** Warum quittet noadj+REALFLAG mit code 1? Log vor [exit-chain] (work/probe_h80_noadj_*/run.log.err, 40 Zeilen davor), wer ruft sys_process_exit / setzt Quit-Flag 0x164AB90 (xref --field 0x10 w, Obj 0x164AB80).

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
