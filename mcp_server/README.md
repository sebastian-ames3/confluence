# Macro Confluence Hub - MCP Server

Model Context Protocol server for Claude Desktop integration. Query your collected research data using natural language.

## Architecture (PRD-016)

As of v1.1.0, the MCP server uses an **API proxy pattern** to fetch data:

```
Claude Desktop → MCP Server → HTTP API → Railway Backend → Database
```

This enables Claude Desktop running locally to access production data on Railway.

## Quick Start

### 1. Requirements

- Python 3.10+ (required for official MCP SDK)
- `httpx` package for HTTP client
- Claude Desktop installed
- Railway deployment running (for production data)

### 2. Install Dependencies

```bash
pip install mcp>=1.0.0 httpx>=0.25.0
```

### 3. Configure Claude Desktop (Production)

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
      "cwd": "C:/path/to/confluence",
      "env": {
        "RAILWAY_API_URL": "https://confluence-production.up.railway.app",
        "AUTH_USERNAME": "admin",
        "AUTH_PASSWORD": "your-password-here"
      }
    }
  }
}
```

### 4. Configure Claude Desktop (Local Development)

For local development, point to localhost:

```json
{
  "mcpServers": {
    "confluence-hub": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "C:/path/to/confluence",
      "env": {
        "RAILWAY_API_URL": "http://localhost:8000",
        "AUTH_USERNAME": "admin",
        "AUTH_PASSWORD": "your-local-password"
      }
    }
  }
}
```

### 5. Restart Claude Desktop

After saving the configuration, restart Claude Desktop. You should see the confluence-hub tools available.

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `RAILWAY_API_URL` | Base URL for the API backend | Yes | `http://localhost:8000` |
| `AUTH_USERNAME` | HTTP Basic Auth username | Yes | `admin` |
| `AUTH_PASSWORD` | HTTP Basic Auth password | Yes (production) | - |
| `MCP_REQUEST_TIMEOUT` | Request timeout in seconds | No | `30.0` |

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
2. Verify environment variables are set correctly
3. Check Claude Desktop logs: `%APPDATA%\Claude\logs\` (Windows)

### Authentication Errors (401)

1. Verify `AUTH_USERNAME` and `AUTH_PASSWORD` match Railway config
2. Check that the API is running and accessible
3. Try accessing the API directly: `curl -u admin:password https://your-api.up.railway.app/health`

### Connection Errors

1. Check that `RAILWAY_API_URL` is correct
2. Verify Railway deployment is running
3. Check network connectivity
4. For local development, ensure the FastAPI server is running on port 8000

### No Results Returned

1. Ensure data has been collected (check Railway logs)
2. Verify the API has content: access `/api/dashboard/stats` endpoint
3. Check that authentication is working

### Tool Errors

Check the MCP server logs for detailed error messages. Common issues:
- Network timeouts (increase `MCP_REQUEST_TIMEOUT`)
- Invalid API responses
- Missing authentication credentials

## Development

### Testing Tools Locally

First, start the backend server:
```bash
cd /path/to/confluence
python -m backend.app
```

Then test the MCP tools:
```python
import os
os.environ["RAILWAY_API_URL"] = "http://localhost:8000"
os.environ["AUTH_USERNAME"] = "admin"
os.environ["AUTH_PASSWORD"] = "your-password"

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
export RAILWAY_API_URL="http://localhost:8000"
export AUTH_USERNAME="admin"
export AUTH_PASSWORD="your-password"
python -m mcp_server.server
```

The server communicates via stdio, so you'll need an MCP client to interact with it.

## API Endpoints Used

The MCP tools call the following API endpoints:

| MCP Tool | API Endpoint | Method |
|----------|--------------|--------|
| `search_content` | `/api/search/content` | GET |
| `get_synthesis` | `/api/synthesis/latest` | GET |
| `get_themes` | `/api/search/themes/aggregated` | GET |
| `get_recent` | `/api/search/recent/{source}` | GET |
| `get_source_view` | `/api/search/sources/{source}/view` | GET |

## Version History

- **v1.1.0** (PRD-016): Refactored to use API proxy pattern
- **v1.0.0** (PRD-013): Initial MCP server implementation with direct database access
