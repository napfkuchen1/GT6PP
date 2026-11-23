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
Hauptloop 0x568800 = Game-Loop. Script-VM startet gtmode, BGM laeuft. Flips ~9500/190s.
Capture: orig = AdjustScreen wartet auf X (Render korrekt, REALFLAG). Nach X: GT-Logo+Spinner = wie noadj.
Offen: Ladephase nach AdjustScreen; noadj-Exit bei 52s (NULL-Element im Zeigervektor, Hyp. 83-89).

## Erledigt / widerlegt (Einzeiler)
- Pad/Dialog-Kette (Hyp. 1-14): alles ohne Wirkung, durch Umgehung (15) hinfaellig. RPCS3 `--no-gui` als Orakel tot (Shader-Precompile).
- Plan B Pad-Replay: PAD_LOG=<pfad> (patches/gt6-v020-padlog.patch, build-v020 neu gebaut, getestet) + scripts/live-padlog.ps1: user spielt live, Log -> PAD_SCRIPT-Replay.
- SDK-Update ps3recomp v0.19 -> v0.20.0 (Klon third_party/ps3recomp-v020, lokale Patches gemergt, Build gt6\build-v020): Baseline noadj 220s/Frame 4200 identisch (GT-Logo+Spinner), Fortschritt gleich; Flips ~3x weniger (Pacing). Backend-Vergleich Vulkan vs D3D12 offen (PS3RECOMP_RSX_VULKAN + rsx_vulkan_backend_init).

- probe.ps1: -FreezeSec, -Seconds 0, END-Zeile, hdd0-Kopie/Lauf (-Parallel ok). PadScript nur Press-Tokens (0x0 verboten).
- Hyp. 78-80: REALFLAG (WaitFlagEx) = DEFAULT, Dialog rendert korrekt. noadj+REALFLAG: Exit ~52s (Race, Hyp. 81/82/86 pinned=deterministisch).
- Hyp. 83: Exit = A25C64 (vector.clear) aus 88B8E0, NULL-Element im Zeigervektor 71E4455C -> zeroed 14E4000..FFFFFFF0. Hyp. 84-89: Puffer/new/Lock nicht Ursache (Heisenbug).
- Hyp. 92: orig + PAD X (80-140s) -> Frame 9000 = GT-Logo+Spinner. AdjustScreen passiert.
- Hyp. 93-96: orig+Pad: Dauer-Churn, kein Freeze; Frame 15000 noch Logo+Spinner.
- Hyp. 109-116 (Details in eu-boot-log.md "Archiv"): Wipe = A25C64 Fill end-8 wrap, Aufrufer Worker-Cleanup 1AAC8C; Guard (A25C64 end<8 return) stoppt Exit, Spinner bleibt -> Wipe ist NICHT Ursache der Ladephase.

## UEBERWACHER-FINDINGS (2026-11-23, Review Hyp. 1-116 gegen ps3recomp v0.20 + third_party/GT5P)
1. Kette Hyp. 83-117 (35 Hyp.) jagt Exit-Race = Symptom. Guard-Survivor zeigen: auch ohne Exit bleibt Logo+Spinner. Race-Jagd STOPPEN.
2. UNGETESTET, billig, je 1 Batch (-Parallel 4): `PS3_PRIO_START=1` (lv2-Prioritaetsstart, SYSCALLS.md; Race-Klasse "Thread laeuft vor Init"), `PPU_RESV_OFF=1` A/B (stwcx-Reservation), `SPU_LOCKSTEP_QUANTUM`.
3. Probe != Live: user sieht live Menue nach Testrace. Probe nutzt FRISCHE userdb pro Lauf (GT6_HDD0-Kopie ohne db), boot.adc-Patches, <=320 s. Spinner evtl. = Erststart-Setup (DB/Save-Aufbau), dauert real >10 min. Test: Live-Run mit users persistenter db + 15 min, Frame-Captures 4200/9000/20000/40000.
4. GT5P-Schwesterport (gleiche PDI-Engine, third_party/GT5P/docs/progress.md): Wurzeln waren Runtime-Schreiber ins Spiel-Heap (VM_HLE_INJECT_BASE, GT6 ok = 0x03000000) und HLE-Stub mit falscher Argzahl (cellDiscGame schrieb in OPD-Tabelle). -> HLE-Stubs auditieren, die in Gast-Zeiger schreiben (PPU_WWATCH auf Opfer-Adresse, Writer-Attribution 'host' vs 'guest-fn').
5. Messen mit `PS3_VERBOSE=0` (probe.ps1 setzt das): Logging serialisiert Threads = Heisenbug-Ursache (GT5P README).

## Naechster Schritt (EINER)
**Befund 3 zuerst:** Live-Lauf (nicht probe.ps1) mit persistenter db, 15 min, Captures; parallel Befund-2-Batch auf Probe-Seite. Danach Befund 4 (HLE-Writer-Audit). Hyp. 117 (Iterator) VERWORFEN als naechster Schritt.

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
