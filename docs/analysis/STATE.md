# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-23. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`.
Regeln/Fallen: `CLAUDE.md`. Voller Verlauf Hyp. 1-35: `docs/analysis/STATE_full_2026-11-22.md`. Details/Messwerte: `eu-boot-log.md`.
**Pflege:** je Erkenntnis EINE Zeile in "Aktive Kette" oder "Erledigt" + "Naechster Schritt" aendern. Zeilen <=200 Zeichen.

## Ziel / Problem
Hauptmenue (gtmode) erreichen. Erststart-Dialoge sind per `boot.adc`-Gates umgehbar (Hyp. 15, `scripts/patch-boot-adc.py`).
KORREKTUR 2026-11-23: Live-Lauf user (Pad-Log work/padlog_20261123_104620.txt): nach Screen-Size-Menue Hang in GT-Logo+Spinner = wie Probes. Probe-Setup ok, Hang echt.

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

## RPCS3-Orakel (Ueberwacher, gleiche EU-Disc BCES01893; BCJS37016 = nur interner Savedata-Name)
- RPCS3 nach AutoSave2 BKUP6: open PDIPFS/59/FI (535 MB Intro-Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. fsv-Lauf (VERBOSE): 0 fehlgeschlagene PDIPFS-Opens, 118 ok.
- Test pdi: RPCS3-USRDIR-Kopie (work/gt6_hdd0_rp) als hdd0, 300 s: NEGATIV, GT-Logo+Spinner, kein Open auf PDIPFS/59. Daten fehlen NICHT als Ursache.
- Gast-PC-Sampler (gt6/src/gt6_gprof.cpp, GT6_GPROF=1, GT6_GPROF_SEC=n; Build build-v020): Spinner = 37 Threads geparkt, 29 in sys_lwcond_wait-Wrapper (pc 0xA4305C), kein Spin/Busyloop.
- Loader 9qstY (tid 32) haengt in lwcond_wait; RPCS3 laeuft dort weiter (PDI-Thread -> 59/FI-Open -> Pamf/Vdec). Ausloeser des 59/FI-Requests unbekannt.
- VERSIONS-DIVERGENZ: RPCS3 fuehrt gepatchtes Spiel (EMAIN 9209104 B, EBOOT 165712 B, Daten GT6_1.N); wir recompilen Disc-Basis (work/bin EMAIN 8843160 B, EBOOT 72920 B, GT6.N).
- Basis nutzt /APP_DATA/%s.%d (GT6.N), GT6_1.N nur im Update-EMAIN. Stack-Walk tid 32 (snap_rf1) nur Altlasten; lwcond-Signaler offen.
- Basis nutzt Format /APP_DATA/%s.%d (GT6.N); GT6_1.N nur im Update-EMAIN. Basis-Pfad laeuft auf Disc ohne Update-Zwang. Stack-Walk tid 32 (snap_rf1) liefert nur Altlasten, lwcond-Signaler offen.
- ABSCHAETZUNG Recomp Patch-EMAIN 1.22 (RPCS3 EMAIN.SELF 9209104 B; FIXEDELF114 = 1.14, 9059040 B), NICHT gestartet, User entscheidet:
  1) SELF->ELF: gt6/scripts/decrypt_self.py braucht pycryptodome (fehlt) + Keys/RAP; ELF liegt dann als work/patchelf/. Aufwand ~1-2 h, Risiko Keys.
  2) Lift + Gen (relift-gt6/gen-functions-gt6, ~1 h Rechenzeit) und Neu-Build ~2 min; alle Adress-Patches/Guards (H113 A25C64, boot.adc-Gates) neu portieren: 0,5-1 Tag. Gesamt ~1-2 Tage.

## Naechster Schritt
lwcond von 9qstY (tid 32) + Signaler per Snapshot/xref finden (war Signal verloren oder Bedingung nie erzeugt?). Parallel pruefen: ob Basis-EMAIN den 59/FI-Pfad ueberhaupt kennt (Update-Differenz).

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
