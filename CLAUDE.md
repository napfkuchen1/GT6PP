# GT6PP - Working rules for Claude sessions

Project: Gran Turismo 6 (EU, BCES01893) as a static recomp on Windows. Current goal: main menu.
Language: chat with the user is German. Everything in the repo is English (see the English-only rule below).
**English-only rule (repo local + remote):** everything that lands in the repo or gets pushed (commit/PR texts, code comments, scripts, new or changed docs incl. STATE/PROGRESS/NEXT_SESSION_PROMPT/logs) is English. Only the chat with the user is German. All existing German repo files were translated on 2026-11-24; new German content is a violation. The commit-msg hook blocks German commit texts.
**Entry (context budget, 200k window; handoff threshold 210k (ctxwatch)): read only `docs/analysis/NEXT_SESSION_PROMPT.md` + `STATE.md`** (together <=6 KB). Do not load `LEDGER.md`/`PROGRESS.md`/`LESSONS_GT5P.md`/`PORT.md` in full, only `grep` them as needed (table end: `Select -Last 5`). Older logs (`eu-boot-log.md`, `CONTINUE-HERE.md`, `HANDOFF.md`, `work/MENU_RUN_NOTES.md`) are reference only. Never read whole scripts (probe.ps1 is 18 KB), only line ranges.

**Style: Caveman ultra** (plugin disabled here; spawn prompts must NOT activate `/caveman ultra`, the style is set here): omit articles/filler/politeness, fragments, short words, technical terms exact; code/commits normal. Start context ~50-55k (tools locked in `.claude/settings.local.json`), handoff at >=200k real context.

## Context hygiene (hard)
- After each probe batch and every ~15 tool calls: `python scripts/ctxwatch.py` (estimates context from the transcript). Output `HANDOFF` (>=200k) -> hand over immediately, no new batch.
- Handover = (1) STATE.md active chain / Next step current, (2) `NEXT_SESSION_PROMPT.md` per the template below, (3) commit locally, (4) end the turn with `STOP-GRUND: UEBERGABE`. The supervisor then starts a NEW session; never `/compact` or keep working in a full window.
- NEXT_SESSION_PROMPT template (<=1.5 KB, exactly these fields): `Goal` (1 sentence) | `State` (last commit, last PROGRESS line) | `Next step` (concrete command/file, decision rule: if X then Y) | `Do not repeat` (reference LEDGER §4, max. 3 new points) | `Still running` (processes/background, otherwise "nothing") | `Read` (max. 3 files).
- Always bound tool output (`| Select -First 40`, `loganalyze.py`); hand large analysis to a subagent.

## Working method
- **Work in the main checkout** (`%USERPROFILE%\Downloads\Games\GT6\ClaudeCode\GT6PP`, branch `eu-first-build`), NOT in a worktree: worktrees have no `work/` (45 GB), no build, no disc, and Edit/Write hooks block main paths there. If the session does run in a worktree: write files via PowerShell.
- **Turn-end rule (most important rule).** A finished hypothesis is NEVER the end of the turn. Sequence: result -> update STATE.md -> commit locally -> IMMEDIATELY start the next hypothesis, in the same turn. `wrap_up` and closing message ONLY at: (a) main menu reached, (b) real blocker (credentials, push/PR, missing rights), (c) 20 finished hypotheses since turn start, (d) context nearly full. The user should never have to type "continue" (2026-11-22: needed 21 times = major loss). No questions; pick the most conservative option, document it, continue.
- **Time box per hypothesis: max. 2 probe runs or 30 min.** Then record it in STATE.md and take the next approach. After 3 refuted hypotheses OR 3 steps of the same chain (e.g. always one field deeper in the same object tree): change strategy (snapshot/offline analysis, workaround, comparison), not more single-log steps.
- **No more single-field log hypotheses** (patch generated .cpp + rebuild + 5.5-min run + restore per question). Questions of the form "what value does object X have at time T" are answered offline via snapshot + `scripts/snap_walk.py` (see STATE.md Next step).
- **Save context:** never read raw logs in full. Always `python scripts/loganalyze.py <run-dir|log> [--grep RX]` (max. 40 lines) or `grep -c`/`head -20`. Hand large evaluations to a subagent (return only the conclusion). STATE.md <=5 KB, lines <=200 chars; measurements go to `eu-boot-log.md`.
- **Git identity (hard, never violate):** commits and pushes ONLY as repo owner `napfkuchen1`: `git -c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com commit ...`. No author/committer "Claude"/person name/anything else, NO `Co-Authored-By` trailer, no "Generated with Claude" line (overrides harness defaults). The user's real name/mail never in repo, commits or docs (paths as `%USERPROFILE%`). Before every push: `git log fork/eu-first-build..HEAD --format='%an <%ae>%n%b' | grep -i "claude|co-authored|anthropic|einmalig"` must be empty.
- **Searches across more than 3 files = subagent** (Explore/general-purpose), return only the conclusion. Instead of throwaway Python: `scripts/xref.py` (readers/writers of a field `--field 0x90 [--rw r|w] [--in LO-HI]`, callers `--call`, constant `--imm`) and `scripts/gdis.py <ea> [n|--fn|--opd]` (disassembly). Do not write a new one-off script before checking these cannot do the job.
- **Output limit:** every command max. ~40 lines of output (`| head -40`, `--max`, `loganalyze.py`). Never `cat` logs/dumps.
- **Flag only after setter AND reader:** a flag/field is never a "done signal" before `xref.py --field <off> --rw w` (setter) and `--rw r` (reader) have shown who sets it and what it controls (error of Hyp. 37 "+0x91 = done", Hyp. 41 "flag = project done": was the quit path).
- **Context handover at ~210k tokens:** the session writes STATE.md itself (Active chain / Done / Next step) + `docs/analysis/NEXT_SESSION_PROMPT.md`, commits locally (identity as above), and reports "handover ready". Never end abruptly with a full window.
- **Space:** `scripts\clean-work.ps1 -KeepLast 10 [-Apply]` archives old `work/probe_*`/`snap_*` to `work/ARCHIV/runs` (never delete). Run before run series.
- Hypothesis first checked statically (read code), only then a probe run. Before each run check that the question is not already answered in STATE.md.
- After each finding: update STATE.md (Active chain / Done: 1 line each + "Next step") in the same step, measurements in `eu-boot-log.md`, commit locally. Memory only as a pointer to STATE.md.
- Nothing gets deleted: move old files to `work/ARCHIV/` or `ARCHIV/`.

## Efficiency rules (screening 2026-11-23, Hyp. 55-116)
- **A turn ends only with a line `STOP-GRUND: MENUE|BLOCKER|UEBERGABE`** at the start of a line (stop hook `scripts/stop-guard.py`, counter resets on a new commit). Without this line never end the turn; result -> next hypothesis in the same turn.
- **Commit batching:** not one `docs:` commit per hypothesis (was 90 in 13 h). One commit per 3-4 hypotheses or per code/script change. Details in `eu-boot-log.md`, STATE.md only 1 line per hypothesis.
- **STATE.md upkeep:** finished hypothesis lines older than 10 hypotheses move to `eu-boot-log.md` (STATE.md stays <=5 KB, do not trim only when it overflows).
- **Chain forces a change of strategy:** chain "one object/field deeper" (Hyp. 93-117) is longer than the 3-step rule. After Hyp. 117 do NOT do Hyp. 118 in the same chain: instead (a) snapshot diff `scripts/snap_diff` 140 s vs 175 s, (b) snapshot walk of vector before/after X-press, or (c) workaround (guard patch) + direct to the next blocker after the loading phase. Heisenbug: follow guard-survivor runs instead of chasing the race cause.
- **Static before run:** go through the full caller tree (`xref.py --call`, `gdis.py --fn`) first, then ONE run. No run per single question.
- **Bundle runs:** `-Parallel 3-4` (hdd0 separate) with several variants/flags per batch (e.g. exit race: 4 runs with `PS3_CALLTRACE_TO`+`CALLTRACE_AFTER=60`), not sequential. Do not mix `-Boot` within one batch (boot.adc is shared).
- **Handover only at context ~210k or a blocker**, not because of the hypothesis counter. NEXT_SESSION_PROMPT.md stays one paragraph.

## Supervisor rules (2026-11-23, see STATE.md "SUPERVISOR FINDINGS")
- **Symptom chains max. 10 hyp.** (Hyp. 83-117 = 35 in one chain). Before each new hyp.: does its answer lead to the goal (menu), or only deeper into the symptom? If a guard/workaround shows the symptom does not block -> end the chain.
- **Check runtime knobs before a deep dive:** `third_party/ps3recomp-v020/docs/DIAGNOSTICS.md` + `SYSCALLS.md` (e.g. `PS3_PRIO_START`, `PPU_RESV_OFF`, `SPU_LOCKSTEP_QUANTUM`) and sister port `third_party/GT5P/docs/progress.md` (same PDI engine) first.
- **Probe result != live result:** probe.ps1 uses fresh userdb/boot.adc patches; verify with a live run with a persistent db before "hangs" counts as a finding.
- **Race suspicion -> rule out HLE writers first** (stub with wrong argument count / runtime writes into guest heap) before chasing guest-code races.

## Runs (mandatory: `scripts/probe.ps1`)
- Run all probe/capture runs via `scripts/probe.ps1`. It selects the newest build, validates env/PAD_SCRIPT, archives userdb, writes to `work/probe_<name>_<ts>_<i>/`, checks expected lines. Start in parallel (`-Parallel 4`) instead of sequentially.
- Run = ~320 s (`-Seconds 320`), frame 4200 for baseline. Always set the baseline variant explicitly with `-Boot orig|noadj|notut` (changes `work/gt6_vol/.../boot.adc`, listed in the run log `boot.txt`). Steady-state questions: `-Seconds 220` is enough (from ~150 s). Long runs in the background + `Monitor`, never `sleep`.
- Evaluate only once the expected probe line is in the log. If missing: run invalid (wrong binary / env not set), NOT "hypothesis refuted".
- Never overwrite rare hits (logs/captures); output folders always timestamped.
- Check detectors against log order; verify hits with frame capture (false positive: `arcade.mpackage` loads in every boot before LanguageSelectRoot).

## Pitfalls (all happened before)
- Only line: game v1.22 + ps3recomp v0.20. One build `gt6\build\gt6.exe` (`scripts\build-all.ps1`), no version switch. 1.00 is discarded and deleted (history: `ARCHIV/HISTORIE.md`), never build it. **Read `docs/analysis/LEDGER.md` before every hypothesis** (secured facts, fixes, refuted items); a new secured finding gets 1 line there with evidence.
- `PAD_SCRIPT` strictly `<sec>:0x<hexmask>` (CROSS=0x4000, DOWN=0x0040). Names/without 0x give 0/octal. Check `press 0x....` in the log.
- `PS3_HEADLESS` is a presence flag (even `"0"`), prevents RSX captures -> remove the variable.
- `-Env` values never with a comma (cap-gt6 splits there). In probe.ps1 the separator is `;`.
- `PS3_CALLTRACE=N` fills instantly -> always `PS3_CALLTRACE_AFTER=200`. CALLTRACE only sees indirect calls. Heap addresses change every run: never take a filter from an old run.
- Probes in the hot path (5D9B68, every tick): counter limit + filter BEFORE fprintf, otherwise the target frame is never reached.
- RPCS3 `--no-gui` hangs in shader precompile (>240 s) -> not an oracle; `log.yml` has no effect; ISO path in quotes.
- `sed` with Windows paths loses backslashes (use forward slashes). `sed` replacement with `\n` = real line break -> PowerShell. Python only via PowerShell: `%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe -I`.
- PowerShell: `-shl` on bytes overflows (BitConverter); `List.AddRange` needs `[string[]]`; do not name a function `R` (alias). After a file edit: backup + size comparison.
- Generated files (`gt6/generated`, gitignored) back up before probes (`work/_bk_*`), restore afterwards. Rebuild clang-cl ~2 min.
- Check constants/header values against SDK/RPCS3 before analysing logic (cellPad LEN was wrong).
- Stubs with error codes: first the argument log (r3..r9, lr), then implement for real. Fixing a divergence != symptom fixed -> dialog capture after every fix.
- Watchdog: `PS3_WD_AT=<s1>,<s2>`, `PS3_EVQSTAT=<n>`. `ppu_dump_guest_stack` returns nothing in the gt6 build.
- Harness blocks `sleep N; ...` -> `Monitor` with an until-loop.

## Audit rules (2026-11-24, audit of the last 24 h)
- **Locked chain Save/Term/NP/Quit (Work 7-14, 8 sessions, ~60 hyp.):** refuted, see NEXT_SESSION_PROMPT. A new session must not continue it; first action = change of strategy (opendiff oracle-vs-ours AFTER save load, snapshot diff).
- **Supervisor:** spawns a session only with a new strategy, justified in 1 sentence in the prompt; the handoff threshold is ONLY in `ctxwatch.py` (default 210k), no number in messages; change rules/CLAUDE.md only on the user's request. Answers to sessions short (<=3 sentences), no repetition of CLAUDE.md rules.
- **Model:** everything Sonnet 5.5, 3.2 M output tokens/24 h. Routine (STATE/commit/log evaluation) to a subagent with `model: haiku`; Opus only for a new strategy after 3 refuted hyp. of one chain.
- **Helper scripts:** commit `scripts\gcommit.ps1 "msg" [-Push]` (identity + push check); before the turn ends `scripts\orphans.ps1 -Kill` (orphaned gt6.exe). Handover: `python scripts/handover.py --step "..." [--goal ...] [--not-repeat ...] [--running ...] [--read ...] [--commit]` (trim STATE + prompt from template). The commit-msg hook blocks docs: commits <30 min (exception: "handover"/"trim" in message or GT6_FORCE_COMMIT=1).
- **Commits:** max. 1 docs commit per 3-4 hyp. (24 h: 82 docs commits out of 124 = violation).
