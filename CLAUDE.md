# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Purpose

PBS Wisconsin Editorial Assistant v3.0 - A database-backed, API-first system for processing video transcripts and generating SEO-optimized metadata for streaming platforms.

**Key differences from v2.0:**
- FastAPI-based API layer (not direct script execution)
- SQLite database as single source of truth
- React web dashboard for monitoring
- Claude Desktop for copy-editor workflow (MCP integration)

## Key Commands

### Development

```bash
# Initialize development session
./init.sh

# Start API server (once implemented)
uvicorn api.main:app --reload

# Run tests
pytest

# Start web dev server (once implemented)
cd web && npm run dev
```

### Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Architecture

```
editorial-assistant-v3/
├── api/                    # FastAPI application
│   ├── main.py             # App entry point
│   ├── routers/            # API endpoints
│   ├── models/             # Pydantic schemas
│   └── services/           # Business logic
├── web/                    # React dashboard (Phase 3)
│   └── src/
├── .claude/
│   ├── agents/             # LLM agent system prompts
│   ├── templates/          # Output document templates
│   └── commands/           # Slash command definitions
├── config/                 # Configuration files
├── transcripts/            # Input files (gitignored)
├── OUTPUT/                 # Processed outputs (gitignored)
├── tests/                  # Test suite
├── docs/                   # Documentation
├── feature_list.json       # Development task queue
├── claude-progress.txt     # Progress tracking
└── DESIGN_v3.0.md          # Full design specification
```

## Long-Running Development Harness

Start every session with `./init.sh`, then read `claude-progress.txt` and `feature_list.json` to select the next feature.

### Workflow

1. **Initializer**: Run `./init.sh` to load context
2. **Select feature**: Pick next `pending` task from `feature_list.json`
3. **Update status**: Mark as `in_progress`
4. **Implement**: Complete the feature with tests
5. **Verify**: Run tests, ensure exit criteria met
6. **Update tracking**: Mark `completed`, update `claude-progress.txt`
7. **Commit**: Create attributed commit

### Agent Assignment

Tasks in `feature_list.json` have an `agent` field:
- `orchestrator`: Claude Code handles directly (complex, multi-file)
- `cli-agent/gemini`: Delegate to Gemini CLI for boilerplate
- `cli-agent/claude`: Delegate to Claude CLI for documentation

## Git Commit Convention

**See**: `/Users/mriechers/Developer/workspace_ops/conventions/COMMIT_CONVENTIONS.md`

AI commits should include agent attribution:
```
feat: Add new feature

[Agent: Main Assistant]

Detailed description...
```

## Design Reference

The full v3.0 design specification is in `DESIGN_v3.0.md`. Key sections:
- Part 4: API Specification
- Part 5: Web Dashboard Design
- Part 9: Development Roadmap
- Appendix C: Detailed Sprint Breakdown

## Current Sprint

**Sprint 2.1: Foundation & Infrastructure Reliability**

See `feature_list.json` for task queue and `claude-progress.txt` for status.

## Notes for Claude Code

1. **Check feature_list.json** before starting work
2. **Update progress** after completing features
3. **Run tests** before marking complete
4. **Don't break the API contract** - OpenAPI spec is the source of truth (once defined)
5. **Log feedback** - Append issues to `AGENT-FEEDBACK.md` if created
