# GT6PP LEDGER - dauerhafte Fakten (Ueberwacher, 2026-11-23). Nur ergaenzen/korrigieren, nie neu anfangen.
Zweck: Session-Wechsel ohne Verlust. STATE.md = aktueller Schritt, LEDGER = was gesichert ist. Jede Zeile mit Beleg. Zeilen <=200 Zeichen.
Einzige Linie: Game v1.22 + ps3recomp v0.20.0. 1.00-Historie: `ARCHIV/HISTORIE.md`.

## 1. Kanon (Build/Runtime)
- Build: `scripts\build-all.ps1` (decrypt-Check -> function list -> PPU lift -> post-lift -> clang-cl/Ninja). Ergebnis `gt6\build\gt6.exe`. Kein Versionsschalter, kein GT6_V122.
- Runtime: `third_party/ps3recomp-v020` (v0.20.0). Lift: `gt6/generated` (EMAIN 1.22, 74935 Fn, 41 Chunks). SPU: `gt6/src/gen` (16 Job-Images, PM id5, 1 Embedded-ELF).
- Beleg 2026-11-23: build-all Voll-Build ~8 min (16 Kerne), inkrementell (stubs.cpp) 4 s; probe smoke: boot.txt exe=gt6\build\gt6.exe, unresolved=0.
- Gast: `work/bin/EMAIN.elf` (1.22, sha256 in scripts/inputs.json, NPDRM-entschluesselt: `tools/self_decrypt_np.py`, Klic 9ff234b1..4724 aus RPCS3-Log Z.3478, keys gt6/data/keys nicht im Repo).
- Orakel RPCS3 (user, gleiche EU-Disc, Game 1.22): Log `...\v1.2_beta4_GT6-Launcher-win64\data\rpcs3\log\RPCS3.log` (Kopie work/oracle/), Daten `...\dev_hdd0\game\BCES01893\USRDIR` nur LESEN.
- Port-Details/Tabelle: `docs/analysis/PORT.md`. Adress-Mapping alt->neu: `tools/map_funcs.py`.
## 2. Offene Ports (1.22 hat noch keine Gast-Hooks)
- Fehlen: Script-Hooks (Kandidaten A67E1C/A67F60/A67DC4 unsicher), boot-presents, Menue-Pump, FileDeviceHost-Flush, (ADCH via Lifter-Entries erledigt), PFS-Cache-Fill, ZWAP, boot.adc-Gates. Frame 4200 schwarz ohne sie. Reihenfolge: boot-kritisch zuerst, Anker per Bytemuster.
- Runtime-Fixes gelten versionsunabhaengig (ps3recomp-v020): generation-keyed lwcond, host-font sync, FileDevice-flush-guard, sys_timer One-Shot, sys_mempool, cellMusic, cellFiber WaitFlag parkend, SPURS-Job-Walker.
## 3. Gesichert 1.22
- SPU: 16 von 20 bekannten Job-fps gefunden, WWS-PM byteidentisch (0 dispatch MISS). memset-Duff + 6er-Switch A2F158 manuelle Entries (tools/add_computed_entries.py).
- Spinner-Stall auf 1.22 identisch zu 1.00 (Hooks fehlen): 37 Threads geparkt (pc 0xB03BAC lwcond-Wrapper), kein Spin, 30 PDIPFS-Opens, kein PDIPFS/59/FI.
- SELF-Decrypt: EMAIN 1.22 = NPDRM (self_type 8, license 3); rpcs3 --decrypt allein scheitert.
- Hooks Stream/FileDevice/Host-Open auf 1.22 (Fuzzy-Map, Match 0.84-0.97) allein: Frame 4200 schwarz, kein PDIPFS/59 (probe hk122, 2026-11-23).
## 4. Widerlegt/Symptom (NICHT wiederholen)
- Pad/Dialog-Kette Hyp. 1-14; Exit-Race Hyp. 83-117; fresh vs persistente db; PRIO_START/LOCKSTEP/RESV_OFF; Fiber-Liste/Busyloop; Snap-Diff 140 vs 175 s; PDIPFS-Daten fehlen; RPCS3 --no-gui als Orakel.
- Version (1.00 vs 1.22) ist NICHT die Ursache des Spinners; Sysmodule-Ladeliste und frisches Savedata (PS3_GAMEDATA_ROOT) keine Divergenz zum Oracle.
## 5. Offene Kernfrage
- RPCS3 oeffnet nach PDIPFS/9/EE/3C `PDIPFS/59/FI` (Movie, PDI-Thread 0x100003b, Pamf/Vdec); wir oeffnen 85/H2, 8M/A9, 6W/RR, 75/M8, SG/LW, SC/IC, 8M/0K, 4J/0E und parken in lwcond (Loader 9qstY).
- Naechster Offline-Diff: Oracle-Aufrufer (LR) von 59/FI, Ausloeser der Movie-Entscheidung nach EE/3C, jetzt auf dem 1.22-Build gegen RPCS3 (gleiche Version). Hooks zuerst portieren.
## 6. Arbeitsregeln
- Vor jeder Hyp.: LEDGER lesen. Neue Erkenntnis -> 1 Zeile mit Beleg. Widerlegtes -> Abschnitt 4. Lauf-Log boot.txt muss `gt6\build\gt6.exe` nennen.

- 1.22: Menue-Pump 616C80 portiert (86302b5); Packages arcade/option/gtmode/garage/gtauto laden, danach Gast-Quit (AFDFC0 Event 0x1798F00, Schreiber unbekannt) ODER Null-Call-Schleife (AD3DFC Kopie, NULL-Element). Beleg: side-session befund_1.22_nullcall.md
- GT5P-Check (b): GT6 laedt Script main.adc ('[GT6] script override' im Log) + 30 PDIPFS-Opens -> Mount/Script-Load laufen; GT5P-Ursache P12 trifft nicht zu. (a) lwcond-Sender fuer Loader 9qstY weiter offen (ein Lauf mit lwcond_signal-Zaehler noetig).
