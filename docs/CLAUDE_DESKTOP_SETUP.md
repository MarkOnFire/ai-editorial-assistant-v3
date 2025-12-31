# Claude Desktop Setup for Editorial Assistant

This guide explains how to configure Claude Desktop to use the Editorial Assistant MCP server for interactive copy editing.

## Prerequisites

1. **Claude Desktop** installed on your Mac
2. **Editorial Assistant v3** running locally
3. **Python 3.10+** with the project's virtual environment

## Quick Setup

### 1. Locate your Claude Desktop config file

```bash
# The config file is at:
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 2. Add the Editorial Assistant MCP server

Edit the config file and add the `editorial-assistant` server:

```json
{
  "mcpServers": {
    "editorial-assistant": {
      "command": "/Users/YOUR_USERNAME/Developer/ai-editorial-assistant-v3/venv/bin/python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "/Users/YOUR_USERNAME/Developer/ai-editorial-assistant-v3"
    }
  }
}
```

**Important**: Replace `YOUR_USERNAME` with your actual macOS username.

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop for the changes to take effect.

### 4. Verify the connection

In a new Claude Desktop conversation, you should be able to say:

> "What projects are ready for editing?"

Claude will use the `list_processed_projects()` tool to show you available projects.

## Available Tools

Once configured, Claude has access to these tools:

| Tool | Description |
|------|-------------|
| `list_processed_projects()` | Discover processed projects ready for editing |
| `load_project_for_editing(name)` | Load full context for an editing session |
| `get_formatted_transcript(name)` | Load AP Style transcript for fact-checking |
| `save_revision(name, content)` | Save copy revision with auto-versioning |
| `save_keyword_report(name, content)` | Save SEO/keyword report |
| `get_project_summary(name)` | Quick status check |
| `read_project_file(name, filename)` | Read specific project file |

## Usage Examples

### Start an editing session

Just tell Claude what you want to do:

> "I'd like to edit 2WLI1209HD"

Claude will:
1. Load the project context (brainstorming, existing revisions)
2. Present the AI-generated content for review
3. Ask how you'd like to proceed

### Review available projects

> "What projects are ready for editing?"

or

> "Show me projects that have revisions in progress"

### Fact-check against transcript

> "Can you check the speaker names in this description against the transcript?"

Claude will load the formatted transcript and verify accuracy.

### Save your work

When you approve a revision, Claude will automatically save it:

> "This looks good, please save it"

Claude saves with auto-versioning (v1, v2, v3...) and confirms the file path.

## Troubleshooting

### Server not connecting

1. **Check the path**: Ensure the Python path in the config matches your actual venv location
2. **Check permissions**: The venv Python must be executable
3. **Check dependencies**: Run `./venv/bin/pip install mcp` if not already installed

### "Project not found" errors

1. **Ensure the API is running**: Start with `uvicorn api.main:app --reload`
2. **Check OUTPUT folder**: Projects must have a `manifest.json` in `OUTPUT/{project_name}/`

### Viewing server logs

Claude Desktop logs MCP server output. Check:
```bash
# Claude Desktop logs
~/Library/Logs/Claude/
```

### Testing the server manually

```bash
cd /Users/YOUR_USERNAME/Developer/ai-editorial-assistant-v3
./venv/bin/python -m mcp_server.server
```

This runs in stdio mode - you'll see it waiting for input (that's normal).

## Project Knowledge Folder

For the best experience, add these to your Claude Desktop project's knowledge folder:

1. **`agent-instructions/EDITOR_AGENT_INSTRUCTIONS.md`** - Full editing workflow and templates
2. **AP Stylebook reference** (if you have a PDF)
3. **Program-specific style guides** (University Place, Here and Now, etc.)

This gives Claude the context to follow PBS Wisconsin's editorial standards.

## Full Config Example

Here's a complete example config with the Editorial Assistant:

```json
{
  "mcpServers": {
    "editorial-assistant": {
      "command": "/Users/mriechers/Developer/ai-editorial-assistant-v3/venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/mriechers/Developer/ai-editorial-assistant-v3"
    }
  }
}
```

## Environment Variables (Optional)

The MCP server supports these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `EDITORIAL_API_URL` | `http://localhost:8000` | FastAPI backend URL |
| `EDITORIAL_OUTPUT_DIR` | `./OUTPUT` | Project output directory |
| `EDITORIAL_TRANSCRIPTS_DIR` | `./transcripts` | Transcript source directory |

You can set these in the Claude Desktop config:

```json
{
  "mcpServers": {
    "editorial-assistant": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/ai-editorial-assistant-v3",
      "env": {
        "EDITORIAL_API_URL": "http://localhost:8000"
      }
    }
  }
}
```
