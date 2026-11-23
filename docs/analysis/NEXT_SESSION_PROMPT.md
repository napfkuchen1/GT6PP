# Naechste Session GT6PP (Stand Hyp. 87 (REALFLAG default, Dialog ok, noadj quittet))
Lies `docs/analysis/STATE.md`, dann CLAUDE.md-Regeln. Weiter mit Hyp. 88: malloc-NULL-Check in 88B9D4, pinned Lauf work/_aff.ps1, siehe STATE.md
Kontext: tid 1 haengt im Event-Wait 568C94->A21D50 (obj 0x7FEAC018). Servicer 568A0C laeuft als Fiber (Entry A2F464),
Zustand obj+0x48 (1..6). Probe-Setup: `$env:GT6_BUILD_DIR='gt6\build-v020'`, `-Env 'GT6_REALFLAG=1;PS3_FIBERLOG=1'`.
Uncommitted-Reste: SDK-Klon `third_party/ps3recomp-v020` cellFiber.c (Patch in patches/gt6-v020-fiberlog.patch).
Hinweis: Hypothesen-Limit pro Turn = 8, danach Uebergabe.
Hinweis: "func_XXXX+0xNNN" im Log ist KEIN Byte-Offset (Statement-Index); Aufrufstelle per xref --call / lr suchen, nicht gdis(func+off).
