# Code Review Notes

Central log for review findings, follow-up items, and resolved issues. The Implementer must check this file before merging changes or handing work to the user.

## How to Use
- **Code Reviewer** – Append dated sections using the template in `agents/code_reviewer.md`. List blockers first, then major/minor findings. Note any tests that need to be rerun.
- **Implementer** – Address each item, recording the fix or rationale in-line. Strike through resolved bullets or add a short response (`_Resolved in <commit>_`).
- **Project Coordinator** – Reference this log in `production_notes.md` so project histories stay in sync.

## Open Items
- None - all findings resolved as of 2025-10-31.

## Resolved Archive
- Add dated notes here once issues are fully addressed.

## 2025-10-31 Findings
- ~~**Blocker** – .claude/commands/start.md:27 – Watcher fails with `ImportError: attempted relative import with no known parent package` when run via `./venv/bin/python automation/watcher.py`. The script uses relative imports (`.processors`) but is executed as a standalone file rather than a module. Switch to module execution: `./venv/bin/python -m automation.watcher --config automation/config.yaml` to make relative imports work correctly.~~ _Resolved: Updated to use `-m automation.watcher`_

## 2025-10-30 Findings
- ~~**Blocker** – .claude/commands/start.md:27 – Editor agent launches the watcher with the system Python (`python3 …`), but required deps (watchdog, PyYAML) live only in `venv/`. The command crashes immediately, so `/start` never actually monitors transcripts. Switch the command to `./venv/bin/python automation/watcher.py --config automation/config.yaml` (or document activating the venv up front) and update any related tooling that shells out to the watcher.~~ _Resolved: Updated to use `./venv/bin/python`, then further updated to use `-m automation.watcher` for module execution_
- ~~**Major** – GETTING_STARTED.md:35 and WORKFLOW_GUIDE.md:744 – Setup docs still tell users to `pip install …` against the system interpreter, which macOS now treats as "externally managed." Rewrite these steps to point at the bundled venv (`./venv/bin/pip install …`) or add a short note about creating/activating a dedicated environment so first-time runs succeed.~~ _Resolved: Updated all docs to use `./venv/bin/pip` with venv activation alternative_

## 2025-02-14 Findings
- ~~**Blocker** – automation/config.yaml:2 – Model name is `claude-sonnet-3.5`; Anthropic expects `claude-3.5-sonnet`, so all Claude calls will 400 and automation never produces outputs. Update the config (and default fallback in automation/processors.py:137) to the correct identifier and re-run the watcher smoke test.~~ _Resolved: Updated to `claude-3-5-sonnet-20241022` in both config.yaml and processors.py default_
- ~~**Blocker** – .gitignore – No root `.gitignore` to exclude `transcripts/` and `output/`. Real transcripts (`transcripts/6WLIDapperCadaverHosted_ForClaude.txt`, etc.) and outputs are showing up as untracked; we risk committing sensitive media. Add a `.gitignore` that keeps the folders but drops their contents plus `.DS_Store`, then clean the worktree.~~ _Resolved: Created .gitignore with proper exclusions for transcripts/*, output/*, and .DS_Store_
- ~~**Major** – automation/processors.py:283 – SEMRush artifacts are matched with `fnmatch` against `*.png`. The match is case-sensitive, so `.PNG` (default macOS) or `.jpg/.jpeg` screenshots are ignored and Phase 3 never triggers. Expand the pattern (e.g., normalize suffix or allow common variants).~~ _Resolved: Replaced fnmatch with case-insensitive extension check supporting .png, .jpg, .jpeg_

## Next Steps
1. ~~Implementer – Update `.claude/commands/start.md` (and any related helper docs) to launch the watcher via the repo's virtualenv interpreter, then verify `/start` runs end-to-end without dependency errors.~~ ✓ Completed - Updated to use `-m automation.watcher` for module execution
2. ~~Implementer – Refresh setup instructions in `GETTING_STARTED.md` and `WORKFLOW_GUIDE.md` to use the bundled venv (or a documented custom env) so dependency installs no longer hit the macOS external-management restriction.~~ ✓ Completed
3. ~~Implementer – Fix the model identifier (config + default) and confirm `python3 automation/test_automation.py` still passes.~~ ✓ Completed
4. ~~Implementer – Add the repository `.gitignore`, remove accidental artifacts from git, and document the hygiene step in coordinator notes.~~ ✓ Completed
5. ~~Implementer – Broaden SEMRush artifact detection and drop a quick regression test (manual or scripted) to ensure uppercase and JPEG files are handled. Provide results back to the Project Coordinator.~~ ✓ Completed
6. ~~User verification – Confirm `/start` works end-to-end in real-world usage.~~ ✓ **VERIFIED 2025-10-31**
