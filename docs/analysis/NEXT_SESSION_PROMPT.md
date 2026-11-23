Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit8. AutoLoad2 wird erreicht (GAME6 -4, BKUP6 -4 / mit Alt-Save LOAD complete), dann sceNp Term statt LoadModule 0xF044 + sceNpTrophyInit (Oracle). C1 FAIL. Details STATE.md Arbeit8-Zeilen.
Naechster Schritt: (1) Caller von sceNpTerm nach LOAD complete finden (Snapshot work/snap_a8s50 stack/threads oder PS3_CALLTRACE_TO), Entscheidungswert: Save-Ergebnis obj+0xb0 (Wrapper AF5620/AF5704). Wenn Term aus Save-Fehlerpfad: Alt-Saves (gamedata/ = 1.00-Format GT6.N) gegen Oracle-Format GT6_1.N 16 MB pruefen; Oracle-Retry (3x neue Threads) nachbilden. (2) sonst Snapshot-Diff vertiefen.
Nicht wiederholen: LEDGER §4; GT6_SAVE_CBRES/NODATA-Variante (kein Effekt), leeres Save-Root (gleiche Term-Folge), Prefix-String-Suche im RAM (GT6_1 nicht vorhanden).
Laeuft noch: nichts.
Lesen: STATE.md, eu-boot-log.md Z.217 (grep).
