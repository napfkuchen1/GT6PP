Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit14. a8[4] = isNewData der StatGet (korrekt 1, kein HLE-Bug). Save-Kette Arb.11-14 beendet: Term kommt nach 1-2 GAME6-Loads unabhaengig von isNewData (Knob GT6_SAVE_ISNEW0=<substr> in third_party cellSaveData.c, nur lokal, Binary enthaelt ihn). Oracle: 3x GAME6 (3 PDI-Threads), dann AutoSave2 BKUP6, kein Term.
Naechster Schritt: Wer ruft sceNp Term (Thread/Aufrufer, `xref.py --call` + CALLTRACE nur indirekt) und was entscheidet dort (Script-Retry-Zaehler?). Alternativ Guard-Patch auf Term-Aufruf und Lauf bis naechster Blocker (Batch: probe.ps1 je Variante einzeln per `pwsh -File`, Parallel max 2; Start-Process powershell 5.1 scheitert an Get-FileHash).
Nicht wiederholen: LEDGER §4; Save-Prefix, a8[4]/isNewData, AutoLoad2 Return/CBRES, Bypass 89BBC0.
Laeuft noch: nichts.
Lesen: STATE.md (letzte 3 Zeilen).
