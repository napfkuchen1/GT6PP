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
- Hyp. 109-111: statische Kette Wipe: 7D083C (Wrapper, Singleton 0x159FD890) > 7CD628 > 88B878 > bl A25C64 (je 1 Aufrufer, 7D083C ohne direkten). CALLTRACE_TO auf 7D083C/7CD628/88B878/88B8E0: 0 Treffer (Exit-Laeufe h110 4/4 mit CALLTRACE=200, 88B8E0 ist ein bl-Site).
- Hyp. 112: GSTACK im Exit-Lauf (run.log.err, h110): Worker tid32 "9qstY" (A304D0>7FB1F0>7FB090>7DF57C>7DFF44>7DF7DC>802004>1AE7CC>1AE5E4>1AE074>1AAC8C>7D083C>7CD628>88B878>A25C64). Unfiltered Calltrace: kein Exit (Heisenbug).
- 1AAC8C = Cleanup-Task (Obj+0x1F30: 7D0904,7D0DE8,7D0FC0,7D083C,7D08DC), einziger Aufrufer 1AE1E8 in 1AE074. Frage: warum laeuft Cleanup beim X-Press, Singleton-Vektor 71E4455C hat NULL-Element.
- Hyp. 113: A25C64 = Fill [begin,end-8] mit 0 (Vektor elem+0x2C: begin@+8, end@+0xC). Leer begin=end=0 -> end-8 wrap (unsigned) -> Fill 0..FFFFFFF8 = Wipe.
  Elem-Objekt unkonstruiert/genullt (race). Loop-Log: normale Laeufe 2 Elemente ok (7FFEE090/E0D8); 2. Exit-Typ: erster NULL-Write aus CAC2D4 (1AE074+0x488), nicht A25C64 -> generelle Race.
- Umgehung: Guard in func_00A25C64 (generated 023): end<8 -> return. Backups work/_bk_h113/. h114/h115 (10 Laeufe): 0 Exits, Guard feuert ~30% (Elem-Zeiger Muell/NULL).
- Hyp. 115: Guard-Survivor Frame 9000 (4x) = GT-Logo+Spinner. fs-Zugriffe enden frueh (kein IO-Wait). 2/4: A2FAD0 Ringlisten-Walk mit NULL-Knoten = Busyloop (3.7M null-writes).
- Befund: Teardown-Tasks (1AE074: +0x178 1AAC8C, +0x508 7CFDD0>88B928) laufen auf Singleton/Listen, die parallel genutzt/genullt sind = Use-after-free-Race. Ursache offen.
- Hyp. 116: TLS-TID-Cache (A3046C) liefert pro r13 eindeutige ids (1,2,5,9..34) -> TID-Duplikat widerlegt. 1AAC8C/1AAD14 laufen JEDEN Frame (kein Wait/Teardown-Trigger) = normal.

## Naechster Schritt (EINER)
**Hyp. 117:** Wer schreibt Muell in Elemente des Vektors (obj+0x17055c / 71E4455C)? Snapshot-Walk (snap_walk.py) vor X-Press vs danach: Vektor-Objekt-Adresse + Allokator (new/free) des Elem-Blocks; Heap-Reuse (use-after-free) pruefen.

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
