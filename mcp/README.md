# Confluence Research MCP Server

Connect Claude Desktop to your Confluence Research Hub for natural research discussions.

## Requirements

- **Python 3.10 or higher** (MCP SDK requirement)
- Claude Desktop with MCP support

To check your Python version: `python --version`

If you have Python 3.9 or lower, download Python 3.10+ from https://www.python.org/downloads/

## Setup

### 1. Install Dependencies

```bash
cd mcp
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Find your Claude Desktop config file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the MCP server configuration:

```json
{
  "mcpServers": {
    "confluence-research": {
      "command": "python",
      "args": ["C:\\Users\\14102\\Documents\\Sebastian Ames\\Projects\\Confluence\\mcp\\server.py"],
      "env": {
        "CONFLUENCE_API_URL": "https://confluence-production-a32e.up.railway.app",
        "CONFLUENCE_USERNAME": "sames3",
        "CONFLUENCE_PASSWORD": "YOUR_PASSWORD_HERE"
      }
    }
  }
}
```

**Important**: Replace `YOUR_PASSWORD_HERE` with your actual password.

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### 4. Verify Connection

In Claude Desktop, you should see "confluence-research" in the MCP tools. Try asking:
> "What should I focus on this week based on my research?"

## Available Tools

| Tool | Description |
|------|-------------|
| `get_latest_synthesis` | Full v3 synthesis with all sections |
| `get_executive_summary` | Quick overview of what sources are saying |
| `get_confluence_zones` | Where your sources align |
| `get_conflicts` | Where sources disagree |
| `get_attention_priorities` | Ranked list of what to focus on |
| `get_source_stance` | What a specific source is saying |
| `get_catalyst_calendar` | Upcoming events with source perspectives |
| `get_re_review_recommendations` | Older content worth revisiting |
| `search_research` | Search content for specific topics |

## Example Conversations

**Quick status:**
> "What's the main theme in my research right now?"

**Deep dive:**
> "Tell me about the VIX positioning across my sources"

**Source-specific:**
> "What is Discord/Imran saying about the market?"

**Conflicts:**
> "Where do my sources disagree?"

**Preparation:**
> "What should I review before FOMC?"

## Troubleshooting

### Server not appearing in Claude Desktop
1. Check the config file path is correct
2. Ensure Python is in your PATH
3. Check Claude Desktop logs for errors

### Authentication errors
1. Verify username/password in config
2. Test API access: `curl -u username:password https://confluence-production-a32e.up.railway.app/health`

### Tool errors
Check the MCP server logs in Claude Desktop's developer console.
