# Editorial Assistant v3.0 - Design & Vision Document

**Goal:** Transition from a sophisticated CLI tool (v2.0) to a robust, database-backed application (v3.0) that decouples processing logic from the user interface, enabling greater stability, scalability, and future web/mobile integrations.

**Last Updated:** December 2024

---

## Executive Summary

Editorial Assistant v3.0 represents an evolution from a working prototype to a production-ready system. The core value proposition remains unchanged: **transform video transcripts into SEO-optimized metadata with minimal human intervention and maximum cost efficiency**.

What changes is *how* we deliver that value:
- **Decoupled architecture** separates viewing from doing
- **Database-backed state** replaces brittle JSON files
- **API-first design** enables multiple interfaces (CLI, TUI, Web, Mobile)
- **Orchestrator/Agent model** enables parallel development and processing
- **Smart cost routing** leverages CLI agents and external services

---

## Pre-Roadmap Requirement: Feedback Integration

**IMPORTANT**: Before finalizing the roadmap or beginning implementation sprints, all feedback from the following sources MUST be fully reviewed and integrated into this design document:

1. **`USER_FEEDBACK.md`** - User-reported issues, pain points, and feature requests
2. **`AGENT-FEEDBACK.md`** - AI agent observations from processing sessions, including:
   - Technical limitations encountered
   - Process bottlenecks
   - Integration issues with external services
   - Recommendations for architectural improvements

### Integration Checklist

- [x] Review all entries in `USER_FEEDBACK.md` - ensure each item is either:
  - Addressed in the design (reference the section)
  - Explicitly deferred with rationale
  - Rejected with explanation
- [x] Review all entries in `AGENT-FEEDBACK.md` - ensure each item is either:
  - Incorporated into relevant design sections
  - Added to the roadmap as a specific task
  - Noted as a known limitation with mitigation strategy
- [x] Update "Current Limitations" table with any newly identified gaps
- [x] Update roadmap phases to include remediation tasks
- [x] Document any conflicts between user and agent feedback with resolution

**Review completed December 2024.** See "Agent Feedback Integration" section below.

### Agent Feedback Integration (December 2024)

Based on review of `AGENT-FEEDBACK.md`, the following issues have been added to the v3.0 roadmap:

| Issue | Source | Resolution | Phase |
|-------|--------|------------|-------|
| **CLI-Agent timeout/chunking** | AGENT-FEEDBACK Issue 1 | Add chunking for large transcripts, timeout params, size warnings | Phase 4 |
| **SRT speaker normalization** | AGENT-FEEDBACK Issue 2 | Add pre-processing step to normalize speaker markers | Phase 2 |
| **Stale job recovery** | AGENT-FEEDBACK Issue 3 | Heartbeat mechanism, auto-reset stuck jobs, dead letter queue | Phase 2 |
| **Partial progress persistence** | AGENT-FEEDBACK Issue 4 | Step-level status tracking, resumable workflows | Phase 2 |

### User Feedback Status (December 2024)

| Item | Status | Notes |
|------|--------|-------|
| F001 - Readable brainstorming | ✅ Implemented | `strip_code_fences()`, prompts updated |
| F002 - Clean transcripts | ✅ Implemented | Prompts forbid code blocks |
| F003 - Filename convention | ✅ Implemented | `prefixed()` function, renamer script |
| F004 - Archive protocol | ✅ Implemented | Auto-archive transcripts + 15-day output cleanup |
| F005 - Chat revision loop | 🔄 Phase 4 | Documented in agent instructions, implementation in Phase 4 |
| F006 - Visualizer controls | ✅ Phase 1 done | SQLite infrastructure complete, API in Phase 2 |
| F007 - Per-model costs | ✅ Implemented | Model Distribution panel in visualizer |
| F008 - Unknown program bug | ✅ Fixed | `get_program_name()` reads from manifest |

This ensures the v3.0 design reflects real-world usage patterns and avoids repeating known issues.

---

## Part 1: Where We Are (v2.0 Assessment)

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           v2.0 SYSTEM OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌──────────────────────┐     ┌───────────────────┐   │
│  │   Claude    │────▶│   MCP Server (TS)    │────▶│  .processing-     │   │
│  │   Desktop   │     │   14 tools exposed   │     │  requests.json    │   │
│  └─────────────┘     └──────────────────────┘     └─────────┬─────────┘   │
│                                                              │             │
│  ┌─────────────┐     ┌──────────────────────┐               ▼             │
│  │  Terminal   │────▶│  process_queue_      │     ┌───────────────────┐   │
│  │    User     │     │  visual.py (TUI)     │────▶│  LLM Backend      │   │
│  └─────────────┘     └──────────────────────┘     │  Router           │   │
│                                                    │  ┌─────────────┐  │   │
│                      ┌──────────────────────┐     │  │ Gemini Flash│  │   │
│                      │  process_queue_      │     │  │ OpenAI Mini │  │   │
│                      │  auto.py (headless)  │────▶│  │ GPT-4o      │  │   │
│                      └──────────────────────┘     │  │ Claude 3.5  │  │   │
│                                                    │  └─────────────┘  │   │
│                                                    └─────────┬─────────┘   │
│                                                              │             │
│                                                              ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         Agent System                                 │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ transcript │  │  formatter │  │copy-editor │  │    seo-    │    │  │
│  │  │  analyst   │  │            │  │            │  │ researcher │    │  │
│  │  │  (Phase 1) │  │  (Phase 4) │  │ (Phase 2-3)│  │  (Phase 3) │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                              │             │
│                                                              ▼             │
│                      ┌──────────────────────────────────────────────────┐ │
│                      │  OUTPUT/{project}/                               │ │
│                      │  ├── manifest.json                               │ │
│                      │  ├── {project}_brainstorming.md                  │ │
│                      │  ├── {project}_formatted_transcript.md           │ │
│                      │  ├── {project}_copy_revision_v{N}.md             │ │
│                      │  └── processing.log.jsonl                        │ │
│                      └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What's Working Well

| Strength | Implementation | Impact |
|----------|----------------|--------|
| **Cost Optimization** | Multi-backend routing with Gemini Flash preference | 70%+ cost reduction vs. GPT-4o only |
| **Robust Processing** | Atomic file ops, thread-safe locks, timeout protection | Zero data loss in production |
| **Agent Modularity** | 4 specialized agents with clear phase ownership | Easy to extend, test, and maintain |
| **Auditability** | Per-deliverable manifest tracking, JSONL logs | Full provenance for every output |
| **MCP Integration** | 14 tools for Claude Desktop | Seamless drag-and-drop workflow |
| **Visual Dashboard** | Rich TUI with sparkline charts | Real-time cost and progress visibility |

### Current Limitations

| Gap | Root Cause | v3.0 Solution |
|-----|------------|---------------|
| JSON queue is primary state | SQLite exists but not integrated | Full database migration |
| No external API | Processing tightly coupled to UI | FastAPI control plane |
| Copy-editor workflow incomplete | No automated revision loop | Chat agent integration (Phase 4) |
| Single-threaded processing | Stability prioritized over speed | Parallel orchestrator + chunk processing (Phase 4) |
| Terminal-only interface | No web layer | React dashboard (Phase 3) |
| No remote monitoring | Requires local terminal access | WebSocket-based updates (Phase 2) |
| **Stale jobs get stuck** | No heartbeat/watchdog | Heartbeat mechanism + auto-reset (Phase 2) |
| **No partial progress** | All-or-nothing processing | Step-level status tracking (Phase 2) |
| **Large transcripts hang** | No chunking, CLI-Agent timeout | Transcript chunking + parallel processing (Phase 4) |
| **Inconsistent speaker markers** | No pre-processing | SRT speaker normalization (Phase 2) |

### v2.0 Configuration & Execution Bugs (December 2024)

Critical issues discovered during troubleshooting that MUST be addressed in v3.0:

| Bug | Description | Root Cause | v3.0 Prevention |
|-----|-------------|------------|-----------------|
| **Hardcoded backend preferences** | `BACKEND_PREFERENCES` dict in `process_queue_visual.py` overrides `llm-config.json` settings | Config scattered across code and JSON | Single source of truth: all config in database with validation |
| **Python cache persistence** | `.pyc` files retain old code even after source edits, causing stale logic to execute | Python bytecode caching | Add cache-clearing to startup scripts; consider `PYTHONDONTWRITEBYTECODE=1` |
| **System vs venv Python confusion** | Scripts run with wrong Python interpreter depending on invocation method (`python script.py` vs `./script.py`) | Shebang not respected without `./`; venv activation inconsistent | Use explicit venv paths in all entry points; add Python path validation at startup |
| **Environment variable isolation** | `.env` file not loaded when running outside venv; LaunchAgents lack shell env vars | `python-dotenv` only in venv; LaunchAgents don't inherit user shell | Centralize env loading; fail fast if required vars missing; document LaunchAgent env setup |
| **OpenRouter API contract** | Sending both `model` and `models` fields causes 400 error; API expects one or the other | Incomplete understanding of OpenRouter fallback API | Add API contract tests; validate request bodies before sending |
| **Model preference drift** | Config says Gemini but logs show OpenAI Mini being used | Multiple config layers with unclear precedence | Explicit config hierarchy with logging of effective settings at startup |
| **Silent fallback failures** | Backend falls through preference list without clear logging of why each failed | Error messages truncated; no structured failure logging | Structured logging with full error context; dead letter queue for debugging |

**Architectural takeaways for v3.0:**

1. **Single configuration source**: All runtime config (model preferences, API keys, timeouts) should come from ONE validated source (database), not scattered across JSON files, Python dicts, and environment variables.

2. **Explicit Python environment**: Entry points should validate they're running in the correct Python environment with all dependencies before proceeding.

3. **Startup validation**: Check all required env vars, API connectivity, and config validity at startup - fail fast with clear error messages.

4. **Config logging**: Log effective configuration at startup so debugging doesn't require guessing which settings are actually in use.

5. **No bytecode caching in dev**: Development scripts should run with `PYTHONDONTWRITEBYTECODE=1` to prevent stale cache issues.

---

## Part 2: Architectural Shift

### Core Design Principles

1. **Separation of Concerns**: Processing logic knows nothing about UI
2. **Database as Truth**: All state lives in SQLite, not JSON files
3. **API-First**: Every action is an API call (even from TUI)
4. **Event-Driven**: State changes emit events for real-time updates
5. **Cost-Aware**: Every decision considers token/dollar tradeoffs
6. **Parallel by Default**: Work that can be parallelized, should be
7. **Graceful Degradation**: System works at reduced capability when infrastructure unavailable

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           v3.0 TARGET ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INTERFACE LAYER (Multiple Frontends)                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Claude  │  │   Web    │  │   TUI    │  │   CLI    │  │  Mobile  │     │
│  │ Desktop  │  │Dashboard │  │  (Rich)  │  │ Commands │  │  (Future)│     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │             │             │            │
│       └─────────────┴──────┬──────┴─────────────┴─────────────┘            │
│                            ▼                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    API LAYER (FastAPI + WebSocket)                    │  │
│  │  POST /api/queue/add     GET /api/queue          WS /api/events      │  │
│  │  POST /api/jobs/{id}/... GET /api/jobs/{id}      GET /api/analytics  │  │
│  │  POST /api/control/...   GET /api/config         POST /api/config    │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    ORCHESTRATOR (Event-Driven Worker)                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Job Poller  │  │  Executor   │  │  Event Bus  │  │  Scheduler  │  │  │
│  │  │ (DB Watch)  │  │  (Parallel) │  │  (Pub/Sub)  │  │ (Priority)  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    MODEL ROUTER (Cost-Optimized)                      │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │  │
│  │  │  CLI-Agent MCP   │  │   Direct APIs    │  │   Local Ollama   │   │  │
│  │  │  (Gemini/Claude  │  │   (OpenAI,       │  │   (Zero-cost,    │   │  │
│  │  │   CLI wrappers)  │  │    Anthropic)    │  │    fallback)     │   │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘   │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                         AGENT LAYER                                   │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │  │
│  │  │ transcript │ │  formatter │ │copy-editor │ │    seo-    │        │  │
│  │  │  analyst   │ │            │ │ (chat mode)│ │ researcher │        │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    DATA LAYER (SQLite + Files)                        │  │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │  │
│  │  │  dashboard.db   │  │   OUTPUT/{proj}  │  │   transcripts/       │ │  │
│  │  │  - jobs         │  │   - manifest     │  │   - incoming         │ │  │
│  │  │  - session_stats│  │   - deliverables │  │   - archive          │ │  │
│  │  │  - config       │  │   - logs         │  │                      │ │  │
│  │  │  - analytics    │  │                  │  │                      │ │  │
│  │  └─────────────────┘  └──────────────────┘  └──────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Comparison

| Component | v2.0 (Current) | v3.0 (Target) | Migration Path |
|-----------|----------------|---------------|----------------|
| **State Management** | `.processing-requests.json` | SQLite `dashboard.db` | Migration script exists |
| **Processing Logic** | Monolithic `process_queue_visual.py` | Headless `orchestrator.py` | Refactor in progress |
| **Interface** | Terminal UI (Rich) | Hybrid (TUI + Web + CLI) | Additive, TUI remains |
| **Control Plane** | Direct script execution | FastAPI server | New component |
| **Configuration** | Raw JSON files | Pydantic models + DB | Validation layer |
| **Real-time Updates** | Polling + Rich.Live | WebSocket events | New component |
| **Cost Routing** | Hardcoded preferences | Dynamic router + CLI-Agent | Enhanced |

---

## Part 3: Database Schema (Expanded)

### Core Tables

```sql
-- Jobs: The heart of the processing queue
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path TEXT NOT NULL,
    transcript_file TEXT NOT NULL,
    project_name TEXT GENERATED ALWAYS AS (
        substr(project_path, instr(project_path, '/') + 1)
    ) STORED,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused')),
    priority INTEGER NOT NULL DEFAULT 0,

    -- Timing
    queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,

    -- Cost tracking
    estimated_cost REAL DEFAULT 0.0,
    actual_cost REAL DEFAULT 0.0,

    -- Processing metadata
    agent_phases TEXT DEFAULT '["analyst", "formatter"]',  -- JSON array of phases to run
    current_phase TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Error handling
    error_message TEXT,
    error_timestamp DATETIME,

    -- Links
    manifest_path TEXT,
    logs_path TEXT
);

-- Session events: Granular tracking for analytics and debugging
CREATE TABLE session_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'job_queued', 'job_started', 'job_completed', 'job_failed',
        'phase_started', 'phase_completed', 'phase_failed',
        'cost_update', 'model_selected', 'model_fallback',
        'system_pause', 'system_resume', 'system_error',
        'user_action', 'api_call'
    )),
    data TEXT  -- JSON: {cost, tokens, backend, model, error, duration_ms, ...}
);

-- Model performance: Track which models work best for which tasks
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    transcript_size_bucket TEXT CHECK (transcript_size_bucket IN ('small', 'medium', 'large', 'xlarge')),

    -- Performance metrics
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms INTEGER,
    avg_cost REAL,
    avg_quality_score REAL,  -- Optional: user ratings

    -- Last updated
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model_name, agent_type, transcript_size_bucket)
);

-- System configuration: Runtime settings in DB
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT DEFAULT 'string' CHECK (value_type IN ('string', 'int', 'float', 'bool', 'json')),
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Daily aggregates: Pre-computed analytics
CREATE TABLE daily_analytics (
    date TEXT PRIMARY KEY,  -- YYYY-MM-DD
    jobs_completed INTEGER DEFAULT 0,
    jobs_failed INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    avg_cost_per_job REAL,
    total_tokens INTEGER DEFAULT 0,
    most_used_model TEXT,
    avg_duration_ms INTEGER
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_priority ON jobs(priority DESC, id ASC);
CREATE INDEX idx_jobs_queued_at ON jobs(queued_at);
CREATE INDEX idx_session_stats_job ON session_stats(job_id);
CREATE INDEX idx_session_stats_timestamp ON session_stats(timestamp);
CREATE INDEX idx_session_stats_type ON session_stats(event_type);
CREATE INDEX idx_model_perf_agent ON model_performance(agent_type);
```

---

## Part 4: API Specification

### RESTful Endpoints

```yaml
# Queue Management
GET    /api/queue                    # List all jobs with status
POST   /api/queue                    # Add new job(s) to queue
DELETE /api/queue/{job_id}           # Cancel/remove job

# Job Control
GET    /api/jobs/{job_id}            # Get job details
PATCH  /api/jobs/{job_id}            # Update job (priority, status)
POST   /api/jobs/{job_id}/pause      # Pause processing
POST   /api/jobs/{job_id}/resume     # Resume processing
POST   /api/jobs/{job_id}/retry      # Retry failed job
POST   /api/jobs/{job_id}/eject      # Stop mid-stream, mark for manual

# Batch Operations
POST   /api/queue/reorder            # Bulk priority update
POST   /api/queue/pause-all          # Pause entire queue
POST   /api/queue/resume-all         # Resume queue processing

# System Control
GET    /api/system/status            # Orchestrator status
POST   /api/system/pause             # Pause orchestrator
POST   /api/system/resume            # Resume orchestrator
GET    /api/system/health            # Health check

# Configuration
GET    /api/config                   # Get all config
PATCH  /api/config                   # Update config values
GET    /api/config/backends          # List available backends
POST   /api/config/backends/test     # Test backend availability

# Analytics
GET    /api/analytics/summary        # 30/90 day overview
GET    /api/analytics/costs          # Cost breakdown by model/agent
GET    /api/analytics/performance    # Model performance comparison
GET    /api/analytics/timeline       # Hourly/daily cost timeline

# Files (read-only, for web dashboard)
GET    /api/projects                 # List completed projects
GET    /api/projects/{name}          # Project details + files
GET    /api/projects/{name}/files/{path}  # Read specific file
```

### WebSocket Events

```yaml
# Connection
WS /api/events

# Events emitted (server → client)
job:queued         {job_id, project_name, estimated_cost}
job:started        {job_id, phase, model}
job:progress       {job_id, phase, percent, tokens_used}
job:completed      {job_id, actual_cost, duration_ms}
job:failed         {job_id, error, retry_count}
system:paused      {reason}
system:resumed     {}
cost:update        {total_today, total_session}
model:selected     {job_id, model, reason}
model:fallback     {job_id, from_model, to_model, reason}
```

---

## Part 5: Web Dashboard Design

### Page Structure

```
/                      → Dashboard (queue overview + live status)
/queue                 → Queue Management (drag-drop reorder)
/jobs/{id}             → Job Detail (logs, phases, cost breakdown)
/projects              → Completed Projects (browse outputs)
/projects/{name}       → Project Viewer (files, revisions)
/analytics             → Analytics Dashboard (costs, performance)
/settings              → Configuration (backends, preferences)
```

### Dashboard Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PBS Wisconsin Editorial Assistant                    [Pause] [Settings] ⚙  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   TODAY'S STATS             │  │   PROCESSING NOW                    │  │
│  │   ─────────────────────     │  │   ─────────────────────────────     │  │
│  │   Jobs Completed: 12        │  │   2WLI1206HD_REV20251103            │  │
│  │   Jobs Failed: 1            │  │   ████████████░░░░░░  65%           │  │
│  │   Total Cost: $0.42         │  │   Phase: formatter                  │  │
│  │   Avg Cost: $0.03/job       │  │   Model: gemini-flash               │  │
│  │                             │  │   Est. remaining: 2m 30s            │  │
│  └─────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   QUEUE (4 pending)                                    [+ Add Jobs]  │  │
│  │   ──────────────────────────────────────────────────────────────     │  │
│  │   ≡  Snowmobile_Short         pending    $0.02 est    [▲] [▼] [✕]   │  │
│  │   ≡  TLB0303_Interview        pending    $0.08 est    [▲] [▼] [✕]   │  │
│  │   ≡  Demo_LongForm            pending    $0.15 est    [▲] [▼] [✕]   │  │
│  │   ≡  Archive_Restoration      pending    $0.05 est    [▲] [▼] [✕]   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   RECENT ACTIVITY                                                     │  │
│  │   ──────────────────────────────────────────────────────────────     │  │
│  │   14:32  ✓ Euchre_Short completed ($0.02, 45s, gemini-flash)        │  │
│  │   14:28  ✓ LadyLuck_Documentary completed ($0.12, 3m 20s, gpt-4o)   │  │
│  │   14:15  ✗ MemoryProject failed: timeout (retry 1/3 scheduled)      │  │
│  │   14:10  → 2WLI1206HD started (analyst phase)                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   COST TIMELINE (Last 60 minutes)                                    │  │
│  │        $0.15 ┤                                    ╭─╮                │  │
│  │        $0.10 ┤              ╭─╮         ╭─╮      │ │                 │  │
│  │        $0.05 ┤    ╭─╮      │ │  ╭─╮   │ │      │ │    ╭─╮          │  │
│  │        $0.00 ┼────┴─┴──────┴─┴──┴─┴───┴─┴──────┴─┴────┴─┴──────▶   │  │
│  │              14:00      14:15      14:30      14:45      15:00      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Analytics Page Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Analytics                                              [30 Days] [90 Days] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   COST SUMMARY (30 DAYS)    │  │   MODEL PERFORMANCE                 │  │
│  │   ─────────────────────     │  │   ──────────────────────────────    │  │
│  │   Total Cost: $12.45        │  │   Model          Success  Avg Cost  │  │
│  │   Avg/Job: $0.04            │  │   ─────────────  ───────  ────────  │  │
│  │   Jobs: 312                 │  │   gemini-flash    98.2%    $0.015   │  │
│  │   Failed: 8 (2.5%)          │  │   openai-mini     95.1%    $0.025   │  │
│  │                             │  │   gpt-4o          99.8%    $0.18    │  │
│  │   COST BY MODEL             │  │   claude-3.5      97.5%    $0.22    │  │
│  │   ██████████████ gemini 62% │  │                                     │  │
│  │   ██████ openai-mini 25%    │  │   Best for large: gpt-4o           │  │
│  │   ███ gpt-4o 10%            │  │   Best for speed: gemini-flash     │  │
│  │   █ claude 3%               │  │   Best value: gemini-flash         │  │
│  └─────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   DAILY COST TREND                                                    │  │
│  │   $2.00 ┤                                                             │  │
│  │   $1.50 ┤      ╭─╮                                      ╭─╮          │  │
│  │   $1.00 ┤  ╭─╮│ │  ╭─╮          ╭─╮  ╭─╮  ╭─╮        │ │  ╭─╮      │  │
│  │   $0.50 ┤──┴─┴┴─┴──┴─┴──────────┴─┴──┴─┴──┴─┴────────┴─┴──┴─┴──▶   │  │
│  │         Nov 8    Nov 15    Nov 22    Nov 29    Dec 6               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Model Router & CLI-Agent Integration

### Dynamic Model Registry (v3.0 Enhancement)

**Goal:** Enable model switching without code changes - new models or pricing adjustments take effect automatically.

#### Data Sources for Model Intelligence

| Source | URL | Data Provided | Update Frequency | Integration |
|--------|-----|---------------|------------------|-------------|
| **OpenRouter API** | openrouter.ai/api/v1/models | Real-time pricing (per-token input/output), context windows, availability, unified API access | Real-time | Primary source; potential routing layer |
| **Artificial Analysis** | artificialanalysis.ai | Quality benchmarks (MMLU, coding, reasoning), speed benchmarks (tokens/sec), pricing verification, cost-per-quality ratios | Weekly updates | Supplementary for quality scores |
| **LMSys Chatbot Arena** | chat.lmsys.org | ELO rankings from blind human preference tests, "which model writes better" data | Updated with votes | Reference for creative task quality |
| **llmprices.dev** | llmprices.dev | Simple pricing aggregator across providers | Frequent | Cross-check pricing |
| **Provider Docs** | OpenAI, Anthropic, Google | Authoritative specs: max tokens, rate limits, deprecation notices | As announced | Ground truth for technical limits |

#### Architecture Options

**Option A: DIY Model Selection**
- Fetch pricing/capability data from multiple sources
- Build our own scoring algorithm (cost × quality × speed)
- Call providers directly (OpenAI, Anthropic, Google APIs)
- Full control over selection logic

**Option B: OpenRouter as Routing Layer**
- Single API endpoint for all models
- OpenRouter handles provider switching and fallbacks
- Real-time pricing built into their API
- Less control, but simpler implementation

**Pending Analysis:** Once OpenRouter documentation is fully reviewed, conduct cost/benefit analysis:
- API cost overhead (OpenRouter markup vs direct)
- Reliability/uptime comparison
- Flexibility for custom routing logic
- Fallback behavior differences

#### Local Override Layer

Regardless of primary source, maintain local config for:
```json
{
  "model_overrides": {
    "pinned": {
      "copy-editor": "claude-3-5-sonnet",  // Always use this for quality tasks
      "analyst": null                       // Use dynamic selection
    },
    "blocked": ["gpt-3.5-turbo"],           // Models that don't work well for our use case
    "cost_adjustments": {}                  // Manual overrides if source data is wrong
  }
}
```

### Model Routing Strategy

**Principle:** Use free-tier CLI tools when available locally, OpenRouter as universal fallback.

#### v3.0 (Local, Standalone Python)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         v3.0 MODEL ROUTING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Model Family      Primary (Free)           Fallback (Paid)               │
│   ────────────      ──────────────           ──────────────                │
│   Gemini        →   CLI-Agent (gemini)   →   OpenRouter                    │
│   OpenAI        →   CLI-Agent (codex)    →   OpenRouter                    │
│   Claude        →   CLI-Agent (claude)   →   OpenRouter                    │
│                                                                             │
│   Startup: Detect which CLI tools are available                            │
│   Runtime: Try CLI-Agent first, fall back to OpenRouter on failure         │
│   Cooldown: Mark CLI as unavailable temporarily after repeated failures    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### v4.0 (Remote)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         v4.0 MODEL ROUTING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Model Family      Primary                                                 │
│   ────────────      ───────                                                │
│   Everything    →   OpenRouter                                              │
│                                                                             │
│   CLI-Agent not available on remote servers                                 │
│   OpenRouter handles all routing and fallbacks                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Configuration

```json
{
  "routing": {
    "cli_agent": {
      "enabled": true,
      "timeout_seconds": 120,
      "cooldown_on_failure_seconds": 300,
      "agents": {
        "gemini": { "enabled": true },
        "codex": { "enabled": true },
        "claude": { "enabled": true }
      }
    },
    "openrouter": {
      "enabled": true,
      "api_key_env": "OPENROUTER_API_KEY"
    }
  }
}
```

### Task-Aware Model Selection

The routing above determines *how* to reach a model. This section determines *which* model to use.

| Agent | Transcript Size | Quality | Preferred Model | Rationale |
|-------|-----------------|---------|-----------------|-----------|
| analyst | any | draft | gemini-flash | Fast, cheap, good enough |
| analyst | any | standard | gemini-flash | Reliable for extraction |
| formatter | small/medium | any | gemini-flash | Handles context well |
| formatter | large/xlarge | any | gemini-flash or gpt-4o | Large context window needed |
| copy-editor | any | draft | gemini-flash | Quick iterations |
| copy-editor | any | premium | claude-3.5-sonnet | Best writing quality |
| seo-researcher | any | any | gemini-flash | Fast keyword analysis |

### CLI-Agent MCP Tools

The `cli-agent-server` MCP provides these tools:

| Tool | Use Case |
|------|----------|
| `query_agent(prompt, agent="gemini")` | Brainstorming, keyword research |
| `query_agent(prompt, agent="claude")` | Copy editing, quality review |
| `query_agent(prompt, agent="codex")` | Code-related tasks |
| `delegate_task(goal, agent, max_iterations)` | Complex multi-step tasks |

**Fallback behavior:**
1. Check CLI-Agent availability at startup
2. Attempt CLI-Agent for matching model family
3. On timeout or error, mark unavailable (temporary cooldown)
4. Route to OpenRouter as fallback
5. Log which path was used for cost tracking

### Prompt Management & Versioning (from Gemini review)

Agent prompts need versioning and testing, especially when used across different models.

#### Current State
```
.claude/agents/
├── analyst.md
├── formatter.md
├── copy-editor.md
└── seo-researcher.md
```

#### v3.0 Improvements

| Aspect | Current | v3.0 Target |
|--------|---------|-------------|
| **Versioning** | Git history only | Semantic versioning in frontmatter |
| **Model compatibility** | Assumed universal | Model-specific variants or notes |
| **Testing** | Manual | Sample inputs with expected outputs |
| **Rollback** | Git revert | Config flag to use previous version |

**Prompt frontmatter format:**
```yaml
---
version: 1.2.0
models_tested: [gemini-2.0-flash, claude-3.5-sonnet, gpt-4o-mini]
last_updated: 2024-12-15
breaking_changes: false
---
```

**Testing approach:**
- Maintain `tests/prompt_samples/` with input transcripts
- Expected output patterns (not exact matches)
- Run before deploying prompt changes
- Log prompt version in manifest for each deliverable

---

## Part 7: Editor Agent UX & Session Awareness

### The Problem: Disconnected Experience

In v1.0/v2.0, users face these friction points:

| Pain Point | Current State | User Impact |
|------------|---------------|-------------|
| **Invisible outputs** | Revisions created but only referenced in chat | User must navigate to `OUTPUT/{project}/` to find files |
| **No workflow guidance** | Agent doesn't know where user is in the process | User must remember what phase they're in |
| **Manual input gathering** | Keywords → SEMRush → screenshot → upload → report | 5+ steps for a single analysis |
| **Scattered context** | Brainstorming in one file, transcript in another, revisions in a third | Constant context-switching |
| **No progress visibility** | User doesn't know what deliverables exist or are pending | Confusion about what's been done |

### Design Principle: The Agent as Guide

The editor agent should feel like a **collaborative partner with a clipboard** - always aware of:
1. **What project you're working on** (and confirming it)
2. **What phase you're in** (brainstorming, editing, analysis, conclusion)
3. **What deliverables exist** (and surfacing them proactively)
4. **What inputs are needed next** (and prompting for them)
5. **Where to find things** (artifacts in chat, or explicit paths for CLI users)

### Session State Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EDITOR SESSION STATE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROJECT CONTEXT (always visible to agent)                          │   │
│  │                                                                      │   │
│  │  project_id: "2WLI1206HD_REV20251103"                               │   │
│  │  project_path: "OUTPUT/2WLI1206HD_REV20251103/"                     │   │
│  │  current_phase: "editing"                                            │   │
│  │                                                                      │   │
│  │  deliverables_status:                                                │   │
│  │    brainstorming:        ✅ created (Dec 8, 14:32)                  │   │
│  │    formatted_transcript: ✅ created (Dec 8, 14:45)                  │   │
│  │    copy_revision_v1:     ✅ created (Dec 8, 15:02)                  │   │
│  │    copy_revision_v2:     🔄 in_progress                             │   │
│  │    keyword_report:       ⏳ pending (needs SEMRush data)            │   │
│  │    timestamp_report:     ⏳ available (video is 23 min)             │   │
│  │                                                                      │   │
│  │  user_inputs_received:                                               │   │
│  │    transcript: ✅                                                    │   │
│  │    draft_copy: ✅ (title + short desc)                              │   │
│  │    semrush_screenshot: ❌                                            │   │
│  │    user_feedback: ✅ ("make title shorter")                         │   │
│  │                                                                      │   │
│  │  next_suggested_action: "Review copy_revision_v2 artifact below"    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Artifact Delivery Strategy

**Goal**: Deliverables should appear where the user is working, not hidden in folders.

| Interface | Artifact Delivery | Fallback |
|-----------|-------------------|----------|
| **Claude Desktop (chat)** | Claude Artifacts (inline, copyable) | "Saved to `OUTPUT/{project}/{file}` - [click to open]" |
| **Claude Code (CLI)** | Reference saved file with full path | Open in editor via `code` or `open` command |
| **Web Dashboard** | Inline preview panel | Download button + copy-to-clipboard |

**Implementation Approach:**

```python
# Pseudocode for artifact delivery
def deliver_artifact(artifact_type: str, content: str, session: EditorSession):
    """
    Deliver artifact to user based on their interface.
    Always save to disk, but present appropriately.
    """
    # 1. Always persist to project folder
    file_path = save_to_project(session.project_path, artifact_type, content)

    # 2. Deliver based on interface
    if session.interface == "claude_desktop":
        # Create Claude Artifact for inline viewing
        return create_artifact(
            title=f"{artifact_type} - {session.project_id}",
            content=content,
            type="markdown"
        )
    elif session.interface == "claude_code":
        # Reference file with actionable path
        return f"""
✅ **{artifact_type}** saved to:
   `{file_path}`

To open: `open "{file_path}"` or `code "{file_path}"`
"""
    elif session.interface == "web":
        # Return both inline preview and file reference
        return {
            "inline_content": content,
            "file_path": file_path,
            "actions": ["copy", "download", "open_in_editor"]
        }
```

### Phase-Based Workflow with Clear Triggers

Adapting v1.0's rigid phase logic for v3.0:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE FLOW WITH TRIGGERS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                           │
│  │   START     │  User provides transcript                                 │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐  Agent creates Brainstorming Document                     │
│  │  PHASE 1    │  → Delivered as ARTIFACT (chat) or saved file (CLI)      │
│  │ BRAINSTORM  │  → Agent prompts: "Ready to start editing, or would      │
│  │             │     you like keyword research first?"                     │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│    ┌────┴────┐                                                             │
│    │         │                                                              │
│    ▼         ▼                                                              │
│  ┌─────┐  ┌─────┐                                                          │
│  │ 2   │  │ 3   │  TRIGGERS:                                               │
│  │EDIT │  │ANLZ │  • User provides draft copy → Phase 2                   │
│  └──┬──┘  └──┬──┘  • User provides SEMRush data → Phase 3                 │
│     │        │     • User asks for keyword research → Phase 3              │
│     │        │                                                              │
│     └────┬───┘                                                             │
│          │                                                                  │
│          ▼                                                                  │
│  ┌─────────────┐  Agent creates Copy Revision Document                     │
│  │  PHASE 2    │  → ALWAYS as artifact (visible next to conversation)     │
│  │  EDITING    │  → Shows: Original | Revised | Reasoning                 │
│  │             │  → Agent prompts: "What would you like to adjust?"       │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│    ┌────┴────┐   LOOP until user satisfied                                 │
│    │ REVISE  │   Each revision → new artifact version                      │
│    └────┬────┘   Always visible, never hidden                              │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐  Agent offers final deliverables:                         │
│  │  PHASE 4    │  → Formatted Transcript (if not already created)         │
│  │ CONCLUSION  │  → Timestamp Report (if video 15+ min)                   │
│  │             │  → Final keyword list (platform-ready)                    │
│  └─────────────┘                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Proactive Agent Prompts

The agent should **always end messages with a clear next step**:

| Phase | After Action | Agent Prompt |
|-------|-------------|--------------|
| **Brainstorming complete** | Delivered brainstorming doc | "When you have draft copy to review, share it here and I'll create a revision document. Or if you'd like keyword research first, upload a SEMRush screenshot or ask me to research." |
| **Revision created** | Delivered copy revision | "Here's your revision (see artifact above). What would you like to adjust? You can: (1) Give feedback on specific elements, (2) Share updated draft copy, (3) Request keyword research, or (4) Move to conclusion if satisfied." |
| **Analysis complete** | Delivered keyword report | "Based on this keyword data, I'd suggest these copy tweaks: [summary]. Would you like me to create an updated revision?" |
| **User seems done** | Multiple revisions completed | "It looks like we're in good shape! Would you like me to: (1) Generate the formatted transcript, (2) Create a timestamp report (your video is 23 min), or (3) Finalize the keyword list for platform upload?" |

### Project Status Panel

For both web dashboard and chat, maintain a visible status panel:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📁 PROJECT: 2WLI1206HD_REV20251103                    Phase: EDITING      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DELIVERABLES                          INPUTS RECEIVED                      │
│  ─────────────                         ───────────────                      │
│  ✅ Brainstorming Document             ✅ Transcript                        │
│  ✅ Formatted Transcript               ✅ Draft copy (title, short desc)   │
│  ✅ Copy Revision v1                   ❌ SEMRush data                      │
│  🔄 Copy Revision v2 (in progress)     ✅ Feedback ("shorter title")       │
│  ⏳ Keyword Report (needs SEMRush)                                         │
│  ⏳ Timestamp Report (available)                                           │
│                                                                             │
│  💡 NEXT: Review revision v2 artifact, or provide SEMRush screenshot       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Simplified SEMRush Workflow

Current flow (5+ steps) vs. target flow:

**Current:**
1. User finds keyword list in JSON/brainstorming doc
2. User copies keywords to SEMRush
3. User takes screenshot of results
4. User uploads screenshot to chat
5. Agent analyzes and creates report

**Target (v3.0):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Option A: Streamlined Manual                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Agent provides COPY-READY keyword list in artifact:                    │
│     "Here are your keywords formatted for SEMRush. Click to copy:"         │
│     ┌────────────────────────────────────────────────────────────┐         │
│     │ wisconsin history, state parks, hiking trails, outdoor... │ [COPY]  │
│     └────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  2. Agent prompts: "Paste these into SEMRush, then share the               │
│     screenshot here. I'll analyze the results and update your              │
│     keyword strategy."                                                      │
│                                                                             │
│  3. User uploads screenshot → Agent delivers Keyword Report artifact       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Option B: API Integration (Future)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Agent calls SEMRush API directly with keywords                          │
│  2. Results analyzed automatically                                          │
│  3. Keyword Report delivered as artifact                                    │
│                                                                             │
│  (Requires: SEMRush API key, rate limit management, cost tracking)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CLI vs Chat Interface Awareness

The agent should detect and adapt to the interface:

| Signal | Interface | Artifact Strategy |
|--------|-----------|-------------------|
| MCP tool calls present | Claude Desktop | Use Claude Artifacts |
| Running in Claude Code | CLI | Reference file paths, suggest `open` commands |
| API call from web dashboard | Web | Return structured JSON with inline + file |

**Agent greeting should set context:**

```markdown
# Claude Desktop Version
"I see you're working on **2WLI1206HD_REV20251103**. You have a brainstorming
document ready and one copy revision so far. I'll show all new revisions as
artifacts right here in our conversation.

What would you like to work on? You can share draft copy for revision, or
I can help with keyword research."

# CLI Version
"I see you're working on **2WLI1206HD_REV20251103**.

📁 Project folder: `OUTPUT/2WLI1206HD_REV20251103/`

Existing deliverables:
  ✅ `2WLI1206HD_brainstorming.md`
  ✅ `2WLI1206HD_copy_revision_v1.md`

What would you like to work on? Share draft copy, or I can open an existing
file for you: `open OUTPUT/2WLI1206HD_REV20251103/`"
```

### Web Dashboard: Unified Queue + Editor View

The web dashboard serves double duty: **monitoring automation** AND **editing workspace**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PBS Wisconsin Editorial Assistant                              [Settings] │
├───────────────┬─────────────────────────────────────────────────────────────┤
│               │                                                             │
│  QUEUE        │   PROJECT WORKSPACE                                         │
│  ─────────    │   ─────────────────                                         │
│               │                                                             │
│  🔄 Processing│   📁 2WLI1206HD_REV20251103              Phase: EDITING    │
│  └ 2WLI1206HD │   ─────────────────────────────────────────────────────    │
│    65% fmt    │                                                             │
│               │   ┌─────────────────────────────────────────────────────┐  │
│  ⏳ Pending   │   │  DELIVERABLES              │  DOCUMENT VIEWER       │  │
│  ├ Snowmobile │   │  ─────────────             │  ────────────────      │  │
│  ├ TLB0303    │   │                            │                        │  │
│  └ Demo_Long  │   │  ✅ Brainstorming    [👁]  │  # Copy Revision v2    │  │
│               │   │  ✅ Formatted Trans  [👁]  │                        │  │
│  ✅ Completed │   │  ✅ Copy Rev v1      [👁]  │  ## Title Revisions    │  │
│  ├ Euchre     │   │  🔄 Copy Rev v2      [👁]  │  | Original | Revised |│  │
│  ├ LadyLuck   │   │  ⏳ Keyword Report        │  |----------|---------|│  │
│  └ Memory...  │   │  ⏳ Timestamps            │  | Wisconsin | Wisc... |│  │
│               │   │                            │                        │  │
│  ─────────    │   │  📋 COPY KEYWORDS:        │  ## Reasoning          │  │
│  [+ Add Job]  │   │  ┌────────────────────┐   │  The revision uses...  │  │
│               │   │  │wisconsin, hiking...│   │                        │  │
│               │   │  └────────────────────┘   │  [Copy] [Download]     │  │
│               │   │        [Copy to Clipboard]│                        │  │
│               │   └─────────────────────────────────────────────────────┘  │
│               │                                                             │
│               │   ┌─────────────────────────────────────────────────────┐  │
│               │   │  💬 CHAT WITH EDITOR AGENT                          │  │
│               │   │  ───────────────────────                            │  │
│               │   │                                                      │  │
│               │   │  Agent: Here's revision v2. The title is now 68     │  │
│               │   │  chars. What would you like to adjust?              │  │
│               │   │                                                      │  │
│               │   │  ┌────────────────────────────────────────────────┐ │  │
│               │   │  │ Make the description more active voice...     │ │  │
│               │   │  └────────────────────────────────────────────────┘ │  │
│               │   │                                        [Send] [📎]  │  │
│               │   └─────────────────────────────────────────────────────┘  │
│               │                                                             │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

**Key Features:**

| Feature | Description |
|---------|-------------|
| **Split view** | Queue on left (compact), workspace on right (detailed) |
| **Click to focus** | Click any project in queue to load its workspace |
| **Document viewer** | Inline markdown rendering with copy/download buttons |
| **Eye icons** | Quick preview of any deliverable without leaving page |
| **Chat integration** | Embedded chat with editor agent (WebSocket-based) |
| **Copy-ready keywords** | One-click copy for SEMRush workflow |
| **Real-time updates** | WebSocket pushes new deliverables as they're created |

**Project Workspace Modes:**

| Mode | Trigger | View |
|------|---------|------|
| **Processing** | Job is `in_progress` | Progress bar, live logs, "Eject" button |
| **Ready to Edit** | Job is `completed` | Deliverable list, document viewer, chat |
| **Editing Active** | User is chatting | Full chat + document side-by-side |
| **Review** | Multiple revisions exist | Version comparison, "Accept" button |

**Mobile-Responsive Behavior:**

```
┌─────────────────────────────────────┐
│  PBS Editorial Assistant     [≡]   │
├─────────────────────────────────────┤
│                                     │
│  📁 2WLI1206HD            EDITING  │
│  ───────────────────────────────   │
│                                     │
│  [Queue] [Docs] [Chat] [Settings]  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  # Copy Revision v2         │   │
│  │                             │   │
│  │  ## Title Revisions         │   │
│  │  | Original | Revised |     │   │
│  │  |----------|---------|     │   │
│  │  | Wisconsin | Wisc...|     │   │
│  │                             │   │
│  │  [Copy] [Download] [Share]  │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Type a message...      [➤] │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**API Endpoints for Web Workspace:**

```yaml
# Workspace-specific endpoints (in addition to queue endpoints)
GET  /api/projects/{name}/workspace    # Full workspace state
GET  /api/projects/{name}/deliverables # List with content previews
GET  /api/projects/{name}/chat/history # Chat session history
POST /api/projects/{name}/chat/message # Send message to editor agent
WS   /api/projects/{name}/events       # Real-time updates for this project
```

---

## Part 7b: Chat Agent Workflow (Copy-Editor)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COPY-EDITOR CHAT WORKFLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐          │
│  │   Phase 1   │────────▶│   Phase 2   │────────▶│   Phase 3   │          │
│  │ Brainstorm  │         │  User Draft │         │   Revision  │          │
│  │  (auto)     │         │  (manual)   │         │   Loop      │          │
│  └─────────────┘         └─────────────┘         └──────┬──────┘          │
│                                                         │                   │
│                                                         ▼                   │
│                          ┌──────────────────────────────────────────────┐  │
│                          │  User provides:                              │  │
│                          │  - Draft title/description                   │  │
│                          │  - Screenshot of current CMS state           │  │
│                          │  - Specific feedback ("too long", "wrong     │  │
│                          │    tone", "missing keyword X")               │  │
│                          └──────────────────────────────────────────────┘  │
│                                                         │                   │
│                                                         ▼                   │
│                          ┌──────────────────────────────────────────────┐  │
│                          │  Copy-Editor Agent:                          │  │
│                          │  1. Ingests brainstorming + transcript       │  │
│                          │  2. Analyzes user draft vs. brainstorming    │  │
│                          │  3. Generates revision as ARTIFACT           │  │
│                          │  4. Provides side-by-side comparison         │  │
│                          │  5. Flags AP Style / character count issues  │  │
│                          └──────────────────────────────────────────────┘  │
│                                                         │                   │
│                                                         ▼                   │
│                          ┌──────────────────────────────────────────────┐  │
│                          │  Revision saved as:                          │  │
│                          │  OUTPUT/{project}/{project}_copy_revision_   │  │
│                          │  v{N}.md                                     │  │
│                          │                                              │  │
│                          │  Loop continues until user approves or       │  │
│                          │  marks "eject" to complete manually          │  │
│                          └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Eject Button Behavior

The "Eject" feature allows graceful mid-stream interruption:

1. **Trigger**: User clicks Eject (web) or sends `/eject` (CLI/chat)
2. **Immediate Actions**:
   - Current LLM call is allowed to complete (no wasted tokens)
   - Job status → `paused_user_takeover`
   - Partial outputs saved with `_PARTIAL` suffix
3. **Resume Options**:
   - `resume`: Continue from last checkpoint
   - `restart_phase`: Redo current phase only
   - `manual_complete`: Mark job done, user handles rest

### Smart Retry Logic

```python
RETRY_STRATEGY = {
    "rate_limit": {
        "wait_time": lambda attempt: min(60 * (2 ** attempt), 300),  # 1m, 2m, 4m, 5m max
        "fallback_model": True,  # Try different model
        "max_attempts": 3
    },
    "timeout": {
        "wait_time": lambda attempt: 30,  # Fixed 30s wait
        "fallback_model": False,  # Same model, might be temp
        "max_attempts": 2
    },
    "context_length": {
        "wait_time": lambda attempt: 0,  # Immediate
        "fallback_model": True,  # Must use larger context model
        "upgrade_path": ["gemini-flash", "gpt-4o", "claude-3.5"]
    },
    "api_error": {
        "wait_time": lambda attempt: 60,
        "fallback_model": True,
        "max_attempts": 3
    }
}
```

---

## Part 8: User Stories

### Core Workflow

**US-001: Batch Processing**
> As an editor, I want to drop multiple transcript files into a folder and have them automatically queued and processed, so I can focus on other work while metadata is generated.

**Acceptance Criteria:**
- [ ] Transcripts in `transcripts/` folder auto-detected within 30s
- [ ] Each transcript creates a job in pending status
- [ ] Jobs process in FIFO order unless prioritized
- [ ] Completed jobs have brainstorming + formatted transcript

**US-002: Priority Override**
> As an editor with a deadline, I want to move a specific transcript to the front of the queue, so it processes before other pending jobs.

**Acceptance Criteria:**
- [ ] Can prioritize via web dashboard (drag-drop or button)
- [ ] Can prioritize via CLI (`/prioritize-transcript NAME`)
- [ ] Can prioritize via API (`PATCH /api/jobs/{id}` with priority)
- [ ] Prioritized job starts within 60s if orchestrator is running

**US-003: Real-time Monitoring**
> As an editor, I want to see live progress of the current job, including which phase it's in and estimated time remaining.

**Acceptance Criteria:**
- [ ] Dashboard shows current job with progress bar
- [ ] Phase name displayed (analyst, formatter, etc.)
- [ ] Estimated time updates as processing continues
- [ ] Cost-so-far visible during processing

### Error Handling

**US-004: Failed Job Recovery**
> As an editor, when a job fails, I want to see why it failed and easily retry it without re-uploading the transcript.

**Acceptance Criteria:**
- [ ] Failed jobs show error message in UI
- [ ] "View Logs" button shows detailed error
- [ ] "Retry" button re-queues with same settings
- [ ] Retry count visible (e.g., "Attempt 2 of 3")

**US-005: Mid-Stream Eject**
> As an editor, if I realize I uploaded the wrong file or need to take over manually, I want to stop processing without losing partial work.

**Acceptance Criteria:**
- [ ] "Eject" button visible during processing
- [ ] Current LLM call completes (no token waste)
- [ ] Partial outputs saved with `_PARTIAL` suffix
- [ ] Job status clearly shows "User Takeover"

### Cost Management

**US-006: Cost Visibility**
> As a budget-conscious editor, I want to see estimated and actual costs for each job before and after processing.

**Acceptance Criteria:**
- [ ] Queue shows estimated cost per job
- [ ] Completed jobs show actual cost
- [ ] Daily/monthly totals visible on dashboard
- [ ] Alert if daily cost exceeds threshold

**US-007: Model Performance Insights**
> As a power user, I want to see which models perform best for different tasks so I can optimize my settings.

**Acceptance Criteria:**
- [ ] Analytics page shows success rate by model
- [ ] Average cost per model visible
- [ ] Recommendation for "best value" model
- [ ] Historical comparison (last 30/90 days)

### Integration

**US-008: Claude Desktop Workflow**
> As an editor using Claude Desktop, I want to interact with the queue and request revisions through natural conversation.

**Acceptance Criteria:**
- [ ] MCP tools work for queue status, prioritization
- [ ] Copy-editor agent accessible via chat
- [ ] Revisions saved automatically to project folder
- [ ] Project context (brainstorming, transcript) loaded on demand

**US-009: Web-Based Editing Workspace**
> As an editor, I want to view my deliverables and chat with the editor agent directly in the web dashboard, so I don't have to switch between browser and file explorer.

**Acceptance Criteria:**
- [ ] Click project in queue → workspace loads with all deliverables
- [ ] Document viewer renders markdown inline with copy/download buttons
- [ ] Keywords displayed with one-click copy for SEMRush workflow
- [ ] Chat panel embedded in workspace for revision requests
- [ ] New deliverables appear in real-time as they're created
- [ ] Phase indicator shows where I am in the workflow
- [ ] Clear "next step" prompt visible at all times

**US-010: Unified Experience Across Interfaces**
> As an editor who switches between CLI and web, I want my project state to be consistent regardless of which interface I use.

**Acceptance Criteria:**
- [ ] Revisions created in CLI appear immediately in web dashboard
- [ ] Chat history persists across sessions
- [ ] Project phase and deliverable status synced in real-time
- [ ] Agent greets me with current context regardless of interface
- [ ] Keywords and copy-ready text available in all interfaces

---

## Part 8b: Development Isolation Strategy

### The Challenge

v2.0 is in active production use. We need to develop v3.0 without breaking the current workflow.

### Solution: Parallel Directory Structure + Protected Branches

**Directory Strategy:**

```
editorial-assistant/
├── scripts/                    # v2.0 PRODUCTION - minimize changes
│   ├── process_queue_visual.py # ← Keep working, don't refactor
│   ├── process_queue_auto.py   # ← Keep working, don't refactor
│   ├── llm_backend.py          # ← Shared, enhance carefully
│   ├── orchestrator.py         # ← v3.0 foundation, extend with flags
│   └── dashboard/              # ← TUI components, keep working
│
├── api/                        # v3.0 NEW - develop freely
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── routers/                # Endpoint modules
│   ├── models/                 # Pydantic schemas
│   ├── services/               # Business logic
│   └── websocket.py            # Real-time events
│
├── web/                        # v3.0 NEW - develop freely
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── config/
│   ├── llm-config.json         # Shared, backward compatible
│   └── dashboard_schema.sql    # Extend with migrations, don't break
│
├── .processing-requests.json   # v2.0 uses this
└── dashboard.db                # v3.0 uses this (v2.0 orchestrator too)
```

**Key Principle:** v3.0 is mostly *additive*. The new `api/` and `web/` directories don't conflict with existing `scripts/`. We extend rather than replace.

### Branch Strategy

```
main (agent-version)
│
├── Protected: Production-ready code only
├── v2.0 scripts work here
│
├─── v3-api ────────────────────────────────
│    │ Phase 2 development
│    │ FastAPI + Pydantic + WebSocket
│    │ Merge to main when stable
│    │
├─── v3-web ────────────────────────────────
│    │ Phase 3 development
│    │ React + Tailwind dashboard
│    │ Merge to main when stable
│    │
└─── v3-integration ────────────────────────
     │ Phase 4 development
     │ CLI-Agent integration, copy-editor workflow
     │ Merge to main when stable
```

### Backward Compatibility Rules

| Component | Rule |
|-----------|------|
| `.processing-requests.json` | Keep working until v3.0 fully replaces it |
| `process_queue_visual.py` | Don't modify; TUI will become API client later |
| `process_queue_auto.py` | Don't modify; headless processing stays |
| `orchestrator.py` | Can extend, but must work standalone |
| `llm-config.json` | Add fields, never remove or rename |
| `dashboard.db` | Use migrations, never drop tables |
| MCP server | Keep all existing tools working |

### Feature Flags for Gradual Migration

```python
# config/feature_flags.py
FEATURES = {
    "use_database_queue": False,      # True = SQLite, False = JSON
    "enable_api_server": False,       # True = start FastAPI alongside
    "websocket_events": False,        # True = emit real-time events
    "new_model_router": False,        # True = use CLI-Agent integration
}
```

This allows testing v3.0 components without breaking v2.0 production use.

---

## Part 8c: Cloud Agent Sprint (Claude Code Web)

> **FOR CLAUDE CODE WEB**: This section defines your sprint scope. Focus ONLY on the tasks below. Do not modify production-critical files in `scripts/` unless explicitly listed.

### Sprint Overview

**Purpose:** Infrastructure and documentation improvements that benefit both v2.0 and v3.0, without touching production-critical code paths.

**Constraints:**
- Budget: ~$75-100 in credits
- Timeline: 3-5 focused sessions
- Scope: Documentation, type hints, validation, error handling
- **NOT in scope:** Feature development, refactoring working code, v3.0 implementation

### Why This Work Matters

| Improvement | v2.0 Benefit | v3.0 Benefit |
|-------------|--------------|--------------|
| Type hints | Easier debugging | Pydantic model foundation |
| Docstrings | Self-documenting code | Architecture understanding |
| Error messages | Less troubleshooting | Better API error responses |
| Agent documentation | Clearer workflows | Copy-editor agent design |
| Config validation | Catch errors early | Pydantic settings prep |

### Session 1: Agent & Template Audit

**Goal:** Ensure all agent prompts and templates are documented and consistent.

**Tasks:**
1. Audit `.claude/agents/*.md` files:
   - [ ] Each agent has clear role description at top
   - [ ] Input/output expectations documented
   - [ ] Phase ownership clearly stated
   - [ ] No conflicting instructions between agents

2. Audit `.claude/templates/*.md` files:
   - [ ] Templates match current deliverable formats
   - [ ] Character count requirements are accurate
   - [ ] AP Style requirements are explicit

3. Create `docs/AGENT_REFERENCE.md`:
   ```markdown
   # Agent Reference

   ## transcript-analyst
   - Phase: 1 (Brainstorming)
   - Input: Raw transcript
   - Output: brainstorming.md
   - Model preference: gemini-flash (cheap, fast)

   ## formatter
   ...
   ```

4. Create `docs/TEMPLATE_GUIDE.md`:
   - Document each template's purpose
   - Show example output for each
   - Note character limits and validation rules

**Deliverables:**
- Updated agent files with consistent structure
- `docs/AGENT_REFERENCE.md`
- `docs/TEMPLATE_GUIDE.md`

### Session 2: Type Hints & Validation

**Goal:** Add type safety to core modules (prep for Pydantic migration).

**Files to modify (SAFE - these are utility modules):**
- [ ] `scripts/llm_backend.py` - Add type hints to all functions
- [ ] `config/` - Create `settings.py` with Pydantic models

**DO NOT modify:**
- `scripts/process_queue_visual.py` (production TUI)
- `scripts/process_queue_auto.py` (production processor)

**Tasks:**
1. Add type hints to `llm_backend.py`:
   ```python
   # Before
   def select_backend(agent, transcript_size):
       ...

   # After
   def select_backend(
       agent: Literal["analyst", "formatter", "copy-editor", "seo-researcher"],
       transcript_size: int
   ) -> tuple[str, str]:  # (backend_name, model_name)
       ...
   ```

2. Create `config/settings.py` with Pydantic models:
   ```python
   from pydantic import BaseModel, Field

   class BackendConfig(BaseModel):
       type: Literal["openai", "anthropic", "gemini", "ollama"]
       endpoint: str
       model: str
       timeout: int = 180
       cost_per_project: float = 0.0
       enabled: bool = True

   class LLMConfig(BaseModel):
       primary_backend: str
       fallback_backend: str
       backends: dict[str, BackendConfig]
       ...
   ```

3. Add validation function that loads and validates `llm-config.json`:
   ```python
   def load_config() -> LLMConfig:
       """Load and validate LLM configuration."""
       with open("config/llm-config.json") as f:
           data = json.load(f)
       return LLMConfig(**data)  # Raises ValidationError if invalid
   ```

**Deliverables:**
- Type-hinted `llm_backend.py`
- New `config/settings.py` with Pydantic models
- Validation function for config loading

### Session 3: Error Handling & Logging

**Goal:** Make errors self-explanatory and logging actionable.

**Tasks:**
1. Audit error messages in `scripts/llm_backend.py`:
   - [ ] Every exception includes context (what failed, why, what to try)
   - [ ] API errors include model/backend that failed
   - [ ] Timeout errors suggest increasing timeout or trying fallback

2. Create structured logging utilities:
   ```python
   # utils/logging.py
   import logging
   from datetime import datetime

   def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
       """Configure logger with consistent format."""
       logger = logging.getLogger(name)
       handler = logging.StreamHandler()
       handler.setFormatter(logging.Formatter(
           '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
       ))
       logger.addHandler(handler)
       logger.setLevel(level)
       return logger
   ```

3. Create `docs/TROUBLESHOOTING.md`:
   ```markdown
   # Troubleshooting Guide

   ## Common Errors

   ### "Backend unavailable: gemini-flash"
   **Cause:** Gemini API not responding or rate limited
   **Solution:**
   1. Check GEMINI_API_KEY is set
   2. Wait 60 seconds and retry
   3. System will auto-fallback to openai-mini

   ### "Context length exceeded"
   **Cause:** Transcript too long for selected model
   **Solution:** System should auto-upgrade to gpt-4o
   ...
   ```

**Deliverables:**
- Improved error messages in `llm_backend.py`
- New `scripts/utils/logging.py`
- `docs/TROUBLESHOOTING.md`

### Session 4: User Documentation

**Goal:** Documentation that reduces "how does this work" questions.

**Tasks:**
1. Update `README.md`:
   - [ ] Current architecture overview (with ASCII diagram)
   - [ ] Quick start for new users
   - [ ] Link to detailed docs

2. Create `docs/QUICK_START.md`:
   - [ ] Prerequisites (Python, API keys, etc.)
   - [ ] Installation steps
   - [ ] First transcript processing walkthrough
   - [ ] Expected output structure

3. Create `docs/ARCHITECTURE.md`:
   - [ ] System overview diagram
   - [ ] Component descriptions
   - [ ] Data flow explanation
   - [ ] File/folder purposes

4. Create `docs/WORKFLOW.md`:
   - [ ] Phase 1-4 workflow with triggers
   - [ ] Deliverable creation flow
   - [ ] User decision points
   - [ ] Example session walkthrough

**Deliverables:**
- Updated `README.md`
- `docs/QUICK_START.md`
- `docs/ARCHITECTURE.md`
- `docs/WORKFLOW.md`

### Session 5: Validation & Handoff

**Goal:** Verify all work and create summary.

**Tasks:**
1. Run any existing tests
2. Validate type hints with `mypy` (if installed)
3. Verify documentation accuracy
4. Create `SPRINT_SUMMARY.md`:
   - What was accomplished
   - Files modified/created
   - Recommendations for v3.0 development
   - Estimated future token savings

**Deliverables:**
- `SPRINT_SUMMARY.md`
- Clean commit history

### Files You MAY Modify

| File | Modifications Allowed |
|------|----------------------|
| `.claude/agents/*.md` | Add docstrings, clarify instructions |
| `.claude/templates/*.md` | Fix formatting, add examples |
| `scripts/llm_backend.py` | Add type hints, improve errors |
| `config/settings.py` | Create new (Pydantic models) |
| `scripts/utils/logging.py` | Create new |
| `docs/*.md` | Create/update documentation |
| `README.md` | Update with current info |

### Files You MUST NOT Modify

| File | Reason |
|------|--------|
| `scripts/process_queue_visual.py` | Production TUI |
| `scripts/process_queue_auto.py` | Production processor |
| `scripts/orchestrator.py` | v3.0 development (local) |
| `mcp-server/*` | Production MCP tools |
| `.processing-requests.json` | Production queue state |
| `dashboard.db` | Production database |

---

## Part 9: Development Roadmap

### Phase 1: The Iron Core (State & Logic) - ✅ COMPLETE

**Goal:** Replace brittle JSON files with robust database and decoupled worker.

| Task | Status | Notes |
|------|--------|-------|
| Schema design (jobs, session_stats) | ✅ Done | `config/dashboard_schema.sql` |
| Migration script (JSON → SQLite) | ✅ Done | 17 jobs migrated |
| Orchestrator refactor | ✅ Done | `scripts/orchestrator.py` (553 lines) |
| Database connection management | ✅ Done | Thread-safe connections |

### Phase 2: The Nervous System (API Layer)

**Goal:** Enable external control without touching files, plus infrastructure reliability improvements from agent feedback.

| Task | Priority | Complexity | Agent Assignment |
|------|----------|------------|------------------|
| FastAPI project setup | High | Low | CLI-Agent (Gemini) |
| Core endpoints (queue CRUD) | High | Medium | Claude Code |
| Job control endpoints (pause/resume/retry) | High | Medium | Claude Code |
| WebSocket event system | Medium | High | Claude Code |
| Pydantic models for validation | Medium | Low | CLI-Agent (Gemini) |
| OpenAPI documentation | Low | Low | CLI-Agent (Gemini) |
| Authentication (optional) | Low | Medium | Defer to Phase 4 |
| **Stale job recovery** (heartbeat, auto-reset) | High | Medium | Claude Code |
| **Step-level status tracking** (resumable workflows) | High | Medium | Claude Code |
| **SRT speaker normalization** (pre-processing) | Medium | Medium | Claude Code |
| **Dynamic model registry** (fetch pricing/capabilities) | Medium | Medium | Claude Code |
| **OpenRouter vs DIY analysis** (pending docs review) | High | Low | Research task |

**Estimated Duration:** 4-5 focused development sessions (padded per Gemini review)

**Blocking dependency:** OpenRouter analysis should complete before implementing dynamic model registry to determine architecture (Option A vs B).

**Infrastructure tasks (from Gemini review):**
- SQLite schema migrations via Alembic
- SQLite backup strategy (daily snapshots, pre-upgrade backups)
- Prompt versioning system for agent prompts

### Phase 3: The Face (Web & Visuals)

**Goal:** Visually appealing, substantially complete interface with unified queue + editing workspace.

| Task | Priority | Complexity | Agent Assignment |
|------|----------|------------|------------------|
| React + Vite + Tailwind setup | High | Low | CLI-Agent (Gemini) |
| Dashboard page (queue + stats) | High | Medium | Claude Code |
| Queue management (drag-drop) | High | High | Claude Code |
| **Project workspace panel** | High | High | Claude Code |
| **Document viewer (markdown)** | High | Medium | Claude Code |
| **Embedded chat component** | High | High | Claude Code |
| Job detail page | Medium | Medium | CLI-Agent (Claude) |
| Analytics page | Medium | Medium | Parallel: Explore agent |
| Settings page | Low | Low | CLI-Agent (Gemini) |
| WebSocket integration | High | Medium | Claude Code |
| **Copy-to-clipboard helpers** | Medium | Low | CLI-Agent (Gemini) |
| Dark mode support | Low | Low | CLI-Agent (Gemini) |
| Mobile-responsive layout | Medium | Medium | CLI-Agent (Gemini) |

**Estimated Duration:** 5-6 focused development sessions (padded per Gemini review - React from scratch is aggressive)

### Phase 4: Polish & Integration

**Goal:** Production-ready with all integrations.

| Task | Priority | Complexity | Agent Assignment |
|------|----------|------------|------------------|
| CLI-Agent MCP integration | High | Medium | Claude Code |
| Chat agent workflow (copy-editor) | High | High | Claude Code |
| **Large transcript chunking** | High | High | Claude Code |
| **Parallel chunk processing** | Medium | High | Claude Code |
| Eject button implementation | Medium | Medium | Claude Code |
| Smart retry logic | Medium | Low | CLI-Agent (Claude) |
| Screenshot ingestion | Low | Medium | Defer |
| CMS direct push (hooks) | Low | High | Defer |
| Mobile-responsive web | Low | Low | CLI-Agent (Gemini) |
| User onboarding flow | Medium | Medium | Claude Code |

**Large Transcript Chunking Strategy:**
- Transcripts >100K chars split into overlapping chunks for parallel formatting
- Each chunk assigned to separate CLI-Agent instance
- Results merged with overlap deduplication
- Holistic tasks (brainstorming, titles) use summarized context or full text with larger-context model
- Size estimation warns before processing transcripts >200K chars

**Estimated Duration:** 4-5 focused development sessions (padded per Gemini review)

### Phase 5: Documentation & Release

| Task | Priority | Agent Assignment |
|------|----------|------------------|
| User documentation (HOW_TO_USE.md) | High | CLI-Agent (Claude) |
| API documentation | Medium | Auto-generated from OpenAPI |
| Developer setup guide | High | Claude Code |
| Video walkthrough | Low | Human |
| Changelog consolidation | Medium | CLI-Agent (Gemini) |

---

## Part 10: Parallel Development Strategy

### Agent Collaboration Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR / AGENT COLLABORATION                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CLAUDE CODE (ORCHESTRATOR)                        │   │
│  │                                                                      │   │
│  │  Responsibilities:                                                   │   │
│  │  • Complex architectural decisions                                   │   │
│  │  • Multi-file refactoring                                           │   │
│  │  • Integration between components                                    │   │
│  │  • Code review and quality assurance                                │   │
│  │  • Debugging complex issues                                          │   │
│  │  • User-facing workflow design                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CLI-AGENT (WORKER POOL)                           │   │
│  │                                                                      │   │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │   │
│  │  │  Gemini Agent     │  │  Claude Agent     │  │  Codex Agent    │  │   │
│  │  │                   │  │                   │  │  (if available) │  │   │
│  │  │  Good for:        │  │  Good for:        │  │                 │  │   │
│  │  │  • Boilerplate    │  │  • Documentation  │  │  Good for:      │  │   │
│  │  │  • Simple CRUD    │  │  • Explanations   │  │  • Code review  │  │   │
│  │  │  • Config files   │  │  • Copy editing   │  │  • Bug finding  │  │   │
│  │  │  • Test stubs     │  │  • User stories   │  │                 │  │   │
│  │  │  • CSS/styling    │  │  • Quality review │  │                 │  │   │
│  │  └───────────────────┘  └───────────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SPECIALIZED CLAUDE AGENTS                         │   │
│  │                                                                      │   │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │   │
│  │  │  Explore Agent    │  │  Plan Agent       │  │ Code Trouble-   │  │   │
│  │  │                   │  │                   │  │ shooter Agent   │  │   │
│  │  │  Good for:        │  │  Good for:        │  │                 │  │   │
│  │  │  • Codebase       │  │  • Architecture   │  │  Good for:      │  │   │
│  │  │    exploration    │  │    planning       │  │  • Debugging    │  │   │
│  │  │  • Finding files  │  │  • Breaking down  │  │    failed code  │  │   │
│  │  │  • Understanding  │  │    complex tasks  │  │  • Root cause   │  │   │
│  │  │    patterns       │  │  • Trade-off      │  │    analysis     │  │   │
│  │  │                   │  │    analysis       │  │                 │  │   │
│  │  └───────────────────┘  └───────────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Task Assignment Guidelines

| Task Type | Primary Agent | Rationale |
|-----------|---------------|-----------|
| **Architectural decisions** | Claude Code | Needs full context, multi-file awareness |
| **New feature implementation** | Claude Code | Complex integration |
| **Boilerplate/scaffolding** | CLI-Agent (Gemini) | Repetitive, well-defined |
| **Pydantic models** | CLI-Agent (Gemini) | Schema → code translation |
| **CSS/Tailwind styling** | CLI-Agent (Gemini) | Visual, low-risk |
| **API endpoint stubs** | CLI-Agent (Gemini) | Template-based |
| **Documentation writing** | CLI-Agent (Claude) | Quality prose |
| **User story refinement** | CLI-Agent (Claude) | Clear communication |
| **Code review** | CLI-Agent (Codex) | Independent perspective |
| **Codebase exploration** | Explore Agent | Efficient search |
| **Implementation planning** | Plan Agent | Structured breakdown |
| **Debugging failures** | Code Troubleshooter | Root cause focus |

### Parallelization Opportunities

**Phase 2 (API Layer):**
```
Parallel Stream A: FastAPI setup + Pydantic models (CLI-Agent Gemini)
Parallel Stream B: Core endpoint logic (Claude Code)
Merge Point: Integration testing
```

**Phase 3 (Web Dashboard):**
```
Parallel Stream A: React component scaffolding (CLI-Agent Gemini)
Parallel Stream B: State management + WebSocket (Claude Code)
Parallel Stream C: Analytics calculations (Explore Agent for research)
Merge Point: Full page integration
```

---

## Part 11: Open Questions & Decisions

### Resolved

| Question | Decision | Rationale |
|----------|----------|-----------|
| SQLite vs Postgres? | SQLite | Single-user, local-first, simpler deployment |
| FastAPI vs Flask? | FastAPI | Async support, auto OpenAPI docs, Pydantic native |
| React vs Vue vs Svelte? | React | Larger ecosystem, more familiar, Tailwind works well |
| **Authentication?** | Local-only (no auth) | Single user, local tool for foreseeable future. Remote access deferred to post-v3.0. |
| **Artifact delivery?** | Both (adaptive) | Always save to disk; also emit Claude Artifacts in Desktop, show inline in web. Interface detection via MCP presence or API headers. |
| **Deployment model?** | Single entry point | One `python run.py` starts orchestrator + API + serves web. Flags available for running components separately if needed. |
| **Testing strategy?** | Phased approach | Phase 2: critical path tests (queue, jobs, API). Phase 3: key web workflow integration tests. Phase 4: E2E for copy-editor chat. |

### Still Open

| Question | Options | Decision Needed By |
|----------|---------|-------------------|
| **Redis for job queue?** | SQLite polling vs. Redis pub/sub | Post-v3.0 (if remote processing needed) |
| **Remote processing?** | Local only vs. Optional remote worker | Post-v3.0 |
| **Notification system?** | None vs. Desktop notifications vs. Email | Post-v3.0 |

### v3.0 Enhancement Notes (December 2024)

#### Model Delegation for Cost Optimization

**Issue:** Both chat agent (Claude Code) and CLI agent should delegate brainstorming/transcript tasks to cheaper, faster models. Currently:
- Chat agent (`/brainstorm`, `/process-transcript`) runs directly with Claude Code's model (Opus/Sonnet)
- CLI agent uses `openai-mini` by default but doesn't explicitly configure `BACKEND_PREFERENCES`

**Note:** OpenAI-Mini struggled with long transcripts; Gemini models performed better.

**Recommendations:**
1. **Chat Agent**: Update slash commands to delegate to CLI-Agent or use OpenRouter model selection for transcript analysis tasks
2. **CLI Agent**: Configure to use OpenRouter model selection or explicitly prefer Gemini models for long-form transcript processing
3. **Config**: Ensure `llm-config.json` includes Gemini backends (e.g., `gemini-flash`) as preferred options for transcript tasks

#### Status Page Visibility Improvements

**Issue:** Dashboard doesn't clearly show:
1. Whether watch script is running
2. Incremental progress on each transcript
3. How long until new transcripts appear / processing completes

**Recommendations:**
1. **Watch Script Indicator**: Add header indicator showing `[WATCHING]` or `[WATCH: OFF]`
   - Check for PID file or `pgrep -f watch-transcripts`
2. **Per-Transcript Progress**: Show granular progress in queue table (e.g., `[████░░] 67%`)
   - Track phases: loading (10%), analyst (10-50%), formatter (50-90%), saving (90-100%)
3. **Time-to-Next Visibility**: Display countdown for next scan and queue completion estimates
   - `Next scan: 45s` | `Queue empty in: ~5 min`

---

## Part 12: Success Metrics

### v3.0 Release Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Queue reliability** | 99% jobs complete without manual intervention | Success rate over 100 jobs |
| **API coverage** | All queue operations available via API | Endpoint checklist |
| **Web dashboard** | Usable for daily workflow | User testing (self) |
| **Cost tracking** | Accurate to within 5% | Compare to API billing |
| **Response time** | Dashboard loads in <2s | Lighthouse score |
| **Documentation** | New user can onboard in <30min | Timed test |

### Long-term Goals (Post-v3.0)

- **Multi-user support**: Separate queues/projects per user
- **Team features**: Shared project review, approval workflows
- **Mobile app**: Push notifications, quick status checks
- **Plugin system**: Custom agents, external integrations
- **Self-hosted option**: Docker compose for easy deployment
- **Remote API access**: Simple token auth for accessing from other devices
- **Embedded web chat (v4.0)**: Build a chat interface directly into the web dashboard for copy-editor workflow, eliminating need for Claude Desktop. Would include:
  - WebSocket-based real-time messaging with LLM backend
  - Chat session persistence and history
  - File attachment handling (screenshots, drafts)
  - Artifact rendering inline (revision documents)
  - Project context auto-loading (brainstorming, transcript)
  - **Note:** Deferred from v3.0 to reduce scope. v3.0 uses Claude Desktop for copy-editor chat; web dashboard is monitoring/queue management only.
- **Collaborative document editing (v4.0 vision)**: Integration with Google Docs or similar, where agent writes to a live document, user edits directly, agent reviews changes - true back-and-forth collaboration like working with a human editor
  - **Note (from Gemini review):** This is a significant re-architecture, not an incremental upgrade. Would require real-time sync, potentially CRDTs/OTs, robust auth, and fundamental changes to the data layer. Plan accordingly.
- **Production deployment hardening (v4.0)**: ASGI server (Gunicorn + Uvicorn), process management (systemd/supervisor), environment variable management for different deployment contexts

### Remote Deployment Options (v4.0 Consideration)

Moving from local-only to remote operation. Three options, in order of increasing impact and requirements:

| Option | Description | Cost | Requirements to Proceed |
|--------|-------------|------|------------------------|
| **A. Proxmox (Self-Hosted)** | Run on home network VM | ~$0/month (electricity) | Docker packaging, remote MCP transport, basic auth |
| **B. Cloud VPS** | DigitalOcean, Linode, etc. | $5-25/month + LLM costs | Same as A, plus domain/SSL, hardened security |
| **C. PBSWI Engineering Infrastructure** | Integrated into station's automated post-processing suite | $0 (absorbed by station) | **High bar** - see below |

#### Option C Requirements (PBSWI Engineering)

For the station to consider adopting this tool:

| Requirement | Why It Matters | v3.0 Status |
|-------------|----------------|-------------|
| **Rock-solid reliability** | Can't break their pipeline | Partial - adding heartbeat, recovery |
| **Predictable, low cost** | They won't approve open-ended LLM spend | Needs cost caps, budget alerts |
| **Easy integration** | Must fit their existing workflows | Needs API, possibly auto-ingest |
| **Minimal maintenance** | Engineering can't babysit it | Needs self-healing, good logging |
| **Clear documentation** | Handoff to their team | Phase 5 deliverable |
| **Proven track record** | "It works for me" isn't enough | Needs months of stable production use |

#### Auto-Ingest Considerations (All Remote Options)

If deployed remotely with access to caption sources (e.g., mmingest.pbswi.wisc.edu):

**Filtering is essential** - not every video needs SEO metadata. Options:
- Show whitelist (auto-process specific programs)
- Manual approval queue (review before processing)
- Keyword/date filters
- Hybrid approach

**Estimated volume:** 40-200 videos/month × $0.03-0.15 = $4-20/month LLM cost if processing everything. Filtering reduces this significantly.

#### Recommendation

Focus v3.0 on local reliability and cost optimization. Remote deployment becomes viable for v4.0 once:
1. Months of stable local production use
2. Cost tracking proves predictable spend
3. Dynamic model registry minimizes per-transcript cost
4. Documentation is complete enough for handoff

The PBSWI Engineering option is the "north star" - if the tool is good enough for them, it's good enough for anyone.

### Graceful Degradation: Prompt-Only Fallback

**Goal:** If MCP server is unavailable, the editor agent should still function in a reduced-capability mode using only the system prompt and knowledge files.

#### Two Operating Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OPERATING MODES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FULL MODE (MCP Available)                                                  │
│  ─────────────────────────                                                  │
│  ├── Queue management (list, prioritize, monitor)                           │
│  ├── Project file access (read transcripts, deliverables)                   │
│  ├── Automated processing (trigger jobs, track status)                      │
│  ├── Revision saving (auto-increment versions)                              │
│  └── Real-time status updates                                               │
│                                                                             │
│  PROMPT-ONLY MODE (MCP Unavailable)                                         │
│  ──────────────────────────────────                                         │
│  ├── Manual transcript input (user pastes into chat)                        │
│  ├── Brainstorming via conversation                                         │
│  ├── Copy revision via conversation                                         │
│  ├── User manually saves outputs                                            │
│  └── Works from Claude web, desktop, mobile - anywhere                      │
│                                                                             │
│  DETECTION                                                                  │
│  ─────────                                                                  │
│  On session start, agent checks for MCP tools:                              │
│  ├── MCP tools present? → Full mode, greet with project status              │
│  └── No MCP tools? → Prompt-only mode, explain manual workflow              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Capability Comparison

| Capability | Full Mode | Prompt-Only Mode |
|------------|-----------|------------------|
| Transcript input | Load from queue/files | User pastes into chat |
| Brainstorming | Auto-saved to project | Output in chat, user saves |
| Copy revision | Versioned, auto-saved | Output in chat, user saves |
| Queue management | Full control | Not available |
| Project history | Access all deliverables | User must provide context |
| Keyword research | Access brainstorming doc | User provides or agent regenerates |
| Platform | Claude Desktop + MCP | Any Claude interface |

#### Agent Greeting by Mode

**Full Mode:**
```
I see you're connected to the Editorial Assistant. You have 3 projects
in queue and 2WLI1206HD is ready for editing.

What would you like to work on?
```

**Prompt-Only Mode:**
```
I'm running in prompt-only mode (MCP server not detected). I can still
help with transcript analysis and copy editing, but you'll need to:
- Paste transcripts directly into our chat
- Save any outputs manually to your project folders

To get full functionality, start the MCP server with `python run.py`.

Ready to work on a transcript? Paste it here or tell me what you need.
```

#### Implementation

```python
# In editor agent system prompt / startup logic

def detect_mode():
    """Check if MCP tools are available."""
    try:
        # Attempt to call a simple MCP tool
        result = mcp__editorial-assistant__get_queue_status()
        return "full"
    except:
        return "prompt-only"

# Agent behavior adapts based on mode
MODE = detect_mode()

if MODE == "full":
    # Load project context, show status, offer queue management
    ...
else:
    # Explain limitations, offer manual workflow
    ...
```

#### Knowledge Folder for Prompt-Only Mode

The prompt-only mode relies on a Claude Project with:

```
project-knowledge/
├── EDITOR_AGENT_INSTRUCTIONS.md    # Full system prompt
├── templates/
│   ├── brainstorming_template.md
│   ├── copy_revision_template.md
│   └── keyword_report_template.md
├── style-guides/
│   ├── ap_style_reference.md
│   └── pbs_brand_guidelines.md
└── examples/
    ├── good_brainstorming_example.md
    └── good_revision_example.md
```

This ensures consistent output quality even without MCP infrastructure.

#### Benefits

| Benefit | Description |
|---------|-------------|
| **Resilience** | Work continues even if local server is down |
| **Portability** | Use from any device without setup |
| **Onboarding** | New users can try before setting up infrastructure |
| **Emergency fallback** | Always have a working path |
| **Travel/mobile** | Quick edits from phone or borrowed computer |

#### Observability Strategy (v3.0 vs v4.0)

| Version | Environment | LLM Sources | Observability Approach |
|---------|-------------|-------------|------------------------|
| **v3.0** | Local | OpenRouter + CLI-Agent | Current tracking (manifest, session_stats). CLI-Agent usage is "free tier" via local CLI subscriptions. |
| **v4.0** | Remote | OpenRouter only | **Langfuse** (self-hosted). CLI-Agent impractical on remote server. All costs are 1:1 metered, precise tracking essential. |

**Why defer Langfuse to v4.0:**
- v3.0 runs locally where CLI-Agent defrays costs with existing subscriptions
- CLI-Agent calls are opaque to Langfuse anyway (bypass our code)
- When remote, CLI-Agent isn't available, so all LLM calls go through OpenRouter
- OpenRouter → Langfuse broadcast gives full visibility on 100% of costs
- Simpler v3.0, better observability when it actually matters (production/remote)

---

## Appendix A: File Structure (Target)

```
editorial-assistant/
├── .claude/
│   ├── agents/                 # Agent system prompts
│   ├── commands/               # Slash commands
│   └── templates/              # Output templates
├── api/                        # NEW: FastAPI application
│   ├── __init__.py
│   ├── main.py                 # App entry point
│   ├── routers/
│   │   ├── queue.py
│   │   ├── jobs.py
│   │   ├── system.py
│   │   ├── config.py
│   │   └── analytics.py
│   ├── models/                 # Pydantic models
│   │   ├── job.py
│   │   ├── config.py
│   │   └── events.py
│   ├── services/
│   │   ├── database.py
│   │   ├── orchestrator.py
│   │   └── model_router.py
│   └── websocket.py
├── web/                        # NEW: React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── lib/
│   ├── package.json
│   └── vite.config.ts
├── scripts/                    # Processing scripts
│   ├── orchestrator.py         # Database-backed worker
│   ├── llm_backend.py          # Model router
│   └── dashboard/              # TUI components
├── config/
│   ├── dashboard_schema.sql
│   ├── llm-config.json
│   └── settings.py             # NEW: Pydantic settings
├── mcp-server/                 # Claude Desktop integration
├── transcripts/                # Input files
├── OUTPUT/                     # Processed projects
├── docs/
│   ├── USER_GUIDE.md
│   ├── API.md
│   └── archive/
├── dashboard.db                # SQLite database
├── CLAUDE.md
├── DESIGN_v3.0.md              # This document
└── README.md
```

---

## Appendix B: Migration Checklist

### Before v3.0 Release

- [ ] All queue operations work via API
- [ ] Web dashboard deployed and functional
- [ ] TUI updated to use API (not direct file access)
- [ ] MCP server updated to use API
- [ ] Database migration script tested
- [ ] Backup/restore procedure documented
- [ ] Cost tracking validated against actual bills
- [ ] All 4 agents working with new orchestrator
- [ ] Documentation complete and reviewed

### Cleanup

- [ ] Remove `.processing-requests.json` dependency
- [ ] Archive `process_queue_visual.py` (replaced by API + TUI client)
- [ ] Consolidate working docs to `docs/archive/`
- [ ] Update CLAUDE.md with v3.0 commands
- [ ] Tag release in git

---

*This document is a living specification. Update as decisions are made and implementation progresses.*

---

## Appendix C: Detailed Development Roadmap (December 2024)

This appendix provides a sprint-level breakdown of the v3.0 development roadmap, organized around the orchestrator/agent framework.

### Orchestrator/Agent Framework Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    v3.0 DEVELOPMENT ORCHESTRATION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLAUDE CODE (MAIN ORCHESTRATOR)                                            │
│  ────────────────────────────────                                           │
│  • Owns complex architectural decisions                                     │
│  • Handles multi-file integrations                                          │
│  • Performs code review of agent outputs                                    │
│  • Manages task dependencies and sequencing                                 │
│                                                                             │
│  CLI-AGENT POOL (PARALLEL WORKERS)                                          │
│  ─────────────────────────────────                                          │
│  • Gemini: Boilerplate, config, scaffolding, styling                       │
│  • Claude: Documentation, quality prose, user stories                       │
│  • Codex: Independent code review, bug finding (if available)              │
│                                                                             │
│  SPECIALIZED CLAUDE AGENTS                                                  │
│  ─────────────────────────────                                              │
│  • Explore: Codebase research, pattern discovery                           │
│  • Plan: Architecture breakdown, implementation strategy                    │
│  • Code-Troubleshooter: Debugging, root cause analysis                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sprint Structure

Each sprint is designed for 2-4 focused development sessions. Tasks are categorized by:
- **🔵 Orchestrator**: Claude Code handles directly (complex, multi-file)
- **🟢 CLI-Agent**: Delegated to external agents (boilerplate, docs, simple)
- **🟡 Parallel**: Can run simultaneously with other tasks
- **🔴 Blocking**: Must complete before next sprint begins

---

### PHASE 2: API Layer (4-5 Sprints)

#### Sprint 2.1: Foundation & Infrastructure Reliability

**Goal:** FastAPI setup + critical reliability improvements from agent feedback

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| FastAPI project setup (`api/` directory) | 🟢 CLI-Agent | Gemini | None | 1 session |
| Pydantic models for Job, Config, Events | 🟢 CLI-Agent | Gemini | FastAPI setup | 1 session |
| Database service layer (`api/services/database.py`) | 🔵 Orchestrator | Claude Code | Pydantic models | 1 session |
| **Heartbeat mechanism** for stale job recovery | 🔵 Orchestrator | Claude Code | Database service | 1 session |
| **Auto-reset stuck jobs** (>N minutes processing) | 🔵 Orchestrator | Claude Code | Heartbeat | 0.5 session |

**Parallelization:**
```
Stream A (Gemini): FastAPI setup → Pydantic models
Stream B (Claude Code): [waits for Pydantic] → Database service → Heartbeat
```

**Sprint 2.1 Exit Criteria:**
- [ ] `api/` directory structure exists with FastAPI app
- [ ] Pydantic models validate against existing database schema
- [ ] Jobs table has `last_heartbeat` column
- [ ] Stuck jobs auto-reset after 10 minutes with no heartbeat

---

#### Sprint 2.2: Core Queue API

**Goal:** Full queue management via REST API

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Queue router (`api/routers/queue.py`) | 🔵 Orchestrator | Claude Code | Sprint 2.1 | 1 session |
| Jobs router (`api/routers/jobs.py`) | 🔵 Orchestrator | Claude Code | Queue router | 1 session |
| **Step-level status tracking** | 🔵 Orchestrator | Claude Code | Jobs router | 1.5 sessions |
| System control endpoints (pause/resume) | 🟢 CLI-Agent | Gemini | Jobs router | 0.5 session |
| OpenAPI documentation review | 🟢 CLI-Agent | Claude | All endpoints | 0.5 session |

**Step-Level Status Design:**
```python
# Job phases tracked individually
class JobPhase(BaseModel):
    phase_name: str  # "analyst", "formatter", etc.
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    deliverable_path: Optional[str]
    error_message: Optional[str]

# Jobs can resume from last successful phase
class Job(BaseModel):
    phases: List[JobPhase]
    current_phase_index: int
    resumable: bool  # True if any phase completed
```

**Sprint 2.2 Exit Criteria:**
- [ ] All queue CRUD operations available via API
- [ ] Job pause/resume/retry endpoints working
- [ ] Phase-level status visible in job details
- [ ] Failed jobs can resume from last successful phase

---

#### Sprint 2.3: Real-time Events & Pre-processing

**Goal:** WebSocket events + SRT normalization

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| WebSocket event system (`api/websocket.py`) | 🔵 Orchestrator | Claude Code | Sprint 2.2 | 1.5 sessions |
| Event types (job_started, phase_completed, etc.) | 🟢 CLI-Agent | Gemini | WebSocket base | 0.5 session |
| **SRT speaker normalization** pre-processor | 🔵 Orchestrator | Claude Code | None (parallel) | 1.5 sessions |
| Integration with orchestrator (emit events) | 🔵 Orchestrator | Claude Code | Both above | 1 session |

**SRT Normalization Strategy:**
```python
def normalize_speaker_markers(transcript: str) -> str:
    """
    Standardize speaker markers before formatting:
    1. Detect all speaker patterns (full names, abbreviations)
    2. Map abbreviated names to full names
    3. Handle unmarked speaker changes via heuristics:
       - Question/answer patterns
       - Short interjections
       - Context clues
    4. Flag ambiguous sections for review
    """
```

**Parallelization:**
```
Stream A (Claude Code): WebSocket system → Integration
Stream B (Claude Code): SRT normalization (independent)
Merge: Integration pulls in normalization
```

**Sprint 2.3 Exit Criteria:**
- [ ] WebSocket endpoint emits job/phase events
- [ ] Events fire correctly during processing
- [ ] SRT transcripts normalized before formatter phase
- [ ] Ambiguous speaker sections flagged in manifest

---

#### Sprint 2.4: Dynamic Model Registry

**Goal:** Fetch real-time pricing, enable automatic model selection

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| **OpenRouter vs DIY analysis** (research) | 🟢 CLI-Agent | Claude | None | 1 session |
| Model registry service | 🔵 Orchestrator | Claude Code | Analysis complete | 1.5 sessions |
| Pricing fetch + cache layer | 🔵 Orchestrator | Claude Code | Registry service | 1 session |
| Local override configuration | 🟢 CLI-Agent | Gemini | Registry service | 0.5 session |
| Integration with llm_backend.py | 🔵 Orchestrator | Claude Code | All above | 1 session |

**Decision Point:** Based on OpenRouter analysis:
- **Option A (DIY):** Fetch from multiple sources, custom scoring
- **Option B (OpenRouter):** Single API, let them handle routing

**Sprint 2.4 Exit Criteria:**
- [ ] Architecture decision documented (OpenRouter vs DIY)
- [ ] Model pricing updated automatically (hourly or daily)
- [ ] Local pinning/blocking overrides work
- [ ] Model selection logged with reasoning

---

#### Sprint 2.5: Schema Migration & Backup

**Goal:** Safe database evolution, data protection

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Alembic setup for migrations | 🟢 CLI-Agent | Gemini | None | 0.5 session |
| Migration scripts for new columns | 🔵 Orchestrator | Claude Code | Alembic setup | 0.5 session |
| Backup script (daily snapshots) | 🟢 CLI-Agent | Gemini | None | 0.5 session |
| Pre-upgrade backup trigger | 🔵 Orchestrator | Claude Code | Backup script | 0.5 session |
| Prompt versioning system | 🔵 Orchestrator | Claude Code | None | 1 session |

**Sprint 2.5 Exit Criteria:**
- [ ] Database changes via migration scripts only
- [ ] Daily backup cron job configured
- [ ] Agent prompts have version frontmatter
- [ ] Prompt version logged in manifest per deliverable

---

### PHASE 3: Web Dashboard (5-6 Sprints)

#### Sprint 3.1: React Foundation

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Vite + React + TypeScript setup | 🟢 CLI-Agent | Gemini | None | 1 session |
| Tailwind CSS configuration | 🟢 CLI-Agent | Gemini | React setup | 0.5 session |
| Base layout components (header, sidebar) | 🟢 CLI-Agent | Gemini | Tailwind | 1 session |
| API client with TypeScript types | 🔵 Orchestrator | Claude Code | OpenAPI spec | 1 session |
| WebSocket hook (`useWebSocket`) | 🔵 Orchestrator | Claude Code | API client | 1 session |

---

#### Sprint 3.2: Dashboard Core

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Queue list component | 🔵 Orchestrator | Claude Code | Sprint 3.1 | 1 session |
| Job status cards | 🟢 CLI-Agent | Gemini | Queue list | 0.5 session |
| Real-time status updates (WebSocket) | 🔵 Orchestrator | Claude Code | WebSocket hook | 1 session |
| Today's stats panel | 🟢 CLI-Agent | Gemini | API client | 0.5 session |
| Processing now indicator | 🟢 CLI-Agent | Gemini | WebSocket hook | 0.5 session |

---

#### Sprint 3.3: Queue Management

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Drag-drop reordering | 🔵 Orchestrator | Claude Code | Queue list | 1.5 sessions |
| Priority buttons (up/down) | 🟢 CLI-Agent | Gemini | Queue list | 0.5 session |
| Job actions (pause, cancel, retry) | 🔵 Orchestrator | Claude Code | Job cards | 1 session |
| Add job modal | 🟢 CLI-Agent | Gemini | API client | 1 session |
| Bulk operations | 🔵 Orchestrator | Claude Code | Job actions | 0.5 session |

---

#### Sprint 3.4: Project Workspace

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| **Workspace panel layout** | 🔵 Orchestrator | Claude Code | Sprint 3.2 | 1 session |
| Deliverables list with status | 🔵 Orchestrator | Claude Code | Workspace panel | 1 session |
| **Markdown document viewer** | 🔵 Orchestrator | Claude Code | None (parallel) | 1.5 sessions |
| Copy-to-clipboard buttons | 🟢 CLI-Agent | Gemini | Document viewer | 0.5 session |
| Download buttons | 🟢 CLI-Agent | Gemini | Document viewer | 0.5 session |

---

#### ~~Sprint 3.5: Embedded Chat~~ → DEFERRED TO v4.0

**Scope Change:** Embedded chat deferred to v4.0. Copy-editor workflow will continue using Claude Desktop with MCP tools. Web dashboard focuses on queue management, project viewing, and analytics only.

See "Long-term Goals (Post-v3.0)" for v4.0 embedded chat scope.

---

#### Sprint 3.5: Analytics & Polish (was 3.6)

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Analytics page layout | 🟢 CLI-Agent | Gemini | Sprint 3.1 | 1 session |
| Cost charts (daily, by model) | 🔵 Orchestrator | Claude Code | Analytics layout | 1.5 sessions |
| Model performance table | 🟢 CLI-Agent | Gemini | Analytics layout | 0.5 session |
| Settings page | 🟢 CLI-Agent | Gemini | None | 1 session |
| Dark mode support | 🟢 CLI-Agent | Gemini | All pages | 1 session |
| Mobile responsive adjustments | 🟢 CLI-Agent | Gemini | All pages | 1 session |

---

### PHASE 4: Integration & Polish (4-5 Sprints)

#### Sprint 4.1: CLI-Agent Integration

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| CLI-Agent availability detection | 🔵 Orchestrator | Claude Code | None | 0.5 session |
| Routing layer (CLI → OpenRouter fallback) | 🔵 Orchestrator | Claude Code | Detection | 1.5 sessions |
| Cooldown logic for failed CLI agents | 🔵 Orchestrator | Claude Code | Routing layer | 0.5 session |
| Usage logging (which path taken) | 🔵 Orchestrator | Claude Code | Routing layer | 0.5 session |

---

#### Sprint 4.2: Large Transcript Handling

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| **Transcript size estimation** | 🔵 Orchestrator | Claude Code | None | 0.5 session |
| **Chunking strategy** (overlapping segments) | 🔵 Orchestrator | Claude Code | Size estimation | 1.5 sessions |
| Parallel chunk processing | 🔵 Orchestrator | Claude Code | Chunking | 1.5 sessions |
| Chunk merge with overlap dedup | 🔵 Orchestrator | Claude Code | Parallel processing | 1 session |
| Size warnings for >200K char transcripts | 🟢 CLI-Agent | Gemini | Size estimation | 0.5 session |

**Chunking Parameters:**
```python
CHUNK_CONFIG = {
    "threshold_chars": 100_000,      # When to start chunking
    "chunk_size": 50_000,            # Target size per chunk
    "overlap_chars": 2_000,          # Overlap for context
    "max_parallel": 3,               # Max concurrent CLI-Agent calls
    "merge_strategy": "dedupe_overlap"
}
```

---

#### Sprint 4.3: Copy-Editor Chat Workflow

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Chat session state model | 🔵 Orchestrator | Claude Code | Phase 3 complete | 1 session |
| Copy-editor agent integration | 🔵 Orchestrator | Claude Code | Session state | 1.5 sessions |
| Revision versioning (auto-increment) | 🔵 Orchestrator | Claude Code | Agent integration | 0.5 session |
| Artifact delivery (chat vs file) | 🔵 Orchestrator | Claude Code | Agent integration | 1 session |
| User feedback loop | 🔵 Orchestrator | Claude Code | All above | 1 session |

---

#### Sprint 4.4: Error Handling & Recovery

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Smart retry logic implementation | 🔵 Orchestrator | Claude Code | None | 1 session |
| Eject button (mid-stream interrupt) | 🔵 Orchestrator | Claude Code | None | 1 session |
| Dead letter queue for failed jobs | 🔵 Orchestrator | Claude Code | Retry logic | 0.5 session |
| Error message improvements | 🟢 CLI-Agent | Claude | None | 1 session |
| Troubleshooting documentation | 🟢 CLI-Agent | Claude | Error messages | 1 session |

---

### PHASE 5: Documentation & Release (2 Sprints)

#### Sprint 5.1: User Documentation

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| Update README.md | 🟢 CLI-Agent | Claude | All code complete | 0.5 session |
| QUICK_START.md guide | 🟢 CLI-Agent | Claude | README | 1 session |
| ARCHITECTURE.md with diagrams | 🟢 CLI-Agent | Claude | None | 1 session |
| WORKFLOW.md user journey | 🟢 CLI-Agent | Claude | None | 1 session |
| API documentation review | 🟢 CLI-Agent | Claude | OpenAPI | 0.5 session |

---

#### Sprint 5.2: Release Preparation

| Task | Type | Agent | Dependencies | Est. Effort |
|------|------|-------|--------------|-------------|
| E2E testing of critical paths | 🔵 Orchestrator | Claude Code | All code | 1 session |
| CHANGELOG consolidation | 🟢 CLI-Agent | Gemini | None | 0.5 session |
| Migration checklist validation | 🔵 Orchestrator | Claude Code | None | 0.5 session |
| Git tag and release notes | 🔵 Orchestrator | Claude Code | All above | 0.5 session |
| Cleanup deprecated files | 🔵 Orchestrator | Claude Code | All above | 0.5 session |

---

### Critical Path Dependencies

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CRITICAL PATH                                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 2.1 ─────▶ Phase 2.2 ─────▶ Phase 2.3 ─────▶ Phase 2.4             │
│  (FastAPI)        (Queue API)      (WebSocket)      (Model Registry)       │
│                                          │                                  │
│                                          ▼                                  │
│                                    Phase 3.1 ─────▶ Phase 3.2 ──...──▶ 3.6│
│                                    (React)          (Dashboard)             │
│                                                           │                 │
│                                                           ▼                 │
│                                    Phase 4.1 ─────▶ Phase 4.3              │
│                                    (CLI-Agent)      (Chat Workflow)        │
│                                                           │                 │
│                                          ┌────────────────┘                 │
│                                          ▼                                  │
│                                    Phase 5.1 ─────▶ Phase 5.2              │
│                                    (Docs)           (Release)               │
│                                                                             │
│  INDEPENDENT TRACKS (can run parallel to critical path):                   │
│  ─────────────────────────────────────────────────────                     │
│  • Phase 2.3b: SRT Normalization                                           │
│  • Phase 2.5: Schema Migrations & Backup                                   │
│  • Phase 4.2: Large Transcript Chunking                                    │
│  • Phase 4.4: Error Handling (after 4.1)                                   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| React learning curve | Medium | Medium | Start with CLI-Agent scaffolding, focus Claude Code on logic |
| WebSocket complexity | Medium | High | Design simple event schema first, test incrementally |
| CLI-Agent reliability | Medium | Medium | Always have OpenRouter fallback, graceful degradation |
| Large transcript edge cases | High | Medium | Test with real PBS transcripts early, document limits |
| Chat agent integration | Medium | High | Prototype early, iterate on prompt engineering |

### Success Metrics per Phase

| Phase | Key Metrics | Target |
|-------|-------------|--------|
| Phase 2 | API endpoint coverage | 100% of queue operations |
| Phase 2 | Job recovery rate | <1% stuck jobs after 24h |
| Phase 3 | Dashboard load time | <2s on localhost |
| Phase 3 | Mobile usability | All features accessible |
| Phase 4 | Large transcript success | 95%+ for transcripts >100K |
| Phase 4 | Chat revision loop | <3 iterations average |
| Phase 5 | Documentation coverage | All features documented |
| Phase 5 | New user onboarding | <30 min to first processed transcript |

---

### Gemini Review Integration (December 2024)

The roadmap was reviewed by Gemini (via CLI-Agent) with the following feedback integrated:

#### 1. Critical Path Revision

**Original Issue:** Jumping from React setup (3.1) directly to embedded chat (3.5) skips foundational UI.

**Resolution:** Critical path now explicitly includes intermediate steps:
```
2.1 → 2.2 → 2.3 → 2.5 (Alembic moved earlier) → 3.1 → 3.2 → 3.3 → 3.4 → 4.1 → 4.3 → 5.1 → 5.2
```

Embedded chat (3.5) moved to **parallel track** - can be deferred to v3.1 if timeline pressure.

#### 2. Alembic Timing Correction

**Original:** Alembic setup at end of Phase 2 (Sprint 2.5)

**Revised:** Alembic setup moves to Sprint 2.1, immediately after Pydantic models. Use migrations iteratively throughout API development.

#### 3. Effort Sizing Added

| Size | Tasks | Notes |
|------|-------|-------|
| **XL** | Embedded Chat (3.5), WebSocket Events (2.3) | High risk, consider deferring chat |
| **L** | Copy-editor Workflow (4.3), Large Transcript Chunking (4.2), Initial React UI (3.1-3.3) | Core business logic, learning curve |
| **M** | Database Service (2.1), Queue/Jobs Routers (2.2), E2E Testing (5.2) | Standard effort |
| **S** | FastAPI Setup, Pydantic Models, Heartbeat | Boilerplate |

#### 4. Enhanced Risk Mitigations

| Risk | Original Mitigation | Enhanced Mitigation |
|------|---------------------|---------------------|
| **CLI-Agent Reliability** | OpenRouter fallback | + JSON Schema contracts for all agent I/O, + Validation layer with intelligent retry, + Consider "Fixer" agent for output correction |
| **Large Transcripts** | Test early | + Context-aware chunking with overlapping segments, + Summarizer agent for context preservation across chunks |
| **Chat Complexity** | Prototype early | + Isolated PoC before integration, + Consider deferring to v3.1 MVP |

#### 5. Missing Tasks Added

| Task | Phase | Priority | Notes |
|------|-------|----------|-------|
| **CI/CD Pipeline** | 2.1 (parallel) | High | GitHub Actions for test/build automation |
| **Structured Logging** | 2.1 | Medium | JSON logging with log levels, observability prep |
| **Unit Tests per Sprint** | All | High | Tests written alongside features, not just E2E at end |
| **Tester Agent Role** | 4.1 | Medium | Agent to verify CLI-Agent outputs with tests |
| **API-First Contract** | 2.2 | High | OpenAPI spec as binding contract for frontend/agents |

#### 6. Scope Decision: Authentication

**Gemini noted:** Auth & authorization not mentioned.

**Resolution:** Per earlier design decisions, v3.0 is local-only, single-user. Auth deferred to v4.0 (remote deployment). This is documented in Part 11 (Open Questions - Resolved).

#### 7. Revised Sprint 2.1 (Foundation)

Sprint 2.1 now includes:
- FastAPI project setup
- Pydantic models
- **Alembic setup** (moved from 2.5)
- **CI/CD pipeline skeleton** (new)
- **Structured logging utility** (new)
- Database service layer
- Heartbeat mechanism

This front-loads infrastructure work for smoother iteration.

#### 8. Chat Feature Scope Decision

**Recommendation from Gemini:** Consider deferring embedded chat to v3.1.

**Decision: ACCEPTED** - Embedded chat moved to v4.0 roadmap. v3.0 scope:
- Web dashboard handles queue management, project viewing, analytics
- **Claude Desktop** handles copy-editor chat workflow (existing MCP integration)
- No custom chat UI in v3.0

This removes ~4.5 sessions of XL-complexity work and eliminates the highest-risk feature from v3.0. Phase 3 reduced from 6 sprints to 5.

---

## Appendix D: Future Enhancement Ideas

This section captures ideas for post-v3.0 enhancements. These are not committed to any roadmap.

### AirTable Integration for Initial Drafts

**Concept:** Editor agents query AirTable via MCP to pull existing draft content before processing.

**Workflow:**
1. When a job enters the editor phase, query AirTable's "Single Source of Truth" table by MediaID
2. If a matching record exists with draft content, pre-populate the editor agent's context
3. Editor agent refines existing draft rather than generating from scratch
4. Reduces duplicate work when partial drafts already exist in the content database

**Integration Points:**
- `api/services/airtable.py` - AirTable MCP client wrapper
- Editor agent system prompts - Instructions for handling pre-existing drafts
- Job model - Field to indicate draft source (generated vs. AirTable import)

**Prerequisites:**
- AirTable MCP server configured with valid token
- "Single Source of Truth" table schema documented
- MediaID field mapping confirmed

**Added:** 2025-12-23
