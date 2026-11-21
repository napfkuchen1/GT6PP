# EU GT6 (BCES01893) — Session-Handoff, Stand 2026-11-21

## Zustand
- Repo: `C:\Users\Daniel\Downloads\Games\GT6\ClaudeCode\GT6PP`, Branch `eu-first-build` (lokal, nicht gepusht; origin=upstream xynnpg/GT6PP, fork=napfkuchen1/GT6PP; PR #3 `eu-region-check` offen, kein PR2).
- Letzte Commits: `0aaca4c` (Patch rsx), `eec0fc2` (rsx-Fix-Doku, cap-gt6.ps1, Screenshot), `4cd25f8`, `8053531` (cellMusicInitialize2).
- Spiel bootet: Boot-2-Validator ok (Cache-Fill), cellMusicInitialize2 gestubbt, ~36 FPS, Sprachauswahl-Dialog sichtbar (`docs/analysis/eu-language-select-dialog.png`): Panel, Titel, 4 Menüzeilen; Text = Blöcke, Hintergrund-Verlauf (gelb/grün/cyan) vermutlich falsch.

## Was geändert ist (wichtig, teils nicht im Git)
- `third_party/` ist gitignored -> Backend-Änderungen `rsx_d3d12_backend.c` liegen als `patches/gt6-rsx-display-tex-zeta.patch` (Display-Offset-Texturen bekommen Screen-Kopie; `ZETA_FILL` default an, füllt ungeschriebene Zeta-Texturen mit 0xFF). Backups: `work/rsx_d3d12_backend.c.bak_safe`, `.bak_zeta`.
- Cache-Fill-Workaround in gitignored `gt6/generated/ppu_recomp_026.cpp` (Doku: `patches/gt6-b5b260-cache-fill.patch.txt`) -> nach Relift neu anwenden.
- Uncommitted: `third_party/.../ppu_fs.cpp`, `ppu_loader.cpp` (Diagnose), `gt6/src/gen/*` (ppu_hle_nids.cpp, spu_workloads_*.c), `fp_dump.hlsl`, `vp*_dump.hlsl` (Debug-Dumps).

## Test-Werkzeuge
- Build: `powershell -File scripts/build-gt6.ps1` (Erfolg = "Built:").
- Run: `scripts/run-gt6.ps1 -Seconds N -Windowed` (Logs `work/gt6_run.log(.err)`).
- Render-Experiment in einem Call: `scripts/cap-gt6.ps1 -Name x -Env "K=V,K=V" [-Frame 2500 -Seconds 60]` -> `work/cap_x/frame_00/{manifest.txt,backbuffer.png}` + Pixelstatistik.
- Debug-Envs: `RT_OFFDBG=1` (Surface/Display-Klassifikation), `TEX_MARKEMPTY=1` + `[TEXEMPTY]` (leere Texturen), `TEX_SAVE`, `TEXFMT`, `EMPTYTEX`, `FP_FORCE`, `RT_CLEARDBG`, `ZETA_FILL=0`, `SCREEN_AS_TEX=0`.
- DRAW_LIMIT-Bisect ist unzuverlässig (Frame-Inhalt variiert pro Lauf).
- Kein Python; sed/heredoc nutzen. Kein `find /`.

## Erkenntnisse
- GT6 registriert Display-Buffer 0x0/0x660000/0xCC0000/0x1320000 und sampelt sie als Textur (Backdrop). Zeta 0x1980000 wird als 1440x1080 fmt 0xE5 Textur gelesen.
- Upstream-Doku (`rsx-first-draw-fix.md`, `d3d12-draw-readiness.md`) bestätigt Offset-Erkennung; `rpcs3-oracle.md`: RPCS3 in `tools/RPCS3` als visuelle Referenz. Upstream hat nichts Neueres (nur US-Disc, schwarz).

## Nächste Schritte (Reihenfolge)
1. Text: Glyph-Texturen prüfen (0x88 8x8, 0x86 128x128, 0xA8 36x36) via `TEX_SAVE`/`TEXFMT`; warum Blöcke statt Glyphen.
2. Hintergrund-Verlauf: Rückkopplung Screen-Kopie vs. echtes Bild; mit RPCS3-Referenz vergleichen.
3. Memory `project_gt6pp-eu.md` aktualisieren (Cache-Fix, cellMusic, Render-Fixes).
4. Uncommitted Diagnosen entscheiden (committen/verwerfen).
5. Offen: cellMusic-Callback, Syscall 327 (2x gestubbt).
- Nur mit Daniels Go: Push, PR2, README, verify-real-frame (Gate 0,8 % < 1 %).

## Regeln
Deutsch, knapp. Commits als `-c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com`, KEINE Trailer/Co-Authored-By. Nie löschen (archivieren), additive Änderungen, live verifizieren, Abschluss mit "Offene Punkte". Nie Credentials anfordern.
