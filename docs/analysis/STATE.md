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
- Tools: probe.ps1 (-KeepDb, -Hdd0Src), PAD_LOG, scripts/live-padlog.ps1. Runtime = ps3recomp v0.20 (build-v020).

## RPCS3-Orakel (Ueberwacher, gleiche EU-Disc BCES01893; BCJS37016 = nur interner Savedata-Name)
- RPCS3 nach AutoSave2 BKUP6: open PDIPFS/59/FI (535 MB Intro-Film), dann Pamf/Dmux/Vdec. Unser hdd0: PDIPFS 24 MB, kein 59/FI. fsv-Lauf (VERBOSE): 0 fehlgeschlagene PDIPFS-Opens, 118 ok.
- Test pdi: RPCS3-USRDIR-Kopie (work/gt6_hdd0_rp) als hdd0, 300 s: NEGATIV, GT-Logo+Spinner, kein Open auf PDIPFS/59. Daten fehlen NICHT als Ursache.
- Gast-PC-Sampler (gt6/src/gt6_gprof.cpp, GT6_GPROF=1, GT6_GPROF_SEC=n; Build build-v020): Spinner = 37 Threads geparkt, 29 in sys_lwcond_wait-Wrapper (pc 0xA4305C), kein Spin/Busyloop.
- Loader 9qstY (tid 32) haengt in lwcond_wait; RPCS3 laeuft dort weiter (PDI-Thread -> 59/FI-Open -> Pamf/Vdec). Ausloeser des 59/FI-Requests unbekannt.
- VERSIONS-DIVERGENZ: RPCS3 fuehrt gepatchtes Spiel (EMAIN 9209104 B, EBOOT 165712 B, Daten GT6_1.N); wir recompilen Disc-Basis (work/bin EMAIN 8843160 B, EBOOT 72920 B, GT6.N).
- Basis-EMAIN (work/bin, 8843160 B) statisch: Movie-Code (tv_*.pam, cellPamf/Dmux/Vdec/Sail), PDIPFSNetworkPatch*, MSystemPatch vorhanden. Kein UPDATENODEINFO/PATCHSEQUENCE.
- Basis nutzt /APP_DATA/%s.%d (GT6.N), GT6_1.N nur im Update-EMAIN. Stack-Walk tid 32 (snap_rf1) nur Altlasten; lwcond-Signaler offen.
- 1.22 SPU-Lift: 16 Job-Images (fp-Scan tools/find_spu_jobs_122.py), PM id5 (byteidentisch, 0x14DAA80), 1 Embedded-ELF -> gt6/src/gen122 + gt6-122/generated/spu_lifted. 0 dispatch MISS, ~11400 Flips/180 s.
- Spinner-Frage 1.22 (VERBOSE-fs, orig+noadj 200-220 s): 30 PDIPFS-Opens, KEIN PDIPFS/59/FI, kein Pamf. Update-EMAIN allein loest Spinner nicht.
- Oracle-Diff (oracle_seq.py, PS3_HLE_TRACE_ARM): Sysmodule-Folge + frisches Savedata = KEINE Divergenz. PDIPFS/9-Opens = Oracle bis EE/3C, danach Oracle 59/FI, wir 85/H2... Divergenz NACH EE/3C.
- Hooks 1.22 portiert (tools/port_hooks.py: Stream r/s/t, 3 FileDevice-Guards, Host-Open AB080C). Probe hk122 noadj 220 s: unresolved=0, Frame 4200 schwarz 100%, kein PDIPFS/59. Script-Hooks/Menue-Pump fehlen.
- rp122 (RPCS3-hdd0, noadj 220 s): kein 59/FI. Open-Diff: Oracle oeffnet 9/PR/MF (Worker MkZA-) nach 8G/RB, wir 8Y/Y0 (Oracle nie); 26 Oracle-Opens vor EE/3C fehlen, EE/3C nie erreicht.
## Naechster Schritt
Hyp. guard (2026-11-23): 3 Laeufe orig 70-90 s (guard / GT6_NO_NOTIFYGUARD / +GT6_NO_CTXFIBER): ALLE identisch ~100 Flips, Gast-Quit nach ~30 s (sceNp Term, cellKb End). Null-Call-Sturm 0-1 mal -> Guard/ctxfiber nicht ursaechlich. Blocker = Quit-Kette AFDFC0 (poll AFE38C, Quit-Test AD2998).
Naechster: statisch AFE38C/AD2998 -> wer setzt Quit-Event (Event-Struct 0x1798F00 +0x30/+0x31). Befund: gt6 haengt nach Quit im Shutdown (ppu_thread_join) -> probe.ps1 Stall-Kill muss gt6 selbst killen.

## Roadmap-Bezug
M2 weitgehend done. M3 (RSX/erster Menue-Frame) offen. Siehe `ROADMAP.md`.
