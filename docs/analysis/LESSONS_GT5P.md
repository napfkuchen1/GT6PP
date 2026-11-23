# Lessons aus GT5P (Schwesterport, gleiche PDI-Engine)
Quelle: third_party/GT5P/docs/progress.md (Phase 12-16). Nur Fakten daraus; "(Annahme)" = nicht belegt.

## Pro Phase: Symptom -> Ursache -> Beleg
- P16 (ps3recomp master): Freelist-Schaden + 4/7/108-Assets-Streuung weg nach Re-Lift. Welcher Upstream-Fix es war: NICHT belegt. Check: `bash scripts/soak.sh 8 40`.
- P16 Main haengt: `li r11,0x6B` = syscall 107 sys_cond_wait, Timeout 0, niemand signalt. Welche Cond/wer signalt: offen (Annahme: gleiche Klasse wie P11).
- P15 longjmp: lifter macht `blr` in longjmp (func_00A0A57C) zu `return;` -> Kontrolle landet beim Aufrufer statt am setjmp-Site -> LZ-Decoder-Loop laeuft 4 MB ueber Fenster.
  Fix: `scripts/setjmp_patch.py` (host-setjmp je Site, Buffer-Stack). Nach JEDEM Re-Lift neu anwenden. Wirkung: Assets 4 -> 108/7.
- P15 Fundort: `scripts/bbcount.py` (Zaehler auf jedes Label einer Funktion) -> Hot-Loop 49,8 Mio Treffer; Register aendern sich ohne Schreiber im Loop => ein Call war schuld.
- P14 Switch: find_functions folgt nur direkten Branches; `bctr` ueber Jump-Table (246 Tabellen, 1710 Ziele) blieb unlifted. Tabelle steht hinter bctr, Eintraege = signed 32-bit Offsets.
  Folge: 4,4 Mio Busy-Spins auf Queue 0 verschwanden. Check: "unresolved indirect" = 0.
- P13 Kommandozeile: argv ist Array aus 64-bit-Zeigern (CRT liest Stride 8, schreibt 4). `boot_from=gamedata` noetig (bdvd sucht USRDIR/GT.VOL). argv[0] = "/dev_bdvd/PS3_GAME/USRDIR/EMAIN.SELF".
  Relativer Pfad `PDIPFS/K/4D` braucht cellFs-Mapping. Danach PDIPFS gemountet, sys_cond_signal 0 -> 36 pro Boot.
- P12 Skript: Boot-Ende ruft `scripts/gt5p/Application` (liegt in PDIPFS). Ohne Mount: kein Attract-Objekt, kein Frame-Loop. `scripts/rtti.py`: 1442 Vtables, 8314 Virtuals (Binary hat RTTI).
- P12 Idle-Deadlock: Main in sys_cond_wait; Worker-Loop func_00935690 wartet auf sys_event_queue_receive (Queue 5: 1901 Receives, 0 Events); sys_cond_signal 0x aufgerufen.
  Befund: Sender fuer Queue 5 existiert nicht, weil der Code, der ihn anlegt (PDIPFS-Mount/Script), nie lief.
- HLE-Writer: `cellDiscGameGetBootDiscInfo` mit 3 statt 1 Parameter deklariert -> schrieb "BLES00000" in OPD-Tabelle (r4). Zufalls-Crashes -> 6/6 saubere Boots nach Fix (ps3recomp#109).
- HLE-Writer 2: `VM_HLE_INJECT_BASE` (GCM-Labels/Offset-Tabellen, 0x8000 B) lag auf Game-Heap 0x20000000 -> Allocator-Size-Class-Tabelle mit 0xFFFF ueberschrieben -> Livelock (ps3recomp#104).
  Fund: Host-Stores sehen LBP_WW nicht. `GT5P_CANARY=<addr>:<erwartet>` + `GT5P_CANARY_ARM=<call#>[:<page>]` (Page-Guard) klammerte 0x20003000..0x20007000 ein.
- Heap/OOM: Alloc 264 B scheitert (calls=2155 zero=2000), Freelist-Knoten +4 als Groesse gelesen = Fehlschluss; `[flcheck]` Bad-Chains; Ursache war der Runtime-Schreiber, nicht func_006A4400.
- Audit: `scripts/audit_cmp.py` (Signedness/Breite/CR-Feld je Compare), `scripts/audit_branch.py` (Branch-Dekodierung). Beide gruen => Lifter-Verdacht ausgeschlossen.

## Pruefregeln fuer GT6
a) Idle-Deadlock: Warter benennen (Cond/Queue-ID, Syscall-Nr.), dann Sender suchen: wer postet diese Queue / ruft sys_cond_signal? Zaehler pro Queue: Receives vs. Events.
   Nie Wait faken (FLOW_CONDKICK) als Fix. Fehlender Sender = vorgelagerter Code lief nicht.
b) Spiel = Skript: werden PDIPFS-Mount und Script-Load (z.B. Application-Skript) wirklich aufgerufen? Erst Aufruf zaehlen, dann Folgesymptome deuten.
c) Erst Runtime-HLE-Schreiber ausschliessen: Arg-Anzahl jedes HLE-Stubs gegen SDK; HLE-Basis (VM_HLE_INJECT_BASE) gegen Gast-Heap-Mappings; Canary + Page-Guard, LBP_WW ist host-blind.
d) Lifter: setjmp/longjmp (`scripts/setjmp_patch.py`) und Switch/bctr-Tabellen: Gast-Libc longjmp vorhanden? Jump-Table-Ziele gelifted? Unresolved-indirect-Zaehler = 0?
e) Pro Schluss EIN Befehl, der ihn widerlegt (bbcount, audit_*, soak.sh, Canary); ohne Lauf als "Hypothese" markieren. Strukturelle Lesarten waren oft falsch, Messungen selten.
