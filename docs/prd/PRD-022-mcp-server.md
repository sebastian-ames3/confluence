# PRD-022: MCP Server for Claude Integration

## Overview

Create an MCP (Model Context Protocol) server that allows Claude Desktop to access the Confluence research hub, enabling natural conversation-based research discussions.

## Problem Statement

Users want to discuss their research with an LLM but:
- Don't want to copy/paste content manually
- Want the LLM to have full context of synthesis and raw content
- Want to use their existing Claude interface (Claude Desktop)

## Solution

Build an MCP server that exposes research tools Claude can call:

```
User: "What's the consensus on VIX heading into FOMC?"

Claude: [calls get_latest_synthesis()]
Claude: [calls search_research("VIX FOMC")]
Claude: "Based on your research, there's strong confluence (85%) on
        volatility expansion ahead of FOMC. Discord is positioned via
        VIX calendar spreads, 42Macro highlights policy uncertainty,
        and KT Technical shows key support tests..."
```

## MCP Tools to Implement

### 1. `get_latest_synthesis`
Returns the latest v3 synthesis in full.

```python
@server.tool()
def get_latest_synthesis() -> dict:
    """Get the latest research synthesis from Confluence Hub.

    Returns the full v3 synthesis including:
    - Executive summary
    - Confluence zones (where sources align)
    - Conflict watch (disagreements)
    - Attention priorities
    - Re-review recommendations
    - Source stances
    - Catalyst calendar
    """
```

### 2. `search_research`
Search across raw content for specific topics.

```python
@server.tool()
def search_research(query: str, source: str = None, days: int = 7) -> list:
    """Search collected research content.

    Args:
        query: Search term (e.g., "VIX", "Bitcoin", "FOMC")
        source: Optional filter by source (discord, 42macro, youtube, etc.)
        days: How many days back to search (default 7)

    Returns list of matching content with source, date, and summary.
    """
```

### 3. `get_confluence_zones`
Get just the confluence zones from the latest synthesis.

```python
@server.tool()
def get_confluence_zones() -> list:
    """Get themes where multiple sources align.

    Returns confluence zones showing:
    - Theme name
    - Confluence strength (0-1)
    - Which sources align and their views
    - Contrary views if any
    - Related catalyst
    """
```

### 4. `get_conflicts`
Get active conflicts/disagreements between sources.

```python
@server.tool()
def get_conflicts() -> list:
    """Get active conflicts between research sources.

    Returns conflicts showing:
    - Topic
    - Bull case (view + sources)
    - Bear case (view + sources)
    - Resolution trigger
    - Weighted lean
    """
```

### 5. `get_source_stance`
Get what a specific source is currently saying.

```python
@server.tool()
def get_source_stance(source: str) -> dict:
    """Get the current stance of a specific research source.

    Args:
        source: Source name (discord, 42macro, kt_technical, youtube, substack)

    Returns the source's current narrative, key themes, and bias.
    """
```

### 6. `get_attention_priorities`
Get the ranked list of what deserves focus.

```python
@server.tool()
def get_attention_priorities() -> list:
    """Get ranked list of what deserves attention this week.

    Returns priorities with:
    - Rank (1-5)
    - Focus area
    - Why it matters
    - Time sensitivity
    - Sources discussing
    """
```

### 7. `get_catalyst_calendar`
Get upcoming events and source perspectives.

```python
@server.tool()
def get_catalyst_calendar() -> list:
    """Get upcoming market catalysts and source perspectives.

    Returns events with:
    - Date
    - Event name
    - Impact level
    - What each source says about it
    """
```

### 8. `get_re_review_recommendations`
Get older content worth revisiting.

```python
@server.tool()
def get_re_review_recommendations() -> list:
    """Get older content that's now highly relevant.

    Returns recommendations with:
    - Source and date
    - Title
    - Why it's relevant now
    - Relevance trigger type
    """
```

## Implementation

### File Structure
```
mcp/
├── server.py           # Main MCP server
├── confluence_client.py # API client for Confluence Hub
├── requirements.txt    # Dependencies
└── README.md          # Setup instructions
```

### Dependencies
```
mcp
httpx
python-dotenv
```

### Configuration
User will need to create a `.env` file or config with:
```
CONFLUENCE_API_URL=https://confluence-production-a32e.up.railway.app
CONFLUENCE_USERNAME=sames3
CONFLUENCE_PASSWORD=<password>
```

### Claude Desktop Configuration
User adds to Claude Desktop config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "confluence-research": {
      "command": "python",
      "args": ["path/to/mcp/server.py"],
      "env": {
        "CONFLUENCE_API_URL": "https://confluence-production-a32e.up.railway.app",
        "CONFLUENCE_USERNAME": "sames3",
        "CONFLUENCE_PASSWORD": "..."
      }
    }
  }
}
```

## User Experience

### Example Conversations

**Quick Status Check:**
> User: "What should I focus on today?"
> Claude: [calls get_attention_priorities()]
> "Your top priority is VIX/volatility strategies ahead of FOMC - there's strong confluence across Discord, YouTube, and 42Macro..."

**Deep Dive:**
> User: "Tell me more about the Bitcoin conflict"
> Claude: [calls get_conflicts()]
> Claude: [calls search_research("Bitcoin")]
> "There's an active debate about Bitcoin's role. Substack sees it as a risk asset tied to liquidity cycles, citing correlation with Fed policy. However, some content positions it as a monetary hedge..."

**Source-Specific:**
> User: "What is Imran saying in Discord?"
> Claude: [calls get_source_stance("discord")]
> "Imran is positioned for volatility expansion through VIX calendar spreads and butterflies. He sees the market as too complacent heading into FOMC..."

**Research Review:**
> User: "What old research should I revisit?"
> Claude: [calls get_re_review_recommendations()]
> "Four pieces worth re-reviewing: KT Technical's Elliott Wave analysis (FOMC approaching), 42Macro's weekly review (scenario playing out)..."

## Success Metrics

1. User can discuss research naturally in Claude Desktop
2. Claude accurately retrieves and synthesizes research context
3. No manual copy/paste required
4. Works reliably with Claude Desktop MCP integration
