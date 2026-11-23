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

## Erledigt / widerlegt (Details: eu-boot-log.md "STATE-Archiv")
- Hyp. 1-116, Befund 2/3 (PRIO_START, LOCKSTEP, fresh db), Fiber-Liste/Busyloop, Exit-Race, Snap-Diff: alle negativ/Symptom. Spinner bleibt.
- Live (user) + Probes: GT-Logo+Spinner nach AdjustScreen identisch. Probe-Setup ok.
- Befund 4 Audit offen: BgmPlaybackStatus, paramsfo memset, cellSync Layout, cellFs/SaveData.
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), PAD_LOG, scripts/live-padlog.ps1. Runtime = ps3recomp v0.20 (build-v020).

## RPCS3-Orakel (Ueberwacher, JP BCJS37016 + Save)
- RPCS3 nach AutoSave2 BKUP6: open PDIPFS/59/FI (535 MB Intro-Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. fsv-Lauf (VERBOSE): 0 fehlgeschlagene PDIPFS-Opens, 118 ok.
- Test pdi: RPCS3-USRDIR-Kopie (work/gt6_hdd0_rp, 14 GB) als hdd0, -KeepDb 300 s: NEGATIV: 18,8k Flips, GT-Logo+Spinner, NPN-IsLoaded-Schleife wie sonst; kein Open auf PDIPFS/59. Daten fehlen NICHT als Ursache.

## Naechster Schritt
Hot-Guest-Funktion-Sampling im Spinner: PS3_GUEST_PROF/Debug-Konsole nur in runtime/ppu/tests/boot_main.cpp (gt6 nutzt es nicht) -> Sampler nach gt6 portieren ODER Audit #1/#2. PDIPFS-Hypothese erledigt.

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
