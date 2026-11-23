# Naechste Session GT6PP (Stand Hyp. 89 (REALFLAG default, Dialog ok, noadj quittet))
Lies `docs/analysis/STATE.md`, dann CLAUDE.md-Regeln. Weiter mit Hyp. 90: Was passiert bei ~52 s im pinned Lauf (work/_aff.ps1), PS3_SNAP_AT=51, siehe STATE.md
Kontext: tid 1 haengt im Event-Wait 568C94->A21D50 (obj 0x7FEAC018). Servicer 568A0C laeuft als Fiber (Entry A2F464),
Zustand obj+0x48 (1..6). Probe-Setup: `$env:GT6_BUILD_DIR='gt6\build-v020'`, `-Env 'GT6_REALFLAG=1;PS3_FIBERLOG=1'`.
Uncommitted-Reste: SDK-Klon `third_party/ps3recomp-v020` cellFiber.c (Patch in patches/gt6-v020-fiberlog.patch).
Hinweis: Hypothesen-Limit pro Turn = 8, danach Uebergabe.
Hinweis: "func_XXXX+0xNNN" im Log ist KEIN Byte-Offset (Statement-Index); Aufrufstelle per xref --call / lr suchen, nicht gdis(func+off).

Hinweis Peer-Session (Workflow-Optimierung): Kette Hyp. 63-89 ist eine Kette -> Strategiewechsel. Vorschlaege:
(1) Snapshot-Diff 140 s vs 175 s (snap_walk) fuer die Frame-Stagnation ab ~9000/159 s (REALFLAG=0).
(2) 3 Varianten orig/noadj/notut je 200 s, Flip-Rate pro 10 s vergleichen.
(3) GT6_UNBUF=1 etc. gegen v0.20-Flip-Pacing testen.
