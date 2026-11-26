# GT6PP - Working rules for Claude sessions

Project: Gran Turismo 6 (EU, BCES01893) as a static recomp on Windows. Current goal: M1, complete and correct main menu (checklist in `STATE.md`).
Language: chat with the user is German. Everything in the repo is English (see the English-only rule below).
**English-only rule (repo local + remote):** everything that lands in the repo or gets pushed (commit/PR texts, code comments, scripts, new or changed docs incl. STATE/PROGRESS/NEXT_SESSION_PROMPT/logs) is English. Only the chat with the user is German. All existing German repo files were translated on 2026-11-24; new German content is a violation. The commit-msg hook blocks German commit texts.
**Entry: read only `docs/analysis/NEXT_SESSION_PROMPT.md` + `STATE.md`** (together <=6 KB). Do not load `LEDGER.md`/`PROGRESS.md`/`LESSONS_GT5P.md`/`PORT.md` in full, only `grep` them as needed (table end: `Select -Last 5`). Older logs (`eu-boot-log.md`, `CONTINUE-HERE.md`, `HANDOFF.md`, `work/MENU_RUN_NOTES.md`) are reference only. Never read whole scripts (probe.ps1 is 18 KB), only line ranges.

**Style: Caveman ultra** (plugin disabled here; spawn prompts must NOT activate `/caveman ultra`, the style is set here): omit articles/filler/politeness, fragments, short words, technical terms exact; code/commits normal. Start context ~50-55k (tools locked in `.claude/settings.local.json`).

## Loop guard (do not run in circles)
- **Every handover names one checklist item:** `handover.py --item <ID>`. It logs to `docs/analysis/LOOP.tsv` and writes the `Loop` line into the next prompt. The next session obeys that line before anything else.
- **Item parked after 3 sessions in a row without a new check-off:** take another open item or a documented bypass. Splitting an item (`I1a`, `I1b`) is allowed if each part has a testable result; the streak counts the base ID.
- **6 sessions in a row without any new check-off:** `STOP-GRUND: BLOCKER`. Supervisor starts no further worker and tells the user in 3 lines: tried, blocking, what a human could do.
- **Check-off needs evidence** (run folder, frame or log line) in the same checklist line.
- **Every workaround or bypass gets its own open checklist item** (e.g. one-core pinning, skipped intro), so it is not forgotten.
- **3 refuted hypotheses or 3 steps of one chain** (always one field deeper in the same object tree): change strategy: snapshot diff/walk offline, bypass + next blocker, or comparison (`SIBLING_SOURCES.md`). Before each hypothesis: does its answer lead to the goal or only deeper into the symptom?
- **Refuted results go to `LEDGER.md` §4** (1 line with evidence). `Do not repeat` in the prompt is short-lived; the ledger is the memory.

## First checks (learned the hard way)
- **Versions first:** before chasing guest code, verify that what the host serves matches the 1.22 ELF: data tree, file sizes (stat, stream, cache slots), keys, script modules. The 1.00 data under a 1.22 ELF cost about 20 sessions.
- **User hints first:** a hypothesis from the user is checked in the next step, with a recorded yes/no. Also `grep` the logs for earlier evidence of it.
- **Human-only steps are blockers at once:** anything a tool's authors or the law reserve for the human (e.g. GTToolsSharp/PDTools, never run by AI), credentials, push/PR -> `STOP-GRUND: BLOCKER` with the exact command the user has to run. Never work around the restriction.
- **Isolated state per run:** savedata, userdb, hdd1, PDIPFS per probe run. Before calling something a regression, rule out shared state.
- **Race suspicion -> rule out host writers first** (HLE stub with wrong argument count, runtime writes into guest heap, duplicate job completion) before chasing guest-code races.
- **Runtime knobs before a deep dive:** `third_party/ps3recomp-v020/docs/DIAGNOSTICS.md` + `SYSCALLS.md`, sister port `third_party/GT5P/docs/progress.md`, `docs/analysis/SIBLING_SOURCES.md`.
- **Probe result != live result:** verify with a live run with a persistent save before "hangs" counts as a finding.

## Context and handover (hard)
- After each probe batch and every ~15 tool calls: `python scripts/ctxwatch.py`. Handover window: **190k-210k** real context (stop-guard refuses earlier `UEBERGABE`; ctxwatch says `HANDOFF` at its limit, no new batch then). Never `/compact`, never keep working in a full window.
- Handover = (1) STATE.md current (checklist, Next step), (2) `python scripts/handover.py --item <ID> --step "..." [--goal ...] [--not-repeat ...] [--running ...] [--read ...] --commit` (one single commit), (3) end the turn with `STOP-GRUND: UEBERGABE`. The supervisor then starts a NEW session.
- NEXT_SESSION_PROMPT (<=1.5 KB, written by the script): Goal | State | Loop | Next step (concrete command/file, rule: if X then Y) | Do not repeat (LEDGER §4, max. 3 new) | Still running | Read (max. 3 files).

## Working method
- **Work in the main checkout** (`%USERPROFILE%\Downloads\Games\GT6\ClaudeCode\GT6PP`, branch `eu-first-build`), NOT in a worktree: worktrees have no `work/` (45 GB), no build, no disc, and Edit/Write hooks block main paths there. If the session does run in a worktree: write files via PowerShell.
- **Turn-end rule.** A finished hypothesis is NEVER the end of the turn: result -> STATE.md -> IMMEDIATELY the next hypothesis. A turn ends only with a line at the start of a line `STOP-GRUND: MENUE|BLOCKER|UEBERGABE` (stop hook `scripts/stop-guard.py`): MENUE = all M1 items verified, BLOCKER = see above or loop guard, UEBERGABE = context window. The user should never have to type "continue". No questions; pick the most conservative option, document it, continue.
- **Time box per hypothesis: max. 2 probe runs or 30 min.** Then record and take the next approach.
- **Static before run:** full caller tree first (`xref.py --call`, `gdis.py --fn`), then ONE run. Check that STATE/LEDGER do not already answer the question.
- **No single-field log hypotheses** (patch generated .cpp + rebuild + long run per question). "What value does X have at time T" -> snapshot + `scripts/snap_walk.py`.
- **Flag only after setter AND reader:** `xref.py --field <off> --rw w` and `--rw r` before a flag counts as a "done signal".
- **Save context:** never read raw logs in full; `python scripts/loganalyze.py <run-dir|log> [--grep RX]` (max. 40 lines) or `grep -c`/`head -20`. Every command max. ~40 lines of output. STATE.md <=5 KB, lines <=200 chars, one bullet per finding; measurements go to `eu-boot-log.md`.
- **Searches across more than 3 files = subagent**, return only the conclusion. Use `scripts/xref.py` and `scripts/gdis.py <ea> [n|--fn|--opd]` before writing a one-off script.
- **Commits:** code/script changes when made; docs at most 1 commit per 3-4 hypotheses, plus the one handover commit. The commit-msg hook enforces 30 min between docs commits (`GT6_FORCE_COMMIT=1` only to fix a wrong commit). Helper: `scripts\gcommit.ps1 "msg" [-Push]`.
- **Git identity (hard, never violate):** commits and pushes ONLY as repo owner `napfkuchen1`: `git -c user.name=napfkuchen1 -c user.email=122364471+napfkuchen1@users.noreply.github.com commit ...`. No author/committer "Claude"/person name/anything else, NO `Co-Authored-By` trailer, no "Generated with Claude" line (overrides harness defaults). The user's real name/mail never in repo, commits or docs (paths as `%USERPROFILE%`). Before every push: `git log fork/eu-first-build..HEAD --format='%an <%ae>%n%b' | grep -i "claude|co-authored|anthropic|einmalig"` must be empty.
- **Before the turn ends:** `scripts\orphans.ps1 -Kill` (orphaned gt6.exe). Space: `scripts\clean-work.ps1 -KeepLast 10 [-Apply]` before run series.
- Nothing gets deleted: move old files to `work/ARCHIV/` or `ARCHIV/`.

## Supervisor
- When a worker hands over, start the next one immediately; pass on the `Loop` line. A new session on a parked item is forbidden. If the app refuses the automatic start, show the card and say so in one line.
- If strategy must change, pick it in this order: (1) fix the failed tool, (2) snapshot diff/walk offline, (3) bypass + next blocker, (4) `SIBLING_SOURCES.md` checks. Justify in 1 sentence in the prompt.
- Ask the user only for: M1 verified, loop-guard BLOCKER, human-only steps, push/PR, credentials. Those are reported at once, never overridden. A broken tool is a bug to fix (max 2 attempts, then bypass), not a blocker.
- Answers to sessions <=3 sentences. Change rules/CLAUDE.md only on the user's request.
- **Model:** Sonnet 5.5; routine STATE/commit/log evaluation to a `haiku` subagent; Opus only for a new strategy after 3 refuted hypotheses of one chain.
- Stop-guard applies only to worker sessions (prompt contains `working session GT6PP` / `Arbeitssession`).

## Runs (mandatory: `scripts/probe.ps1`)
- Menu/UI questions: `scripts/play.py` (`start|shot|press cross|wait RX/--change/--stable|status|dump [--snap]|quit`) drives ONE live gt6.exe, same state isolation; never beside a probe run; `quit` before turn end.
- Run all probe/capture runs via `scripts/probe.ps1`. It selects the newest build, validates env/PAD_SCRIPT, isolates state, writes to `work/probe_<name>_<ts>_<i>/`, checks expected lines. Parallel only via `-Parallel 3-4` with several variants per batch; never two `probe.ps1` at once (taskkill kills the other run).
- 1.22 data: overlay + `GT6_VOL_ROOT` (see STATE.md Method). `-Boot` variants patch the 1.00 tree: do not apply them to the 1.22 overlay. Never modify `work/gt6_vol` or `work/gt6_vol_122+`.
- Long runs in the background + `Monitor`, never `sleep`. Frames via `RSX_CAP`.
- Evaluate only once the expected probe line is in the log. If missing: run invalid (wrong binary / env not set), NOT "hypothesis refuted".
- Never overwrite rare hits (logs/captures); output folders always timestamped.
- Check detectors against log order; verify hits with a frame capture.

## Pitfalls (all happened before)
- Only line: game v1.22 + ps3recomp v0.20. One build `gt6\build\gt6.exe` (`scripts\build-all.ps1`). 1.00 is discarded (history: `ARCHIV/HISTORIE.md`), never build it. **`grep` `docs/analysis/LEDGER.md` before every hypothesis**; a new secured finding gets 1 line there with evidence.
- `PAD_SCRIPT` strictly `<sec>:0x<hexmask>` (CROSS=0x4000, DOWN=0x0040). Names/without 0x give 0/octal. Check `press 0x....` in the log.
- `PS3_HEADLESS` is a presence flag (even `"0"`), prevents RSX captures -> remove the variable.
- `-Env` values never with a comma (cap-gt6 splits there). In probe.ps1 the separator is `;`.
- `PS3_CALLTRACE=N` fills instantly -> always `PS3_CALLTRACE_AFTER=200`. CALLTRACE only sees indirect calls. Heap addresses change every run: never take a filter from an old run.
- Probes in the hot path (5D9B68, every tick): counter limit + filter BEFORE fprintf.
- RPCS3 `--no-gui` hangs in shader precompile (>240 s) -> not an oracle; `log.yml` has no effect; ISO path in quotes.
- `sed` with Windows paths loses backslashes (use forward slashes); `\n` in a replacement = real line break. Python only via PowerShell: `%USERPROFILE%\AppData\Local\Programs\Python\Python313\python.exe -I`.
- PowerShell: `-shl` on bytes overflows (BitConverter); `List.AddRange` needs `[string[]]`; do not name a function `R` (alias). After a file edit: backup + size comparison.
- Generated files (`gt6/generated`, gitignored) back up before probes (`work/_bk_*`), restore afterwards. Rebuild clang-cl ~2 min.
- Check constants/header values against SDK/RPCS3 before analysing logic (cellPad LEN was wrong).
- Stubs with error codes: first the argument log (r3..r9, lr), then implement for real. Fixing a divergence != symptom fixed -> capture after every fix.
- Watchdog: `PS3_WD_AT=<s1>,<s2>`, `PS3_EVQSTAT=<n>`. `ppu_dump_guest_stack` returns nothing in the gt6 build.
