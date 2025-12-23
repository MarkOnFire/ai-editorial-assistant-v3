# Agent Instructions

This folder contains the custom instructions needed to configure the **Editor Agent** in Claude Desktop (or other chat interfaces).

## Contents

| File | Purpose | When to Use |
|------|---------|-------------|
| `EDITOR_AGENT_INSTRUCTIONS.md` | Full system prompt for the copy-editor agent | Paste into Claude Desktop project instructions |
| `CLAUDE_DESKTOP_SETUP.md` | Step-by-step guide to connect MCP server and configure Claude Desktop | Initial setup only |

## Quick Setup

1. **Build the MCP server** (if not already done):
   ```bash
   cd mcp-server && npm install && npm run build
   ```

2. **Add MCP server to Claude Desktop** config:
   ```json
   {
     "mcpServers": {
       "editorial-assistant": {
         "command": "node",
         "args": ["/path/to/editorial-assistant/mcp-server/build/index.js"]
       }
     }
   }
   ```

3. **Create a Claude Desktop project** and paste the contents of `EDITOR_AGENT_INSTRUCTIONS.md` into the project instructions.

4. **Test the connection**:
   - Open a new conversation in the project
   - Ask: "What transcripts are ready for editing?"
   - The agent should call `list_processed_projects()` and show available projects

## Updating Instructions

When modifying the editor agent's behavior:

1. Edit `EDITOR_AGENT_INSTRUCTIONS.md` in this folder
2. Copy the updated content to your Claude Desktop project
3. Test with a sample project to verify changes

## Related Documentation

- `HOW_TO_USE.md` - End-user workflow guide
- `QUICK_REFERENCE.md` - Command and tool quick reference
- `DESIGN_v3.0.md` Part 7 - Editor Agent UX design (v3.0 vision)
