Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit10. sceNpTerm-Aufrufer belegt (NP_TERM_BT=1): synchron in tid1 via main-Stufe 13C44 <- A52140 <- A7E6BC <- A7BA60 (Run-Fn) -> A2FFCC -> A2F0EC -> AA41FC -> AA55FC -> A5C070 -> A7479C -> A746E8 -> 9AD1DC (native PDINetwork.finalize) -> A088DC -> B4AD4C Term. Script/Projekt ruft finalize kurz nach AutoLoad (gtauto.mpackage laedt davor). Oracle: kein finalize, main schlaeft 76->106 s.
Naechster Schritt: wer/warum ruft finalize: HOSTBT-Tiefe/Frames bei A5C070/A7479C ansehen (gdis, Aufrufer-Slot), welches Script-Projekt (gtauto/boot) die Methode 'finalize' ruft; in adch-Dump (tools/adch_disasm.py, alle Projekte grep 'finalize') Bedingung davor finden. Wenn Bedingung = Netz/Np-Status OFFLINE: Oracle-Status pruefen (sceNpManagerGetStatus bei uns OFFLINE).
Nicht wiederholen: Save-Prefix, Frame-Pacing, AFDFC0, CALLTRACE_TO 1198C/9B0098/9AFCE4 (0 Treffer, Term-Pfad ist nicht 1198C), Z.102-Hypothese.
Laeuft noch: nichts.
Lesen: STATE.md, eu-boot-log.md "Arbeit10".
