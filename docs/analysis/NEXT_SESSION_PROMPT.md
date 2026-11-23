Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Quit nur maskiert. main()=0x14010 Stufe 146E8 (Main-Loop while(!AD2778)) endet sofort, weil Task-Klasse 0x15DD3E0 (vtbl[2]=AFDFC0) "fertig" meldet: Struct 0x179ED20 byte0&&byte1 frueh 1 (byte0 via AFE200, byte1 via AFE1C8=(C6390C==0)). Details STATE.md MAIN-LOOP.
Naechster Schritt: AFE190: Strings aus AF32FC() (0x179A1E8) und obj+0x48 loggen (C6390C=strcmp, byte1=gleich), AF32FC lesen/Setter xref; EIN Lauf mit fprintf in generated 023 (func_00AFE190/AFE2A0). Wenn Wert falsch -> HLE fixen, dann Capture C1.
Nicht wiederholen: LEDGER Quit-Flag/IsExitGame; AC746C-Wait-Skip; BFF0A0/BFF578/C1F4C8 harmlos; main-Stufen 143E8/141E8/91E464 keine Loops.
Laeuft noch: nichts. generated clean, Binary mit Diagnose -> build-all.ps1 vor Baseline.
Lesen: STATE.md.
