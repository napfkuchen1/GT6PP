# GT6PP LEDGER - dauerhafte Fakten (Ueberwacher, 2026-11-23). Nur ergaenzen/korrigieren, nie neu anfangen.
Zweck: Session-Wechsel ohne Verlust. STATE.md = aktueller Schritt, LEDGER = was gesichert ist. Jede Zeile mit Beleg. Zeilen <=200 Zeichen.

## 1. Kanon (Build/Runtime) - HIER nachschauen, nicht raten
- Gueltiger Build: `gt6\build-v020\gt6.exe` = Runtime ps3recomp v0.20.0 (Klon `third_party/ps3recomp-v020`). PFLICHT: `$env:GT6_BUILD_DIR='gt6\build-v020'`.
- ARCHIVIERT 2026-11-23 (nicht geloescht): alte Builds `gt6\build`, `build-clangcl` (v0.19), `build-v020-vk` -> `ARCHIV/old-builds/`; alte Snapshots -> `work/ARCHIV/snaps/` (2 neueste bleiben im Root). `third_party/ps3recomp` = v0.19, veraltet: Archivierung offen (CMake-Default + Skripte erst auf -v020 umstellen).
- Fix 2026-11-23: probe.ps1 nimmt jetzt build-v020 als Default; alte Builds nur mit `-AllowOldBuild`. Lauf-Log `boot.txt` nennt EXE-Pfad.
- 2. Kanon (Port eingefroren 2026-11-23): `gt6\build-v122\gt6.exe` (EMAIN v1.22, gt6-122/generated, GT6_V122=ON) baut+laeuft (0 unresolved, SPU lift ok), Gast-Hooks nicht portiert; Spinner identisch -> keine weitere Investition.
- Gast-Basis: EMAIN.elf aus EU-Disc BCES01893 v1.00 (`work/bin`, 8843160 B SELF, 22371400 B ELF), Lift `gt6/generated` (75538 Fn), per-fp Post-Lift-Patches `tools/apply_gt6_post_lift.py`.
- RPCS3-Orakel (user): Log `...\v1.2_beta4_GT6-Launcher-win64\data\rpcs3\log\RPCS3.log`, Daten `...\data\rpcs3\dev_hdd0\game\BCES01893\USRDIR` (nur LESEN). Game v1.22, gleiche EU-Disc.
- Version-Divergenz: RPCS3 = v1.22 (EMAIN 9209104 B, EBOOT 165712 B, Daten GT6_1.N). Wir = v1.00 (GT6.N). Recomp v1.22 freigegeben (User 2026-11-23), additiv in neuen Pfaden.
- Umstellung 2026-11-23: PS3RECOMP_DIR-Default + scripts (build-gt6, gen-functions, lift-spu*, relift, probe) + boundary_audit.py -> ps3recomp-v020. Test: build-gt6-clangcl -BuildName build-v020 gruen.
- v0.19-Runtime `third_party/ps3recomp` -> `ARCHIV/ps3recomp-v019/`; 47 `work/_bk_*` (kein Skript referenziert sie) -> `work/ARCHIV/bk/` (inkl. _bk_gt6_v020.exe).
- v1.22 SELF->ELF BLOCKIERT: decrypt_self.py braucht gt6/data/keys (fehlt, nie im Repo); rpcs3.exe --decrypt erzeugt stumm nichts. Dep: Keys oder GUI-Decrypt (User). work/bin122/EMAIN.SELF = Kopie.
## 2. Historie (belegt per git)
- 2026-10-31/11-01 Upstream (xynnpg, USA-Disc): Boot bis schwarzes Fenster, MGOM.start("boot"), Manager Zustand 2. KEIN Menue. (docs/STATUS.md, progress.json)
- 2026-11-20..22 Fork: EU-Disc kompatibel (eu-bces01893-compat.md). Erster echter Frame, Sprachauswahl sichtbar (eu-boot-log "First real frame").
- 2026-11-22/23 Fixes bis AdjustScreen (Screen-Size-Menue) mit Pad-Eingabe. Danach GT-Logo+Spinner ewig. Hauptmenue wurde NIE erreicht (eu-boot-log "Menue-Run": NICHT erreicht; Live-Lauf user 11-23: Hang).
- "Menue sichtbar" in alten Notizen = Sprachauswahl/AdjustScreen, nicht Hauptmenue.

## 3. Verifizierte Fixes (muessen bei v1.22-Port WIEDER angewendet werden; Adressen dort neu suchen!)
- Runtime: generation-keyed lwcond (3467267), host-font sync (patches/gt6-host-font-sync.patch), FileDevice-flush-guard, sys_timer One-Shot, sys_mempool, cellMusic*2 + Callback, cellFiber WaitFlag/CheckFlags parkend (REALFLAG default, behebt AdjustScreen-Render), SPURS-Job-Walker (Hyp. 46).
- Spiel-Seite: PFS-Cache-Fill (b5b260), ZWAP-Gate, MGOM.start Pump (Hyp. 39/42), per-fp a3 Titelfarbe, boot.adc-Gates (scripts/patch-boot-adc.py).
- Patch-Dateien: `patches/`, Post-Lift-Skript `tools/apply_gt6_post_lift.py`; Backups `work/_bk_*`. Harte US-1.00-Adressen -> bei 1.22 verschieben.

## 4. Widerlegt/Symptom (NICHT wiederholen)
- Pad/Dialog-Kette Hyp. 1-14; Exit-Race Hyp. 83-117 (Symptom); fresh vs persistente db; PRIO_START/LOCKSTEP/RESV_OFF; Fiber-Liste/Busyloop; Snap-Diff 140 vs 175 s.
- PDIPFS-Daten fehlen: NEGATIV (Lauf mit 14-GB-RPCS3-Kopie, gleicher Spinner). RPCS3 `--no-gui` als Orakel: tot (Shader-Precompile).
- Oracle-Diff 2026-11-23 (scripts/oracle_seq.py, HLE-Trace PS3_HLE_TRACE_ARM): Sysmodule-Ladeliste nach AutoSave2 = KEINE Divergenz (Oracle-Extra-IDs 0x24-0x2d = RPCS3-Dependency-Rekursion, gleicher LR); Savedata frisch (PS3_GAMEDATA_ROOT leer, AutoLoad2 -4 wie Oracle): kein 59/FI.
- PDIPFS/9-Open-Folge 1.00+rp-hdd0 (probe_pdi) = Oracle bis EE/3C (14/16 Namen); danach Oracle: 59/FI, wir: 85/H2,8M/A9..4J/0E. Divergenz liegt NACH EE/3C (Auswahl Movie vs Folge-Assets), nicht in Savedata/Sysmodule.
- Spinner = reiner Deadlock: 37 Threads geparkt, 29 in sys_lwcond_wait (pc A4305C), Loader 9qstY (tid 32) wartet; kein Busyloop (GT6_GPROF).

## 5. Offene Kernfrage
- RPCS3 laeuft an derselben Stelle weiter (PDI-Thread -> PDIPFS/59/FI -> Pamf/Vdec/Dmux/Sail). Basis-EMAIN kennt Movie- und Patch-Code (PDIPFSNetworkPatch*, PatchInstall, MSystemPatch).
- Naechster Offline-Diff: Oracle-Thread, der 59/FI oeffnet (PDI 0x100003b), und was NACH PDIPFS/9/EE/3C in 9qstY/PDI-Kette die Movie-Entscheidung triggert (Aufrufer-Baum 1.22 per oracle LR, auf 1.00 mappen).
- Hypothese (offen): v1.00 wartet auf Patch/Update-/NP-Ereignis, das v1.22 nicht braucht. Test = v1.22-Recomp.

## 6. Arbeitsregeln (Ueberwacher)
- Vor jeder Hyp.: LEDGER lesen. Neue gesicherte Erkenntnis -> hier 1 Zeile mit Beleg. Widerlegtes -> Abschnitt 4.
- Immer GT6_BUILD_DIR/Kanon pruefen (Abschnitt 1) und im Lauf-Log EXE verifizieren, bevor Ergebnis gilt.

## 7. SELF-Decrypt v1.22 (Ueberwacher 2026-11-23, getestet)
- `rpcs3.exe --decrypt`: v1.00 EMAIN OK (SHA ACB00C19.. identisch), v1.22 EBOOT.BIN OK (-> `work/bin122/EBOOT_122.elf`, 278344 B). v1.22 EMAIN.SELF und v1.14 FIXEDELF114: "SELF: Failed to decrypt SELF metadata info!"
- Gleiches Ergebnis mit tools/RPCS3 (v0.0.43-20641 master) und User-RPCS3 (v0.0.43-eee3f0f7 gt6-Build). Nicht an Pfad/Rechten/Build-Variante.
- RPCS3 bootet dieselbe Datei trotzdem: EBOOT 1.22 ruft sceNpDrmIsAvailable(EMAIN.SELF) + sceNpDrmProcessExitSpawn2 (Orakel-Log Z.3479). Verdacht: EMAIN 1.22 ist NPDRM-SELF, Klic kommt vom EBOOT, nicht im --decrypt-Pfad.
- Naechster Test: Klic (16 B) in EBOOT_122.elf an den sceNpDrm*-Aufrufen suchen; mit Klic per RPCS3-Decrypt (GUI Utilities) oder eigenem Skript entschluesseln. Kein Credential noetig.
- GELOEST 2026-11-23: EMAIN 1.22 = NPDRM (self_type 8, license 3), Klic <klicensee redacted> (RPCS3-Log Z.3478). `tools/self_decrypt_np.py in.SELF out.elf [klic]` (keys gt6/data/keys, nicht im Repo) -> work/bin122/EMAIN.elf 23787792 B. Selbsttest: 1.00 byte-identisch mit work/bin/EMAIN.elf.
- 1.22 EMAIN.elf sha1 0e1fc30db223a65375f0032985a73e2bde630751. Klic nicht als 16-B-Literal in EBOOT_122.elf (Suche leer); Wert aus RPCS3-Log funktioniert. Port-Tabelle: docs/analysis/PORT_122.md.

## 8. v1.22-Port (2026-11-23)
- build-v122 = zweiter Kanon (`gt6\build-v122\gt6.exe`, `gt6-122/generated`, EMAIN work/bin122, 74935 Funcs). Probe: `-BuildDir build-v122`.
- 1.22 memset-Duff + 6er-Switch (A2F158) brauchen manuelle Entries (add_computed_entries.py ... 122); ctor/setjmp relokiert (PORT_122). Beleg: v122b->v122d unresolved 6733->0.
- 1.22 SPU: Job-Images sind Rohbereiche in EMAIN 1.22 (128-aligned, Header 4x-Worte 0x42/0x43..0x02/0x82); FNV-fp aus Laufzeitlog -> tools/find_spu_jobs_122.py. 16 von 20 bekannten 1.00/1.22-fps gefunden; WWS-PM fp 5510DCB8.. byteidentisch (Beleg: probe_v122g, 0 dispatch MISS).
- 1.22 Spinner-Test (probe_v122fsv orig, probe_v122noadj noadj; PS3_VERBOSE=1): 30 PDIPFS-Opens, 0x PDIPFS/59, 0x Pamf -> kein Unterschied zu 1.00; Gast-Hooks fehlen aber (Frame 4200 schwarz), also nur Vorbefund.
- 1.22 Gast-PC-Sampler (probe_v122gprof noadj, GT6_GPROF=1): 37 Threads geparkt (pc 0xB03BAC lwcond-wait-Wrapper, 9qstY tid30 ebenso), kein Spin -> Spinner-Stall auf 1.22 identisch zu 1.00 (Hooks nicht portiert).
