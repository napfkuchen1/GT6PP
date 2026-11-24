Ziel: Hauptmenue (C6), EU 1.22 + ps3recomp v0.20.
Stand: Arbeit13. GAME6/BKUP6 = 2 Aufrufe der Script-Native 0x89D59C (Caller 0x8147A0, Namen-Tabelle). Return-bool aus 0x89BBC0 = (ctrl.a8[4]==0); bei uns a8[4]=1 -> false -> Script nimmt BKUP6. Umgehung (Return=1 am Label loc_0089BC18) -> GAME6 2x wie Oracle-Retry, dann sceNp Term (Oracle: 3. GAME6, sysmodule F044, TrophyInit). Baseline: `probe.ps1 -Boot notut -Hdd0Src work\gt6_hdd0_rp -Env "PS3_LANG=en-gb;PS3_GAMEDATA_ROOT=<abs work/_gd_empty>" -Seconds 100`. generated/Binary clean.
Naechster Schritt: (a) Setter von a8[4] (struct ctrl+0xa8, CBResult-aehnlich; xref --field 4 --rw w --in 89B000-89D000: 89BE30/89BE40/89BED8/89BEE4 = Callback-Fill) statisch; (b) ein gebuendelter Batch -Parallel 3 mit Bypass (patch: `ctx->gpr[3]=1;` nach `loc_0089BC18:` in func_0089BBC0, ppu_recomp_018.cpp; danach work/_bk_a13/*_clean.cpp zurueck + touch + Rebuild), Frage: warum Term nach 2. GAME6 statt 3.
Nicht wiederholen: LEDGER §4; Arbeit12 AF5xxx-Callback/Return, CBRES; Arbeit13 Einzelfrage-Laeufe (Overseer: nur Batches).
Laeuft noch: nichts.
Lesen: STATE.md (letzte 2 Zeilen).
