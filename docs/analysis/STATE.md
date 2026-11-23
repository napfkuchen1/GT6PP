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
- Hyp. 65-68: tid 1 Dauer-Haenger ab <=100 s (auch v0.19). Servicer 56865C = OPD 14BF800->568A0C (obj 0x7FEAC000), gestartet via 56B948->A14824 (Factory 0x7FFBE280). Kein Thread mit dem Entry.
- Hyp. 69: A14824 laeuft frueh (CALLTRACE ohne AFTER): vt+8 A2F93C, vt+0xC A2FC54 = cellFiberPpuCreateFiber (NID 7C2F4034, Entry-OPD 14E0848). Es ist ein FIBER, kein Thread.
- Hyp. 69b/70: Runner A2FAD0 (vt+0x1C, RunFibers) laeuft in tid 32 (567D74+0x2A4). PS3_FIBERLOG=1 (cellFiber.c Patch, build-v020): Fiber 7FF0C800 opd 14E0848 wird erzeugt+resumed.
- => Hyp. 66-68 'Thread nie gestartet' FALSCH: Servicer laeuft als FIBER (CALLTRACE sieht Fiber-Entry nicht). Fiber resume/back state=0 (READY=Yield) in Dauerschleife = pollt.

## Naechster Schritt (EINER)
**Hyp. 71:** Fiber yieldet dauernd (state=0). Wer yieldet (gt6_cellFiberPpuWaitFlag stubs.cpp:1382 / cellFiberPpuYield) und worauf pollt er (flag_ea)? Danach: setzt irgendwer obj+0x48 1->2 im Fiber?

## Roadmap-Bezug
M2 (Engine-Boot/Assets) weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
