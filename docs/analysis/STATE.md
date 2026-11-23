# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-23. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`.
Regeln/Fallen: `CLAUDE.md`. Voller Verlauf Hyp. 1-35: `docs/analysis/STATE_full_2026-11-22.md`. Details/Messwerte: `eu-boot-log.md`.
**Pflege:** je Erkenntnis EINE Zeile in "Aktive Kette" oder "Erledigt" + "Naechster Schritt" aendern. Zeilen <=200 Zeichen.

## Ziel / Problem
Hauptmenue (gtmode) erreichen. Erststart-Dialoge sind per `boot.adc`-Gates umgehbar (Hyp. 15, `scripts/patch-boot-adc.py`).
KORREKTUR 2026-11-23: Live-Lauf user (live-padlog, Pad-Log work/padlog_20261123_104620.txt): Screen-Size-Menue, Eingaben akzeptiert, danach Hang in GT-Logo+Spinner = identisch zu Probes. "Menue sichtbar" war frueher falsch/ueberbewertet. Probe-Setup ist KEIN Fehler; Hang ist echt.

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
- Hyp. 109-116 (Details in eu-boot-log.md "Archiv"): Wipe = A25C64 Fill end-8 wrap, Aufrufer Worker-Cleanup 1AAC8C; Guard (A25C64 end<8 return) stoppt Exit, Spinner bleibt -> Wipe ist NICHT Ursache der Ladephase.

## UEBERWACHER-FINDINGS (2026-11-23, Review Hyp. 1-116 gegen ps3recomp v0.20 + third_party/GT5P)
1. Kette Hyp. 83-117 (35 Hyp.) jagt Exit-Race = Symptom. Guard-Survivor zeigen: auch ohne Exit bleibt Logo+Spinner. Race-Jagd STOPPEN.
2. UNGETESTET, billig, je 1 Batch (-Parallel 4): `PS3_PRIO_START=1` (lv2-Prioritaetsstart, SYSCALLS.md; Race-Klasse "Thread laeuft vor Init"), `PPU_RESV_OFF=1` A/B (stwcx-Reservation), `SPU_LOCKSTEP_QUANTUM`.
3. Probe != Live: user sieht live Menue nach Testrace. Probe nutzt FRISCHE userdb pro Lauf (GT6_HDD0-Kopie ohne db), boot.adc-Patches, <=320 s. Spinner evtl. = Erststart-Setup (DB/Save-Aufbau), dauert real >10 min. Test: Live-Run mit users persistenter db + 15 min, Frame-Captures 4200/9000/20000/40000.
4. GT5P-Schwesterport (gleiche PDI-Engine, third_party/GT5P/docs/progress.md): Wurzeln waren Runtime-Schreiber ins Spiel-Heap (VM_HLE_INJECT_BASE, GT6 ok = 0x03000000) und HLE-Stub mit falscher Argzahl (cellDiscGame schrieb in OPD-Tabelle). -> HLE-Stubs auditieren, die in Gast-Zeiger schreiben (PPU_WWATCH auf Opfer-Adresse, Writer-Attribution 'host' vs 'guest-fn').
5. Messen mit `PS3_VERBOSE=0` (probe.ps1 setzt das): Logging serialisiert Threads = Heisenbug-Ursache (GT5P README).

ERGEBNISSE 2026-11-23 (probe.ps1 -KeepDb, RSX_CAP=start:count:stride via -Env, build-v020):
- Befund 3 WIDERLEGT: persistente db (-KeepDb), orig+X@100s, 900 s/100k Flips: Frame 4200 AdjustScreen, 7200..19200 stabil GT-Logo+Spinner. Fresh-db ist nicht die Ursache.
- Befund 2 NEGATIV: PRIO_START=1 / SPU_LOCKSTEP(Q1000) / Kontrolle: Frame 4200 identisch (AdjustScreen, 28,4% schwarz). PPU_RESV_OFF=1 schlechter: nur 6555 Flips/430 s, NP2-IsLoaded-Schleife.
- Befund 4 Audit (statisch, offen): Verdacht M-H cellSysutilGetBgmPlaybackStatus (cellSysutil.c ~507, memset 0x28 vs SDK-Struct), M sys_process_get_paramsfo memset 256, cellSync Barrier/Rwm Host-Layout. cellFs/SaveData nicht auditiert.
- Spinner-Zustand (wd2/ct): Waiter alle idle, keine Event-Staus. NEU: wake-all A2FAD0 ~13k/s von tid32 (func_00567D74+0x2A4), Fiber-Listenknoten mit NULL-Element (NULL+0x40-Writes, 4,5M). Details eu-boot-log.md.

- Fiber-Liste A/B (snap 200s, REALFLAG 0 vs 1): Obj 7FFBE280 count=1, Knoten-Payload nicht NULL, Struktur identisch -> NULL+0x40 kommt NICHT aus dieser Liste; REALFLAG ohne Einfluss.

## Naechster Schritt (EINER)
A2FAD0-Aufrufe zaehlen je r3 (CALLTRACE_TO=A2FAD0), woher NULL-Payload-Liste; cellFiberPpu*-Rueckgaben loggen; danach Audit #1/#2.

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
