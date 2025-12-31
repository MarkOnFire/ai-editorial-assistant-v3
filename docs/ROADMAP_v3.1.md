# Editorial Assistant v3.1 Roadmap

## Vision

Transform the Editorial Assistant from a transcript processing pipeline into a fully integrated editorial workstation where:
1. **Airtable is the canonical source** - SST records drive context for all agents
2. **One-command editing** - Give a Media ID, get immediate access to everything
3. **Real-time visibility** - Live updates across dashboard and processing

---

## CRITICAL CONSTRAINT: Read-Only Airtable Access

**AI agents must NEVER write to Airtable.** All Airtable integration is READ-ONLY.

- Agents READ SST metadata to enhance their work (titles, descriptions, keywords)
- Users make ALL Airtable edits manually in the Airtable UI
- If asked to update Airtable, agents must decline and explain this policy
- The API token is configured as read-only, but this constraint is also enforced at the agent instruction level

This protects data integrity in the canonical Single Source of Truth database.

---

## Sprint 6: Airtable Deep Integration

### 6.1 SST Record Linking (Foundation)

**Goal:** Every job automatically links to its Airtable SST record.

| Task | Description | Files |
|------|-------------|-------|
| 6.1.1 | Add `airtable_record_id` and `airtable_url` fields to Job model | `api/models/job.py`, migration |
| 6.1.2 | Create Airtable service with MCP client wrapper | `api/services/airtable.py` |
| 6.1.3 | SST lookup by Media ID (extracted from filename) | `api/services/airtable.py` |
| 6.1.4 | Auto-link on job creation: extract Media ID → find SST record → store link | `api/routers/queue.py` |
| 6.1.5 | Display SST link in Job Detail page (opens Airtable) | `web/src/pages/JobDetail.tsx` |

**Airtable Details:**
- Base ID: `appZ2HGwhiifQToB6`
- Table: `✔️Single Source of Truth` (`tblTKFOwTvK7xw1H5`)
- Key field: `Media ID` (`fld8k42kJeWMHA963`)
- SST URL format: `https://airtable.com/appZ2HGwhiifQToB6/tblTKFOwTvK7xw1H5/{record_id}`

### 6.2 SST Context Injection

**Goal:** Agents receive relevant SST metadata to enhance their work.

| Task | Description | Files |
|------|-------------|-------|
| 6.2.1 | Fetch SST fields on job start: title, descriptions, keywords, tags | `api/services/worker.py` |
| 6.2.2 | Add `sst_context` to job processing context | `api/services/worker.py` |
| 6.2.3 | Update analyst prompt to use SST context (existing metadata awareness) | `.claude/agents/analyst.md` |
| 6.2.4 | Update formatter prompt with SST speaker/topic hints | `.claude/agents/formatter.md` |
| 6.2.5 | Update SEO prompt to align with existing SST descriptions | `.claude/agents/seo.md` |
| 6.2.6 | Update manager prompt to cross-reference against SST | `.claude/agents/manager.md` |

**SST Fields to Fetch:**
```
- Release Title (fldXqxjjxR4z5IJv6)
- Short Description (fldDwTtKlOCdgKHpW)
- Long Description (fld6HsWiKL77bFqo1)
- Social Media Tags (fldcenwfu4nEWjPbt)
- General Keywords/Tags (fldjdPEXZyvx3rc6Y)
- Media Manager Short Description (fldFdFQ2ZPKvcoP3y)
- Media Manager Long Description (fldQRiL4xYWt9UaqW)
- Host (fldezf5GBU6yxXxuO)
- Presenter (fld7KxmZqGH9pPHSQ)
- Project (fld3su0x59DeTog76) → links to Projects table
```

### 6.3 Copy Editor Workstation

**Goal:** Chat agent can start editing with just a Media ID.

| Task | Description | Files |
|------|-------------|-------|
| 6.3.1 | `/lookup <media_id>` slash command - finds job and SST record | `.claude/commands/lookup.md` |
| 6.3.2 | `/edit <media_id>` slash command - loads all context for editing | `.claude/commands/edit.md` |
| 6.3.3 | API endpoint: GET `/api/jobs/by-media-id/{media_id}` | `api/routers/jobs.py` |
| 6.3.4 | Include all agent outputs in edit context (analyst, formatter, seo, manager reports) | `api/routers/jobs.py` |
| 6.3.5 | Include SST metadata in edit context | `api/routers/jobs.py` |
| 6.3.6 | `/available` command - list jobs ready for editing (completed, not yet edited) | `.claude/commands/available.md` |

**Edit Context Bundle:**
```json
{
  "job": { "id": 123, "media_id": "2WLI1209HD", ... },
  "sst": {
    "record_id": "rec...",
    "url": "https://airtable.com/...",
    "title": "...",
    "short_description": "...",
    "long_description": "...",
    "keywords": [...],
    "tags": [...]
  },
  "outputs": {
    "analyst": "...",
    "formatter": "...",
    "seo": "...",
    "manager": "..."
  },
  "transcript": "..."
}
```

---

## Sprint 7: Real-Time & Polish

### 7.1 WebSocket Live Updates

**Goal:** Dashboard updates in real-time without polling.

| Task | Description | Files |
|------|-------------|-------|
| 7.1.1 | Add WebSocket endpoint `/ws/jobs` | `api/routers/websocket.py` |
| 7.1.2 | Emit events on job status change | `api/services/worker.py` |
| 7.1.3 | Emit events on phase completion | `api/services/worker.py` |
| 7.1.4 | Dashboard WebSocket client | `web/src/hooks/useWebSocket.ts` |
| 7.1.5 | Live queue updates | `web/src/pages/Queue.tsx` |
| 7.1.6 | Live job detail updates | `web/src/pages/JobDetail.tsx` |

### 7.2 Web UI Bulk Uploader

**Goal:** Drag-and-drop batch transcript upload.

| Task | Description | Files |
|------|-------------|-------|
| 7.2.1 | Upload page with dropzone | `web/src/pages/Upload.tsx` |
| 7.2.2 | File upload API endpoint | `api/routers/queue.py` |
| 7.2.3 | Batch job creation with SST auto-linking | `api/routers/queue.py` |
| 7.2.4 | Upload progress indicator | `web/src/pages/Upload.tsx` |
| 7.2.5 | Duplicate detection UI (show existing jobs) | `web/src/pages/Upload.tsx` |

### 7.3 Timestamp Agent (Optional)

**Goal:** Dedicated agent for timestamp refinement.

| Task | Description | Files |
|------|-------------|-------|
| 7.3.1 | Timestamp agent instructions | `.claude/agents/timestamp.md` |
| 7.3.2 | Add timestamp phase to worker (optional, configurable) | `api/services/worker.py` |
| 7.3.3 | SRT parsing and regeneration | `api/services/utils.py` |

---

## Implementation Priority

### Phase 1: SST Linking (Sprint 6.1) - HIGH
- Minimal effort, immediate value
- Every job gets an Airtable link
- Foundation for everything else

### Phase 2: Copy Editor Workstation (Sprint 6.3) - HIGH
- Biggest UX improvement
- `/edit 2WLI1209HD` gets you into editing immediately
- Requires 6.1 first

### Phase 3: SST Context Injection (Sprint 6.2) - MEDIUM
- Enhances agent quality
- Can be done incrementally (one agent at a time)

### Phase 4: Real-Time Updates (Sprint 7.1) - MEDIUM
- Nice to have, reduces polling
- More complex implementation

### Phase 5: Bulk Uploader (Sprint 7.2) - LOW
- `watch_transcripts.py` works for now
- Only needed for non-technical users

### Phase 6: Timestamp Agent (Sprint 7.3) - LOW
- Edge case optimization
- Formatter handles timestamps adequately

---

## Technical Notes

### Airtable MCP Integration

The Airtable MCP server is already configured and provides:
- `mcp__airtable__search_records` - Search by Media ID
- `mcp__airtable__get_record` - Fetch full record
- `mcp__airtable__list_records` - List available records

For the API service, we'll use direct Airtable API calls (not MCP) since the worker runs headless.

### Media ID Extraction

```python
def extract_media_id(filename: str) -> str:
    """Extract Media ID from transcript filename.

    Examples:
        2WLI1209HD_ForClaude.txt → 2WLI1209HD
        9UNP2005HD.srt → 9UNP2005HD
        2BUC0000HDWEB02_REV20251202.srt → 2BUC0000HDWEB02
    """
    # Remove extension and common suffixes
    base = Path(filename).stem
    base = re.sub(r'_ForClaude$', '', base)
    base = re.sub(r'_REV\d+$', '', base)
    return base
```

### SST Record URL Format

```
https://airtable.com/{base_id}/{table_id}/{record_id}
https://airtable.com/appZ2HGwhiifQToB6/tblTKFOwTvK7xw1H5/recXXXXXXXXXXXXXX
```

---

## Sprint 8: UX Improvements

**Source:** `docs/UX_IMPROVEMENT_SPRINT_PLAN.md` (comprehensive UX assessment)
**Current Score:** 5.4/10 composite | **Target:** 8.0/10

### 8.1 Critical Accessibility Foundation (CRITICAL - Blocks all others)

| Task | Agent | Description |
|------|-------|-------------|
| 8.1.1 | the-drone | Add skip navigation link |
| 8.1.2 | cli-agent/gemini | Add focus-visible states globally |
| 8.1.3 | the-drone | Fix color contrast violations (gray-600→gray-400) |
| 8.1.4 | the-drone | Add labels to form inputs |
| 8.1.5 | cli-agent/gemini | Add ARIA to navigation |
| 8.1.6 | the-drone | Fix modal accessibility (focus trap, escape key) |
| 8.1.7 | cli-agent/gemini | Add reduced motion support |
| 8.1.8 | the-drone | Add error announcements (role=alert) |

### 8.2 Interactive Feedback System (HIGH)

| Task | Agent | Description |
|------|-------|-------------|
| 8.2.1 | the-drone | Create Toast notification component |
| 8.2.2 | the-drone | Create ConfirmDialog component |
| 8.2.3 | the-drone | Replace native dialogs in Queue.tsx |
| 8.2.4 | cli-agent/gemini | Create LoadingSpinner component |
| 8.2.5 | the-drone | Create Skeleton loader components |
| 8.2.6 | the-drone | Replace loading text with skeletons |
| 8.2.7 | the-drone | Add action feedback to JobDetail |

### 8.3 Navigation & Wayfinding (HIGH)

| Task | Agent | Description |
|------|-------|-------------|
| 8.3.1 | the-drone | Fix back navigation (use history) |
| 8.3.2 | the-drone | Add Breadcrumb component |
| 8.3.3 | the-drone | Add System page to main nav |
| 8.3.4 | the-drone | Add filter counts to Queue tabs |
| 8.3.5 | the-drone | Implement instant search with debounce |
| 8.3.6 | the-drone | Add keyboard shortcuts (g+h, g+q, etc.) |

### 8.4 Cognitive Load Reduction (MEDIUM)

| Task | Agent | Description |
|------|-------|-------------|
| 8.4.1 | orchestrator | Refactor Settings page with tabs |
| 8.4.2 | the-drone | Simplify StatusBar information |
| 8.4.3 | cli-agent/gemini | Add relative time utilities |
| 8.4.4 | the-drone | Apply relative times throughout app |
| 8.4.5 | the-drone | Add duration to completed jobs |

### 8.5 Accessibility Preferences (LOW)

| Task | Agent | Description |
|------|-------|-------------|
| 8.5.1 | the-drone | Create Preferences context |
| 8.5.2 | the-drone | Add Accessibility settings section |
| 8.5.3 | the-drone | Apply preferences throughout app |

**New Files to Create:**
- `web/src/components/ui/Toast.tsx`
- `web/src/components/ui/ConfirmDialog.tsx`
- `web/src/components/ui/LoadingSpinner.tsx`
- `web/src/components/ui/Skeleton.tsx`
- `web/src/components/ui/Breadcrumb.tsx`
- `web/src/hooks/useFocusTrap.ts`
- `web/src/hooks/useDebounce.ts`
- `web/src/hooks/useKeyboardShortcuts.ts`
- `web/src/utils/formatTime.ts`
- `web/src/contexts/PreferencesContext.tsx`

**Estimated Effort:** 8-11 days of agent work

---

## Sprint 9: Testing & Bug Fixes

**Source:** Gemini code review (`SPRINT_PLAN.md`)

### 9.1 Bug Fixes (HIGH PRIORITY)

| Task | Agent | Description |
|------|-------|-------------|
| 9.1.1 | cli-agent/gemini | Fix race condition in `claim_next_job` - use atomic `UPDATE...RETURNING` |
| 9.1.2 | cli-agent/gemini | Robust `project_path` sanitization for invalid characters |
| 9.1.3 | cli-agent/gemini | Load worker defaults from `config/llm-config.json` |

### 9.2 Test Coverage (HIGH/MEDIUM PRIORITY)

| Task | Agent | Description |
|------|-------|-------------|
| 9.2.1 | orchestrator | Add tests for JobWorker (state machine, phase transitions, error handling) |
| 9.2.2 | cli-agent/gemini | Add tests for API endpoints (jobs.py, queue.py) |
| 9.2.3 | orchestrator | Add tests for LLMClient (mocking, cost tracking, safety guards) |
| 9.2.4 | cli-agent/gemini | Add tests for watch_transcripts.py |

### 9.3 Validation Review (HIGH PRIORITY)

| Task | Agent | Description |
|------|-------|-------------|
| 9.3.1 | cli-agent/gemini | Second round comprehensive code review after bug fixes |

**New Files to Create:**
- `tests/api/test_worker.py`
- `tests/api/test_jobs.py`
- `tests/api/test_queue.py`
- `tests/api/test_llm.py`
- `tests/test_watch_transcripts.py`

---

## Future (v4.0 and Beyond) - DEFERRED

These features are documented but explicitly deferred to post-v3.1:

### Remote Deployment & Multi-User

| Feature | Description | Requirements |
|---------|-------------|--------------|
| **VM Deployment** | Run on Proxmox/VPS with remote access | Docker packaging, process management |
| **Cloudflare Tunnel** | Secure remote access without port forwarding | Tunnel configuration, authentication |
| **Simple Token Auth** | Basic authentication for remote API access | Token generation, validation middleware |
| **Multi-user Support** | Separate queues/projects per user | User model, data isolation, auth system |
| **Team Features** | Shared project review, approval workflows | Roles, permissions, notifications |

### Embedded Chat Interface (v4.0)

**Status:** Explicitly tabled for future version.

Build chat interface directly into web dashboard for copy-editor workflow:
- WebSocket-based real-time messaging with LLM backend
- Chat session persistence and history
- File attachment handling (screenshots, drafts)
- Artifact rendering inline (revision documents)
- Project context auto-loading

**Note:** v3.x uses Claude Desktop/Code for copy-editor chat; web dashboard is monitoring/queue management only.

### Advanced Integrations

| Feature | Description | Complexity |
|---------|-------------|------------|
| **SEMRush Data Integration** | See notes below - API not available | Medium |
| **CMS Direct Push** | Auto-publish metadata to CMS | High |
| **Google Docs Integration** | Real-time collaborative editing | Very High |
| **Mobile App** | Push notifications, quick status checks | High |
| **Plugin System** | Custom agents, external integrations | High |

#### SEMRush Integration Options (No API Access)

Since SEMRush API access is not available, alternative approaches to explore:

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Screenshot Analysis** | User takes screenshot, agent analyzes via vision | Works now, no setup | Manual, limited data extraction |
| **CSV Export** | User exports data from SEMRush, uploads to app | Structured data, accurate | Extra user steps |
| **Browser Extension** | Custom extension scrapes visible data | Could automate extraction | Development overhead, TOS concerns |
| **Copy-Paste Templates** | Formatted text areas for pasting SEMRush output | Simple, reliable | Manual formatting |
| **Alternative Tools** | Explore free/open keyword research APIs | No SEMRush dependency | Different data quality |

**Recommended approach for v3.1:** Improve the screenshot workflow with better prompts and copy-ready keyword formatting. Explore CSV export as a cleaner alternative for users willing to do the extra step.

### Production Hardening

| Feature | Description |
|---------|-------------|
| **ASGI Server** | Gunicorn + Uvicorn for production |
| **Process Management** | systemd/supervisor configuration |
| **Docker Compose** | Easy self-hosted deployment |
| **Backup Strategy** | Automated database snapshots |

### PBSWI Engineering Integration (North Star)

For the station to adopt this tool into their automated post-processing pipeline:
- Rock-solid reliability (months of stable production use)
- Predictable, low cost (proven cost tracking)
- Easy integration (API, auto-ingest from caption sources)
- Minimal maintenance (self-healing, good logging)
- Clear documentation (handoff-ready)

---

## Success Metrics

1. **SST Link Rate**: % of jobs with valid Airtable links (target: 95%+)
2. **Edit Session Time**: Time from `/edit` to first revision (target: <30s)
3. **Agent Quality**: Manager approval rate with SST context (target: improvement)
4. **Dashboard Latency**: Time for status updates to appear (target: <1s with WebSocket)
