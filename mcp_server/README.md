# Macro Confluence Hub - MCP Server

Model Context Protocol server for Claude Desktop integration. Query your collected research data using natural language.

## Quick Start

### 1. Requirements

- Python 3.10+ (required for official MCP SDK)
- SQLite database with collected research data
- Claude Desktop installed

### 2. Install Dependencies

```bash
pip install mcp>=1.0.0
```

### 3. Configure Claude Desktop

Add the following to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "confluence-hub": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "C:/Users/14102/Documents/Sebastian Ames/Projects/Confluence",
      "env": {
        "DATABASE_PATH": "C:/Users/14102/Documents/Sebastian Ames/Projects/Confluence/database/confluence.db"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

After saving the configuration, restart Claude Desktop. You should see the confluence-hub tools available.

## Available Tools

### search_content
Search collected research content by keyword.

**Example prompts:**
- "Search my research for 'gold positioning'"
- "What have my sources said about volatility?"
- "Find content about Fed policy from 42macro"

### get_synthesis
Get the latest AI-generated research synthesis.

**Example prompts:**
- "What are the key themes from today's research?"
- "Show me the latest synthesis"
- "What's the market regime according to my research?"

### get_themes
List currently tracked macro themes.

**Example prompts:**
- "What themes are being discussed across my sources?"
- "Which themes have multiple sources talking about them?"

### get_recent
Get recent content from a specific source.

**Example prompts:**
- "What has 42macro published recently?"
- "Show me the latest from Discord"
- "What videos were posted on YouTube this week?"

### get_source_view
Get a source's view on a specific topic.

**Example prompts:**
- "What does 42macro think about equities?"
- "What's Imran's view on volatility?"
- "How does KT Technical see gold right now?"

## Example Conversations

### Quick Research Check
**You**: "What are the main themes from my research this week?"

**Claude** will use `get_synthesis` and `get_themes` to provide a summary.

### Source-Specific Query
**You**: "What has Imran been saying about volatility lately?"

**Claude** will use `get_recent` and `search_content` to find relevant content.

### Trade Idea Validation
**You**: "I'm thinking about going long gold. What does my research say?"

**Claude** will use `search_content` and `get_source_view` to compile views from all sources.

## Troubleshooting

### MCP Server Not Connecting

1. Check that Python is in your PATH
2. Verify the database path exists
3. Check Claude Desktop logs: `%APPDATA%\Claude\logs\` (Windows)

### No Results Returned

1. Ensure data has been collected (run the scheduler)
2. Check the database has content: `sqlite3 database/confluence.db "SELECT COUNT(*) FROM raw_content"`

### Tool Errors

Check the MCP server logs for detailed error messages.

## Development

### Testing Tools Locally

```python
from mcp_server.tools import search_content, get_synthesis

# Test search
results = search_content("gold", days=7)
print(results)

# Test synthesis
synthesis = get_synthesis("24h")
print(synthesis)
```

### Running the Server Manually

```bash
cd /path/to/confluence
python -m mcp_server.server
```

The server communicates via stdio, so you'll need an MCP client to interact with it.
