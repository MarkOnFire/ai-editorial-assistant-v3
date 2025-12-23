# Editorial Assistant v3.0

PBS Wisconsin Editorial Assistant - A system for processing video transcripts and generating SEO-optimized metadata (titles, descriptions, keywords) for streaming platforms.

## Overview

v3.0 represents an architectural evolution from v2.0:
- **API-first design** - FastAPI backend enables multiple interfaces
- **Database-backed state** - SQLite replaces JSON files
- **Web dashboard** - React-based monitoring and queue management
- **Claude Desktop integration** - MCP tools for copy-editor workflow

## Status

🚧 **Under Development** - Sprint 2.1 (Foundation)

See `DESIGN_v3.0.md` for full specification and roadmap.

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd editorial-assistant-v3
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize development session
./init.sh

# Start API server
uvicorn api.main:app --reload
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Claude    │     │    Web      │     │    CLI      │
│   Desktop   │     │  Dashboard  │     │  Commands   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │    API      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼───┐ ┌─────▼─────┐
       │ Orchestrator │ │SQLite │ │LLM Backend│
       │   (Worker)   │ │  DB   │ │  Router   │
       └──────────────┘ └───────┘ └───────────┘
```

## Development

See `CLAUDE.md` for development guidelines and `feature_list.json` for current tasks.

## License

Internal PBS Wisconsin tool - not for distribution.
