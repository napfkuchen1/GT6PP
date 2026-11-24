# EU GT6 (BCES01893) — session handoff, state 2026-11-21

## State
- Repo: `%USERPROFILE%\Downloads\Games\GT6\ClaudeCode\GT6PP`, branch `eu-first-build` (local, not pushed; origin=upstream xynnpg/GT6PP, fork=napfkuchen1/GT6PP; PR #3 `eu-region-check` open, no PR2).
- Latest commits: `0aaca4c` (patch rsx), `eec0fc2` (rsx fix docs, cap-gt6.ps1, screenshot), `4cd25f8`, `8053531` (cellMusicInitialize2).
- Game boots: boot-2 validator ok (cache fill), cellMusicInitialize2 stubbed, ~36 FPS, language-select dialog visible (`docs/analysis/eu-language-select-dialog.png`): panel, title, 4 menu lines; text readable (commit 34b1e2d), background gradient wrong.

## What is changed (important, partly not in git)
- `third_party/` is gitignored -> backend changes in `rsx_d3d12_backend.c` live as `patches/gt6-rsx-display-tex-zeta.patch` (display-offset textures get a screen copy; `ZETA_FILL` default on, fills unwritten zeta textures with 0xFF). Backups: `work/rsx_d3d12_backend.c.bak_safe`, `.bak_zeta`.
- Cache-fill workaround in gitignored `gt6/generated/ppu_recomp_026.cpp` (docs: `patches/gt6-b5b260-cache-fill.patch.txt`) -> re-apply after re-lift.
- Uncommitted: `third_party/.../ppu_fs.cpp`, `ppu_loader.cpp` (diagnostics), `gt6/src/gen/*` (ppu_hle_nids.cpp, spu_workloads_*.c), `fp_dump.hlsl`, `vp*_dump.hlsl` (debug dumps).

## Test tools
- Build: `powershell -File scripts/build-gt6.ps1` (success = "Built:").
- Run: `scripts/run-gt6.ps1 -Seconds N -Windowed` (logs `work/gt6_run.log(.err)`).
- Render experiment in one call: `scripts/cap-gt6.ps1 -Name x -Env "K=V,K=V" [-Frame 2500 -Seconds 60]` -> `work/cap_x/frame_00/{manifest.txt,backbuffer.png}` + pixel statistics.
- Debug envs: `RT_OFFDBG=1` (surface/display classification), `TEX_MARKEMPTY=1` + `[TEXEMPTY]` (empty textures), `TEX_SAVE`, `TEXFMT`, `EMPTYTEX`, `FP_FORCE`, `RT_CLEARDBG`, `ZETA_FILL=0`, `SCREEN_AS_TEX=0`.
- DRAW_LIMIT bisect is unreliable (frame content varies per run).
- No Python; use sed/heredoc. No `find /`.

## Findings
- GT6 registers display buffers 0x0/0x660000/0xCC0000/0x1320000 and samples them as textures (backdrop). Zeta 0x1980000 is read as a 1440x1080 fmt 0xE5 texture.
- Upstream docs (`rsx-first-draw-fix.md`, `d3d12-draw-readiness.md`) confirm the offset detection; `rpcs3-oracle.md`: RPCS3 in `tools/RPCS3` as visual reference. Upstream has nothing newer (US disc only, black).

## Next steps (order)
1. (done, commit 34b1e2d) Text readable: stencil glyphs + zeta-as-texture, `patches/gt6-rsx-zeta-depth-text.patch` (apply after display-tex-zeta). New: `TEXDUMP="86 88 A8"` dumps textures, manifest shows `zeta=`/`zs=`, `DS_REMAP=0` = old crossbar. Screenshot `eu-language-select-text.png`.
2. Background (open): check op003/004 (vs=6/2, t0=0x04E76980/0x04EADF00 + t3=display 0x1320000); content varies per run, SCREEN_AS_TEX=0 gives magenta/black/white areas. Feedback loop screen copy vs. real image; compare with RPCS3 reference.
3. Update memory `project_gt6pp-eu.md` (cache fix, cellMusic, render fixes).
4. Decide uncommitted diagnostics (commit or discard).
5. Open: cellMusic callback, syscall 327 (stubbed 2x).
- Only with the user's go: push, PR2, README, verify-real-frame (gate 0.8 % < 1 %).

## Rules
Chat in German, concise. Commits as `-c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com`, NO trailers / Co-Authored-By. Never delete (archive), additive changes, verify live, close with "Open points". Never request credentials.

## Update 2026-11-21 (late)
- Background + title color solved (a3 rule per fp, see eu-boot-log). Patches: `gt6-rsx-ignore-stale-a3.patch`, `gt6-rsx-debug-hooks.patch` (apply after display-tex-zeta + zeta-depth-text).
- Diagnostics: root `*.hlsl` dumps moved to `ARCHIV/diag-hlsl/`. `gt6/src/gen/*` not committed (CRLF noise + generated NIDs matching the local third_party). `ppu_fs.cpp`/`ppu_loader.cpp` diagnostics stay local in third_party.
- cellMusic callback / syscall 327: no blocker observed (boot runs to language select) -> no quick win, documented as open.
- RPCS3 with firmware ready in `tools/RPCS3` (reference).
