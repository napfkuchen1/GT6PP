# Start-Prompt naechste Session (kopieren)

```
Arbeite im Haupt-Checkout (kein Worktree), Branch eu-first-build, Repo GT6PP.
Lies zuerst CLAUDE.md und docs/analysis/STATE.md (nur diese beiden). STATE_full_2026-11-22.md nur nachschlagen.

Ziel: Ladebildschirm-Haenger nach dem Boot bei GT6 EU aufloesen (Hauptmenue/gtmode erreichen).
Aufgabe: Der "Naechste Schritt" aus STATE.md - Snapshot-Werkzeug bauen statt weiterer Einzelfeld-Log-Hypothesen:
1. PS3_SNAP_AT=<s> in der ps3recomp-Runtime (Gast-RAM, Thread-Register/Stacks, Sync-Objekt-Tabellen nach work/snap_<ts>/; Patch unter patches/).
2. scripts/snap_walk.py (Objekt am Zeiger, vtable/OPD ueber ELF aufloesen, Felder dumpen, [callee+0x14] -> vtable+0x54 disassemblieren).
3. Ein Lauf: scripts\probe.ps1 -Name snap -Boot notut -Seconds 320 -Env "PS3_SNAP_AT=200", danach alles offline analysieren.
Zeitbox 2 h. Scheitert der Bau: Fallback Hyp. 36 (Log in 0x9B89D8 vor bctrl 0x9B8A44, Cap pro Methodenadresse).

Arbeitsweise (aus CLAUDE.md, hier nochmal hart):
- Laeufe nur ueber scripts\probe.ps1, Auswertung ueber scripts\loganalyze.py (nie Roh-Logs in den Kontext).
- Eine Hypothese = eine Messung; nach jeder Erkenntnis STATE.md um EINE Zeile aktualisieren (Datei <5 KB, Zeilen <=200 Zeichen).
- Nicht nach jeder Hypothese den Turn beenden; erst stoppen, wenn Snapshot-Ergebnis vorliegt, die Zeitbox endet oder eine Nutzerentscheidung noetig ist.
- Max. 2 Fehlversuche pro Ansatz, dann Strategiewechsel benennen statt weiterzupatchen.
- Am Ende: STATE.md, CHANGELOG, Memory synchron; "Offene Punkte" nennen. Nicht pushen ohne Aufforderung.
```
