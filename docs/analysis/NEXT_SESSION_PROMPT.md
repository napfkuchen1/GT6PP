# Start-Prompt naechste Session (kopieren)

```
Arbeite im Haupt-Checkout (kein Worktree), Branch eu-first-build, Repo GT6PP.
Lies zuerst CLAUDE.md und docs/analysis/STATE.md (nur diese beiden). eu-boot-log.md (Hyp. 36-45) und STATE_full_2026-11-22.md nur gezielt nachschlagen.

Ziel: erster Menue-Frame von GT6 EU (nach dem Ladebildschirm). Stand: Snapshot-Werkzeug (PS3_SNAP_AT, scripts/snap_walk.py) steht. Die Game-Loop 568800 laeuft und flippt (~2193 Flips/320 s), zeigt aber nur Legal+Logo+Spinner. Offen (Hyp. 45): pro Track laeuft ein SPURS-Chain "soc-job" (3754 RunJobChain/320 s), aber nur 8 JobGuardNotify geloggt, einmal job 3 rc=-1. Verdacht: Completion-Luecke in der SPURS-Emulation. Snapshot: work/snap_h45.

Aufgabe: STATE.md "Naechster Schritt" abarbeiten:
1. Pruefen, ob/wo das soc-job-Ergebnis gemeldet wird (JobGuardNotify im Runtime-Code third_party/ps3recomp, Spurs-Jobchain-Completion), wer auf das Ergebnis wartet, woher rc=-1 stammt.
2. Wenn eine Completion fehlt: Fix im Runtime-Code (Patch unter patches/), Lauf scripts\probe.ps1 -Name x -Boot notut -Seconds 220, Auswertung scripts\loganalyze.py.

Arbeitsweise: Laeufe nur ueber probe.ps1; Snapshots/Offline-Analyse statt Einzelfeld-Logs; mehrere Hypothesen pro Turn, Turn erst bei Durchbruch, Zeitbox 2 h oder noetiger Entscheidung beenden; STATE.md <5 KB, Zeilen <=200 Zeichen, nach jeder Erkenntnis eine Zeile; max. 2 Fehlversuche pro Ansatz; lokal committen, nicht pushen.
```
