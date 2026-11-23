Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit8 (ctx ~170k). AutoLoad2 erreicht; Oracle laeuft danach LoadModule 0xF044 + sceNpTrophyInit (Kette 10BDD20<-B36E00<-B36F80<-B37980 / B376E4<-B359CC), bei uns nie (CALLTRACE_TO B37980/B359CC = 0 Treffer, 60 s). sceNpTerm bei uns = Prozess-Teardown (main-Return, bekannt). C1 FAIL.
Naechster Schritt: Wer ruft B37980/B359CC im Oracle? Oracle-Log (work/oracle/RPCS3_user_oracle.log) Threads T025/T034 ab Z.155344: Thread-Erzeuger/LR; dann Gast-Pfad dorthin statisch (xref/gdis), pruefen welche Bedingung bei uns fehlt (HLE-Rueckgabewert davor). Wenn Wurzel ueber vtable: snap_walk find32 0x00B37980.
Nicht wiederholen: Save-Return-Varianten (CBRES/NODATA), leeres Save-Root, Prefix-String-Suche, NP-Term-Bedingung.
Laeuft noch: nichts.
Lesen: STATE.md.
