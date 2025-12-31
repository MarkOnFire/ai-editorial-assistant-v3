#!/usr/bin/env python3
"""
Editorial Assistant MCP Server

Provides tools for the copy editor agent in Claude Desktop to:
- Discover processed projects ready for editing
- Load project context (transcript, brainstorming, revisions)
- Save revisions and keyword reports with auto-versioning

Connects to the FastAPI backend on localhost:8000 for job metadata,
and reads/writes directly to the OUTPUT folder for content.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
API_BASE_URL = os.getenv("EDITORIAL_API_URL", "http://localhost:8000")
OUTPUT_DIR = Path(os.getenv("EDITORIAL_OUTPUT_DIR",
    Path(__file__).parent.parent / "OUTPUT"))
TRANSCRIPTS_DIR = Path(os.getenv("EDITORIAL_TRANSCRIPTS_DIR",
    Path(__file__).parent.parent / "transcripts"))

# Initialize MCP server
server = Server("editorial-assistant")


# =============================================================================
# Helper Functions
# =============================================================================

def get_project_path(project_name: str) -> Path:
    """Get the OUTPUT path for a project."""
    return OUTPUT_DIR / project_name


def load_manifest(project_name: str) -> dict | None:
    """Load the manifest.json for a project."""
    manifest_path = get_project_path(project_name) / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def save_manifest(project_name: str, manifest: dict) -> None:
    """Save the manifest.json for a project."""
    manifest_path = get_project_path(project_name) / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)


def get_next_version(project_path: Path, prefix: str) -> int:
    """Find the next version number for a file type."""
    pattern = re.compile(rf"{prefix}_v(\d+)\.md")
    max_version = 0
    for file in project_path.glob(f"{prefix}_v*.md"):
        match = pattern.match(file.name)
        if match:
            max_version = max(max_version, int(match.group(1)))
    return max_version + 1


def determine_project_status(manifest: dict, project_path: Path) -> str:
    """Determine the editing status of a project."""
    phases = manifest.get("phases", [])

    # Check if still processing
    for phase in phases:
        if phase.get("status") == "in_progress":
            return "processing"

    # Check if any phases failed
    for phase in phases:
        if phase.get("status") == "failed":
            return "failed"

    # Check if we have revisions
    if list(project_path.glob("copy_revision_v*.md")):
        return "revision_in_progress"

    # Check if core phases are complete
    core_phases = ["analyst", "formatter", "seo"]
    completed = [p["name"] for p in phases if p.get("status") == "completed"]
    if all(p in completed for p in core_phases):
        return "ready_for_editing"

    return "incomplete"


def get_available_deliverables(project_path: Path, manifest: dict) -> list[str]:
    """List available deliverables for a project."""
    deliverables = []
    outputs = manifest.get("outputs", {})

    if (project_path / outputs.get("analysis", "")).exists():
        deliverables.append("brainstorming")
    if (project_path / outputs.get("formatted_transcript", "")).exists():
        deliverables.append("formatted_transcript")
    if (project_path / outputs.get("seo_metadata", "")).exists():
        deliverables.append("seo_metadata")

    # Check for revisions
    revisions = list(project_path.glob("copy_revision_v*.md"))
    if revisions:
        deliverables.append(f"revisions ({len(revisions)})")

    # Check for keyword reports
    keyword_reports = list(project_path.glob("keyword_report_v*.md"))
    if keyword_reports:
        deliverables.append(f"keyword_reports ({len(keyword_reports)})")

    return deliverables


async def fetch_job_from_api(project_name: str) -> dict | None:
    """Fetch job details from the FastAPI backend."""
    try:
        async with httpx.AsyncClient() as client:
            # Try to find job by project name
            response = await client.get(
                f"{API_BASE_URL}/api/queue",
                params={"limit": 100}
            )
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                for job in jobs:
                    if job.get("project_name") == project_name:
                        return job
    except Exception:
        pass
    return None


# =============================================================================
# MCP Tool Definitions
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the copy editor."""
    return [
        Tool(
            name="list_processed_projects",
            description="Discover what transcripts have been processed and are ready for editing. Returns project ID, status, and available deliverables.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["all", "ready_for_editing", "revision_in_progress", "processing"],
                        "description": "Filter by project status. Default: all"
                    }
                }
            }
        ),
        Tool(
            name="load_project_for_editing",
            description="Load full context for an editing session: transcript, brainstorming (titles, descriptions, keywords), existing revisions, and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The project ID (e.g., '2WLI1209HD')"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="get_formatted_transcript",
            description="Load the AP Style formatted transcript for fact-checking. Use this to verify quotes, speaker names, and facts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The project ID"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="save_revision",
            description="Save a copy revision document with auto-versioning. Returns the file path and version number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The project ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "The revision document content (Markdown)"
                    }
                },
                "required": ["project_name", "content"]
            }
        ),
        Tool(
            name="save_keyword_report",
            description="Save a keyword/SEO analysis report with auto-versioning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The project ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "The keyword report content (Markdown)"
                    }
                },
                "required": ["project_name", "content"]
            }
        ),
        Tool(
            name="get_project_summary",
            description="Quick status check for a specific project without loading full context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The project ID"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="read_project_file",
            description="Read a specific file from a project folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The project ID"
                    },
                    "filename": {
                        "type": "string",
                        "description": "The filename to read (e.g., 'analyst_output.md')"
                    }
                },
                "required": ["project_name", "filename"]
            }
        ),
    ]


# =============================================================================
# MCP Tool Implementations
# =============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls from the copy editor agent."""

    if name == "list_processed_projects":
        return await handle_list_processed_projects(arguments)
    elif name == "load_project_for_editing":
        return await handle_load_project_for_editing(arguments)
    elif name == "get_formatted_transcript":
        return await handle_get_formatted_transcript(arguments)
    elif name == "save_revision":
        return await handle_save_revision(arguments)
    elif name == "save_keyword_report":
        return await handle_save_keyword_report(arguments)
    elif name == "get_project_summary":
        return await handle_get_project_summary(arguments)
    elif name == "read_project_file":
        return await handle_read_project_file(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_list_processed_projects(arguments: dict) -> list[TextContent]:
    """List all processed projects with their status."""
    status_filter = arguments.get("status_filter", "all")

    projects = []

    if not OUTPUT_DIR.exists():
        return [TextContent(type="text", text="No OUTPUT directory found.")]

    for project_path in sorted(OUTPUT_DIR.iterdir()):
        if not project_path.is_dir():
            continue

        manifest = load_manifest(project_path.name)
        if not manifest:
            continue

        status = determine_project_status(manifest, project_path)

        # Apply filter
        if status_filter != "all" and status != status_filter:
            continue

        deliverables = get_available_deliverables(project_path, manifest)

        # Extract metadata from manifest
        completed_at = manifest.get("completed_at", "")
        if completed_at:
            try:
                dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                completed_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        projects.append({
            "project_name": project_path.name,
            "status": status,
            "completed_at": completed_at,
            "deliverables": deliverables,
            "job_id": manifest.get("job_id")
        })

    if not projects:
        return [TextContent(type="text", text="No processed projects found.")]

    # Format output
    lines = [f"Found {len(projects)} processed project(s):\n"]
    for p in projects:
        status_emoji = {
            "ready_for_editing": "✅",
            "revision_in_progress": "📝",
            "processing": "⏳",
            "failed": "❌",
            "incomplete": "⚠️"
        }.get(p["status"], "❓")

        lines.append(f"{status_emoji} **{p['project_name']}**")
        lines.append(f"   Status: {p['status']}")
        if p["completed_at"]:
            lines.append(f"   Completed: {p['completed_at']}")
        lines.append(f"   Has: {', '.join(p['deliverables'])}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_load_project_for_editing(arguments: dict) -> list[TextContent]:
    """Load full project context for editing."""
    project_name = arguments.get("project_name")
    if not project_name:
        return [TextContent(type="text", text="Error: project_name is required")]

    project_path = get_project_path(project_name)
    if not project_path.exists():
        return [TextContent(type="text", text=f"Error: Project '{project_name}' not found")]

    manifest = load_manifest(project_name)
    if not manifest:
        return [TextContent(type="text", text=f"Error: No manifest found for '{project_name}'")]

    outputs = manifest.get("outputs", {})
    result_parts = []

    # Header
    result_parts.append(f"# Project: {project_name}\n")
    result_parts.append(f"**Status**: {determine_project_status(manifest, project_path)}")
    result_parts.append(f"**Job ID**: {manifest.get('job_id', 'N/A')}")
    if manifest.get("completed_at"):
        result_parts.append(f"**Completed**: {manifest['completed_at']}")
    result_parts.append("")

    # Load brainstorming (analyst output)
    analyst_file = project_path / outputs.get("analysis", "analyst_output.md")
    if analyst_file.exists():
        result_parts.append("---\n## Brainstorming (AI-Generated)\n")
        result_parts.append(analyst_file.read_text())
        result_parts.append("")

    # Load latest revision if exists
    revisions = sorted(project_path.glob("copy_revision_v*.md"), reverse=True)
    if revisions:
        latest = revisions[0]
        version = re.search(r"v(\d+)", latest.name)
        version_num = version.group(1) if version else "?"
        result_parts.append(f"---\n## Latest Revision (v{version_num})\n")
        result_parts.append(latest.read_text())
        result_parts.append("")

    # Note about transcript
    result_parts.append("---\n## Transcript Access\n")
    result_parts.append("Use `get_formatted_transcript()` to load the AP Style formatted transcript for fact-checking.")

    return [TextContent(type="text", text="\n".join(result_parts))]


async def handle_get_formatted_transcript(arguments: dict) -> list[TextContent]:
    """Load the formatted transcript for fact-checking."""
    project_name = arguments.get("project_name")
    if not project_name:
        return [TextContent(type="text", text="Error: project_name is required")]

    project_path = get_project_path(project_name)
    manifest = load_manifest(project_name)

    if not manifest:
        return [TextContent(type="text", text=f"Error: Project '{project_name}' not found")]

    outputs = manifest.get("outputs", {})

    # Try formatted transcript first
    formatter_file = project_path / outputs.get("formatted_transcript", "formatter_output.md")
    if formatter_file.exists():
        content = formatter_file.read_text()
        return [TextContent(type="text", text=f"# Formatted Transcript: {project_name}\n\n{content}")]

    # Fall back to raw transcript
    transcript_name = manifest.get("transcript_file", "")
    if transcript_name:
        for search_dir in [TRANSCRIPTS_DIR, TRANSCRIPTS_DIR / "archive"]:
            transcript_path = search_dir / transcript_name
            if transcript_path.exists():
                content = transcript_path.read_text()
                return [TextContent(
                    type="text",
                    text=f"# Raw Transcript: {project_name}\n\n**Note**: Formatted transcript not available. Using raw transcript.\n\n{content}"
                )]

    return [TextContent(type="text", text=f"Error: No transcript found for '{project_name}'")]


async def handle_save_revision(arguments: dict) -> list[TextContent]:
    """Save a copy revision with auto-versioning."""
    project_name = arguments.get("project_name")
    content = arguments.get("content")

    if not project_name or not content:
        return [TextContent(type="text", text="Error: project_name and content are required")]

    project_path = get_project_path(project_name)
    if not project_path.exists():
        return [TextContent(type="text", text=f"Error: Project '{project_name}' not found")]

    # Get next version number
    version = get_next_version(project_path, "copy_revision")
    filename = f"copy_revision_v{version}.md"
    filepath = project_path / filename

    # Save the file
    filepath.write_text(content)

    # Update manifest
    manifest = load_manifest(project_name)
    if manifest:
        if "revisions" not in manifest:
            manifest["revisions"] = []
        manifest["revisions"].append({
            "version": version,
            "filename": filename,
            "saved_at": datetime.now().isoformat()
        })
        save_manifest(project_name, manifest)

    return [TextContent(
        type="text",
        text=f"✅ Saved revision as `{filename}` in OUTPUT/{project_name}/\n\nVersion: v{version}\nPath: {filepath}"
    )]


async def handle_save_keyword_report(arguments: dict) -> list[TextContent]:
    """Save a keyword report with auto-versioning."""
    project_name = arguments.get("project_name")
    content = arguments.get("content")

    if not project_name or not content:
        return [TextContent(type="text", text="Error: project_name and content are required")]

    project_path = get_project_path(project_name)
    if not project_path.exists():
        return [TextContent(type="text", text=f"Error: Project '{project_name}' not found")]

    # Get next version number
    version = get_next_version(project_path, "keyword_report")
    filename = f"keyword_report_v{version}.md"
    filepath = project_path / filename

    # Save the file
    filepath.write_text(content)

    # Update manifest
    manifest = load_manifest(project_name)
    if manifest:
        if "keyword_reports" not in manifest:
            manifest["keyword_reports"] = []
        manifest["keyword_reports"].append({
            "version": version,
            "filename": filename,
            "saved_at": datetime.now().isoformat()
        })
        save_manifest(project_name, manifest)

    return [TextContent(
        type="text",
        text=f"✅ Saved keyword report as `{filename}` in OUTPUT/{project_name}/\n\nVersion: v{version}\nPath: {filepath}"
    )]


async def handle_get_project_summary(arguments: dict) -> list[TextContent]:
    """Get a quick summary of a project's status."""
    project_name = arguments.get("project_name")
    if not project_name:
        return [TextContent(type="text", text="Error: project_name is required")]

    project_path = get_project_path(project_name)
    if not project_path.exists():
        return [TextContent(type="text", text=f"Error: Project '{project_name}' not found")]

    manifest = load_manifest(project_name)
    if not manifest:
        return [TextContent(type="text", text=f"Error: No manifest found for '{project_name}'")]

    status = determine_project_status(manifest, project_path)
    deliverables = get_available_deliverables(project_path, manifest)

    # Count revisions
    revisions = list(project_path.glob("copy_revision_v*.md"))
    keyword_reports = list(project_path.glob("keyword_report_v*.md"))

    lines = [
        f"# Project Summary: {project_name}\n",
        f"**Status**: {status}",
        f"**Job ID**: {manifest.get('job_id', 'N/A')}",
        f"**Completed**: {manifest.get('completed_at', 'N/A')}",
        "",
        "## Available Deliverables",
        *[f"- {d}" for d in deliverables],
        "",
        "## Revision History",
        f"- Copy Revisions: {len(revisions)}",
        f"- Keyword Reports: {len(keyword_reports)}",
    ]

    if revisions:
        latest = sorted(revisions, reverse=True)[0]
        lines.append(f"- Latest Revision: {latest.name}")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_read_project_file(arguments: dict) -> list[TextContent]:
    """Read a specific file from a project folder."""
    project_name = arguments.get("project_name")
    filename = arguments.get("filename")

    if not project_name or not filename:
        return [TextContent(type="text", text="Error: project_name and filename are required")]

    project_path = get_project_path(project_name)
    filepath = project_path / filename

    # Security check: ensure file is within project folder
    try:
        filepath.resolve().relative_to(project_path.resolve())
    except ValueError:
        return [TextContent(type="text", text="Error: Invalid file path")]

    if not filepath.exists():
        return [TextContent(type="text", text=f"Error: File '{filename}' not found in {project_name}")]

    content = filepath.read_text()
    return [TextContent(type="text", text=f"# {filename}\n\n{content}")]


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
