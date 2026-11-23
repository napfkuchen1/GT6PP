# GT6PP EU - STATE (Einstieg, max ~5 KB halten)

Stand: 2026-11-23. Branch `eu-first-build`, Haupt-Checkout. Disc EU `BCES01893`.
Regeln/Fallen: `CLAUDE.md`. Gesicherte Fakten/Kanon: `LEDGER.md` (zuerst lesen). Voller Verlauf Hyp. 1-35: `ARCHIV/docs-analysis/STATE_full_2026-11-22.md`. Details/Messwerte: `eu-boot-log.md`.
**Pflege:** je Erkenntnis EINE Zeile in "Aktive Kette" oder "Erledigt" + "Naechster Schritt" aendern. Zeilen <=200 Zeichen.

## Ziel / Problem
Hauptmenue (gtmode) erreichen. Erststart-Dialoge sind per `boot.adc`-Gates umgehbar (Hyp. 15, `scripts/patch-boot-adc.py`).
KORREKTUR 2026-11-23: Live-Lauf user (Pad-Log work/padlog_20261123_104620.txt): nach Screen-Size-Menue Hang in GT-Logo+Spinner = wie Probes. Probe-Setup ok, Hang echt.

## Baseline-Varianten (probe.ps1 `-Boot`)
`orig` = Original | `noadj` = Dialog+Adjust uebersprungen, Tutorial-Rennen laeuft | `notut` = alles uebersprungen, 27-Track-Schleife.
Varianten aendern `work/gt6_vol/.../boot.adc` -> NIE parallel starten. Originale in `work/ARCHIV/boot.adc.*`.
Standard: `scripts\probe.ps1 -Name x -Boot notut -Seconds 320`. Frame-Capture: `-Frame N` (Frame 4200 ~320-420 s).
Binary: `gt6\build\gt6.exe` (Game 1.22 + ps3recomp v0.20, `scripts\build-all.ps1`).

## Aktive Kette
Hauptloop 0x568800 = Game-Loop. Script-VM startet gtmode, BGM laeuft. Flips ~9500/190s.
Capture: orig = AdjustScreen wartet auf X (Render korrekt, REALFLAG). Nach X: GT-Logo+Spinner = wie noadj.
Offen: Ladephase nach AdjustScreen; noadj-Exit bei 52s (NULL-Element im Zeigervektor, Hyp. 83-89).

## Erledigt / widerlegt (Details: eu-boot-log.md "STATE-Archiv")
- Hyp. 1-116, Befund 2/3 (PRIO_START, LOCKSTEP, fresh db), Fiber-Liste/Busyloop, Exit-Race, Snap-Diff: alle negativ/Symptom. Spinner bleibt.
- Live (user) + Probes: GT-Logo+Spinner nach AdjustScreen identisch. Probe-Setup ok.
- Befund 4 Audit offen: BgmPlaybackStatus, paramsfo memset, cellSync Layout, cellFs/SaveData.
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), PAD_LOG, scripts/live-padlog.ps1. Runtime = ps3recomp v0.20.

## RPCS3-Orakel (Ueberwacher, gleiche EU-Disc BCES01893; BCJS37016 = nur interner Savedata-Name)
- RPCS3 nach AutoSave2 BKUP6: open PDIPFS/59/FI (535 MB Intro-Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. fsv-Lauf (VERBOSE): 0 fehlgeschlagene PDIPFS-Opens, 118 ok.
- Test pdi: RPCS3-USRDIR-Kopie (work/gt6_hdd0_rp) als hdd0, 300 s: NEGATIV, GT-Logo+Spinner, kein Open auf PDIPFS/59. Daten fehlen NICHT als Ursache.
- Gast-PC-Sampler (gt6/src/gt6_gprof.cpp, GT6_GPROF=1, GT6_GPROF_SEC=n): Spinner = 37 Threads geparkt, 29 in sys_lwcond_wait-Wrapper (pc 0xA4305C), kein Spin/Busyloop.
- Loader 9qstY (tid 32) haengt in lwcond_wait; RPCS3 laeuft dort weiter (PDI-Thread -> 59/FI-Open -> Pamf/Vdec). Ausloeser des 59/FI-Requests unbekannt.
- VERSIONS-DIVERGENZ: RPCS3 fuehrt gepatchtes Spiel (EMAIN 9209104 B, EBOOT 165712 B, Daten GT6_1.N); wir recompilen Disc-Basis (work/bin EMAIN 8843160 B, EBOOT 72920 B, GT6.N).
- Basis-EMAIN (work/bin, 8843160 B) statisch: Movie-Code (tv_*.pam, cellPamf/Dmux/Vdec/Sail), PDIPFSNetworkPatch*, MSystemPatch vorhanden. Kein UPDATENODEINFO/PATCHSEQUENCE.
- Basis nutzt /APP_DATA/%s.%d (GT6.N), GT6_1.N nur im Update-EMAIN. Stack-Walk tid 32 (snap_rf1) nur Altlasten; lwcond-Signaler offen.
## Naechster Schritt
Hyp. guard (2026-11-23): 3 Laeufe orig 70-90 s (guard / NO_NOTIFYGUARD / +NO_CTXFIBER) identisch: ~100 Flips, Gast-Quit nach ~30 s. Null-Call-Sturm 0-1x -> Guard/ctxfiber nicht ursaechlich.
Quit-Kette 1.22 (korrigiert): Hauptloop 0x146E8 endet wenn AD2998 !=0 = Byte 0x1796DC8 (Objekt 0x1796DB8+0x10). PPU_WWATCH=1796DB0 LEN 32: KEIN Store setzt es !=0 -> Writer ist ungehookt (HLE-memcpy/Host-Pointer, z.B. cellSaveData-Load GT6.0-5 direkt vor Term) oder Flag via anderen Pfad.
AFDFC0/0x179ECF0-Struct = Titel-ID-Strcmp ("BCES01893"), NICHT der Quit-Weg (Alt-Annahme 0x1798F00 falsch).
Hyp. fileBuf: Savedata-fileBuf = 0x901A0000/0x931C0000 (16 MB), kein Overlap mit 0x1796DC8 -> Savedata-HLE entlastet.
Hyp. snap: SNAP_AT 6 s: Main (tid1) noch in INIT, wartet (lwcond) auf Task-Objekt 0x7FFCEE90; Stack A30028<-A7E6CC<-A521CC<-13D94(ctr)<-109C4. Ab 8 s schon Shutdown-Wait (while [0x1710E3C] usleep 5ms). Flag 0x1796DC8 in allen Snaps 0 -> Quit NICHT ueber Loop 146E8, Init-Wait bricht ab/Fehlerpfad.
Hyp. nullist: tid30 fuehrt Job 0x7FFCEE70 (Run 7B5208->6166A4(obj 7FEEC000,vt 15B5668)->AD4294(disp 7FFBE100,vt 15DC800)). AD4294 kopiert Listener-Liste (AD3DFC), Knoten next=0 -> Endlos-NULL-read.
Naechster: Snap 6 s: Listener-Liste von disp 7FFBE100 (Kopie sp+0x70 in AD4294 Frame D00CEA90) per snap_walk obj laufen; welcher Knoten next=0, wer hat ihn genullt (WWATCH, Log run.log.err). Dann warum Main-Wait endet.
Infra: probe.ps1 killt gt6 jetzt zusaetzlich per taskkill /T (hing in ppu_thread_join).

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
