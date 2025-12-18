# PRD-039: Symbol-Level Confluence Tracking

## Overview

Enhance the Macro Confluence Hub to track **symbol-specific price levels and positioning** from KT Technical Analysis (Elliott Wave) and Discord Options Insight, enabling automated detection of high-conviction trade setups where both sources align.

## Problem Statement

Currently, the system tracks macro themes and content-level confluence but lacks:
1. Symbol-specific price level storage (support, resistance, targets, invalidation)
2. Elliott Wave state tracking per symbol
3. Options positioning data (IV regime, strategy quadrant)
4. Cross-source confluence detection at the symbol level

When KT says "GOOGL support at 313, target 330" and Discord shows "GOOGL in buy-call quadrant with cheap IV," this is a high-conviction setup that should be surfaced automatically.

## Tracked Symbols

Limited scope (11 symbols from `stock-analysis-list.txt`):
- **Indices**: SPX, QQQ, IWM
- **Crypto**: BTC
- **Semis**: SMH, NVDA
- **Mega-cap**: TSLA, GOOGL, AAPL, MSFT, AMZN

## Data Sources

### KT Technical Analysis (Elliott Wave)

**From Video Transcripts:**
- Wave counts and positions ("wave 4 completing", "wave 5 target")
- Price levels with context ("support at 313", "0.382 fib at 236")
- Invalidation levels ("below 270 negates the count")
- Directional bias (bullish/bearish based on wave structure)

**From Chart Images:**
- Annotated fib levels (e.g., "0.236 (319.05)")
- Wave labels ((i), (ii), (iii), (iv), (v))
- Target projections and demand zones
- Text notes explaining the setup

### Discord Options Insight

**From Text Posts:**
- Gamma levels ("peak gamma at 350-355")
- Volume shelves ("big volume shelf around 72-73")
- IV assessment ("vol is still quite cheap")
- Strategy recommendations ("calendar call spreads work here")

**From Stock Compass Images:**
- 4-quadrant positioning: BUY CALL, BUY PUT, SELL CALL, SELL PUT
- Y-axis: Implied Volatility (high at top, low at bottom)
- X-axis: Spot direction bias
- Ticker positions color-coded by sector
- Center = neutral/spread strategies

## Technical Implementation

### 1. Database Models

```python
class SymbolLevel(Base):
    """Price levels per symbol from various sources"""
    __tablename__ = "symbol_levels"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, index=True)
    source = Column(String(20), nullable=False)  # kt_technical, discord

    # Level details
    level_type = Column(String(20), nullable=False)
    # Types: support, resistance, target, invalidation, gamma, volume_shelf, fib_level
    price = Column(Float, nullable=False)
    price_upper = Column(Float)  # For ranges like "313-319"
    significance = Column(String(10))  # critical, important, minor

    # Direction vector - disambiguates how to trade the level
    # "support at 313" (bullish_reversal) vs "breakdown below 313" (bearish_breakdown)
    direction = Column(String(20))
    # Values: bullish_reversal, bearish_reversal, bullish_breakout, bearish_breakdown, neutral

    # Context from source
    wave_context = Column(String(100))  # "wave iv support", "wave 5 target"
    options_context = Column(String(100))  # "peak gamma", "put wall", "volume shelf"
    fib_level = Column(String(10))  # "0.236", "0.382", "0.5", "0.618", "1.236"

    # Context snippet for verification (5-10 words surrounding the extraction)
    context_snippet = Column(String(200))  # e.g., "support likely holding at 313 if bulls defend"

    # Extraction metadata
    confidence = Column(Float, default=0.8)  # 0.0-1.0, flag for review if < 0.7
    extracted_from_content_id = Column(Integer, ForeignKey("raw_content.id"))
    extraction_method = Column(String(20))  # transcript, chart_image, text_post, compass_image

    # Validity tracking
    is_active = Column(Boolean, default=True)
    invalidation_price = Column(Float)  # Price at which this level becomes invalid (extracted from KT)
    invalidated_at = Column(DateTime)  # When manually marked invalid
    invalidation_reason = Column(String(100))

    # Staleness (14-day default)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_confirmed_at = Column(DateTime)
    is_stale = Column(Boolean, default=False)
    stale_reason = Column(String(100))

    __table_args__ = (
        Index('idx_symbol_source', 'symbol', 'source'),
        Index('idx_symbol_active', 'symbol', 'is_active'),
        CheckConstraint("direction IN ('bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral')", name='check_direction_values'),
    )


class SymbolState(Base):
    """Current consolidated state per symbol"""
    __tablename__ = "symbol_states"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)

    # KT Technical state
    kt_wave_degree = Column(String(20))  # minor, intermediate, primary
    kt_wave_position = Column(String(20))  # wave_1, wave_2, wave_3, wave_4, wave_5
    kt_wave_direction = Column(String(10))  # up, down (impulse direction)
    kt_wave_phase = Column(String(15))  # impulse (trending) or correction (choppy)
    kt_bias = Column(String(10))  # bullish, bearish, neutral
    kt_primary_target = Column(Float)
    kt_primary_support = Column(Float)
    kt_invalidation = Column(Float)
    kt_notes = Column(Text)  # AI-extracted key points
    kt_last_updated = Column(DateTime)
    kt_is_stale = Column(Boolean, default=False)
    kt_stale_warning = Column(String(100))
    kt_source_content_id = Column(Integer, ForeignKey("raw_content.id"))

    # Discord Options state
    discord_quadrant = Column(String(20))  # buy_call, buy_put, sell_call, sell_put, neutral
    discord_iv_regime = Column(String(15))  # cheap, neutral, expensive
    discord_strategy_rec = Column(String(100))  # "call spreads", "put calendars", etc.
    discord_key_strikes = Column(Text)  # JSON array of important strikes
    discord_notes = Column(Text)
    discord_last_updated = Column(DateTime)
    discord_is_stale = Column(Boolean, default=False)
    discord_source_content_id = Column(Integer, ForeignKey("raw_content.id"))

    # Confluence scoring
    # NOTE: Confluence requires DIRECTION alignment, not just price proximity
    # "Support at 313" (bullish) + "Buy Call quadrant" (bullish) = HIGH confluence
    # "Support at 313" (bullish) + "Sell Call quadrant" (bearish) = CONFLICT, not confluence
    sources_directionally_aligned = Column(Boolean)  # Both bullish or both bearish
    confluence_score = Column(Float)  # 0.0 to 1.0
    confluence_summary = Column(Text)  # AI-generated alignment analysis
    trade_setup_suggestion = Column(Text)  # AI-generated trade idea when aligned

    updated_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Level Extraction Agent

New agent: `agents/symbol_level_extractor.py`

```python
class SymbolLevelExtractor(BaseAgent):
    """
    Extracts symbol-specific price levels from content.

    Handles:
    - KT Technical transcripts (text parsing)
    - KT Technical chart images (vision parsing)
    - Discord text posts (text parsing)
    - Discord Stock Compass images (vision parsing)
    """

    TRACKED_SYMBOLS = ['SPX', 'QQQ', 'IWM', 'BTC', 'SMH', 'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'MSFT', 'AMZN']

    # Comprehensive symbol aliasing - normalize all variations to canonical tickers
    SYMBOL_ALIASES = {
        # GOOGL variations
        'GOOGLE': 'GOOGL', 'GOOG': 'GOOGL', 'ALPHABET': 'GOOGL',
        # AAPL variations
        'APPLE': 'AAPL',
        # AMZN variations
        'AMAZON': 'AMZN',
        # MSFT variations
        'MICROSOFT': 'MSFT',
        # TSLA variations
        'TESLA': 'TSLA',
        # NVDA variations
        'NVIDIA': 'NVDA',
        # IWM variations
        'RUSSELL': 'IWM', 'RUSSELL 2000': 'IWM', 'RTY': 'IWM', 'RUT': 'IWM',
        # QQQ variations
        'NASDAQ': 'QQQ', 'NASDAQ 100': 'QQQ', 'NQ': 'QQQ', 'NDX': 'QQQ', 'QS': 'QQQ',
        # SPX variations
        'S&P': 'SPX', 'S&P 500': 'SPX', 'SP500': 'SPX', 'ES': 'SPX', 'SPY': 'SPX',
        # BTC variations
        'BITCOIN': 'BTC', 'BTCUSD': 'BTC',
        # SMH variations
        'SEMIS': 'SMH', 'SEMICONDUCTORS': 'SMH',
    }

    # Transcript chunking: Long videos (30+ min) must be split to avoid "lost in middle" errors
    CHUNK_SIZE_MINUTES = 5  # Split transcripts every 5 minutes or by speaker change

    def extract_from_transcript(self, transcript: str, source: str) -> List[Dict]:
        """Extract levels from KT Technical or Discord text."""

    def extract_from_chart_image(self, image_path: str) -> List[Dict]:
        """Extract levels from KT Technical annotated charts using Claude vision."""

    def extract_from_compass_image(self, image_path: str) -> List[Dict]:
        """Extract quadrant positions from Discord Stock Compass using Claude vision."""

    def update_symbol_state(self, symbol: str, levels: List[Dict], source: str):
        """Update SymbolState with latest extracted data."""
```

#### Transcript Extraction Prompt

```
You are extracting price levels for specific symbols from investment research content.

TRACKED SYMBOLS: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN
(Also match aliases: "Google"=GOOGL, "Nasdaq"=QQQ, "S&P"=SPX, "Russell"=IWM, etc.)

For each tracked symbol mentioned, extract:
1. Support levels (with fib level if mentioned, e.g., "0.382")
2. Resistance levels
3. Target prices (with wave context if Elliott Wave, e.g., "wave 5 target")
4. Invalidation levels (the specific price where the thesis breaks)
5. Wave position (if Elliott Wave: wave_1 through wave_5, direction up/down)
6. Wave phase: Is this an IMPULSE (trending, 5-wave move) or CORRECTION (choppy, 3-wave move)?
7. Overall bias (bullish/bearish/neutral)

For each level, you MUST also extract:
- direction: How should this level be traded?
  - bullish_reversal: Buy at support, expecting bounce up
  - bearish_reversal: Sell at resistance, expecting rejection down
  - bullish_breakout: Buy above this level on breakout
  - bearish_breakdown: Sell below this level on breakdown
  - neutral: Level is informational only
- context_snippet: The exact 5-10 words surrounding this level in the transcript
- invalidation_price: At what price does THIS LEVEL become invalid? (e.g., "support at 313 invalid if we lose 308")

Return JSON:
{
  "symbols": [
    {
      "symbol": "GOOGL",
      "bias": "bullish",
      "wave_position": "wave_4",
      "wave_direction": "up",
      "wave_phase": "impulse",
      "levels": [
        {
          "type": "support",
          "price": 313.04,
          "fib": "0.382",
          "direction": "bullish_reversal",
          "context": "wave iv retracement",
          "context_snippet": "support likely holding at 313 if bulls defend",
          "invalidation_price": 308.27
        },
        {
          "type": "target",
          "price": 330,
          "direction": "neutral",
          "context": "wave 5 completion",
          "context_snippet": "looking for wave 5 to complete around 328 to 330",
          "invalidation_price": null
        },
        {
          "type": "invalidation",
          "price": 270,
          "direction": "bearish_breakdown",
          "context": "weekly demand break invalidates bullish count",
          "context_snippet": "if we lose 270 the whole count is invalid",
          "invalidation_price": null
        }
      ],
      "notes": "Monster breakout from 270 low, looking for wave 5 to 328-330 if 310 support holds"
    }
  ],
  "extraction_confidence": 0.9
}

IMPORTANT:
- Only extract levels you are confident about (>70% confidence)
- If a number is ambiguous or you're unsure which symbol it refers to, skip it
- Context snippets must be EXACT quotes from the transcript, not paraphrased
```

#### Chart Image Vision Prompt

```
Analyze this trading chart image and extract all annotated price levels.

Look for:
1. Fibonacci retracement/extension levels (labeled like "0.382 (313.04)")
2. Wave labels ((i), (ii), (iii), (iv), (v) or 1, 2, 3, 4, 5)
3. Support/resistance zones (horizontal lines or boxes)
4. Target projections (arrows pointing to price levels)
5. Invalidation levels (often marked in red or labeled "hard invalidation")
6. Text annotations explaining the setup
7. "BOS" (Break of Structure) markers
8. Demand/supply zones (often shown as shaded rectangles)

Identify the symbol from the chart title/ticker shown (bottom-left corner typically).

Determine the wave phase:
- IMPULSE: 5-wave trending structure (waves labeled 1-2-3-4-5 or i-ii-iii-iv-v)
- CORRECTION: 3-wave counter-trend structure (waves labeled A-B-C)

For each level, determine the direction vector:
- Support zones with bullish projection arrows = bullish_reversal
- Resistance zones with bearish projection arrows = bearish_reversal
- Levels with "if breaks above" annotations = bullish_breakout
- Levels with "if loses" or "hard invalidation" = bearish_breakdown

Return JSON with same schema as transcript extraction, including:
- wave_phase (impulse/correction)
- direction for each level
- context_snippet (use the text annotation near the level if visible)
```

#### Stock Compass Vision Prompt

```
Analyze this Options Insight Stock Compass image.

The compass has 4 quadrants:
- Top-left: SELL PUT (bullish, high IV)
- Top-right: SELL CALL (bearish, high IV)
- Bottom-left: BUY CALL (bullish, low IV)
- Bottom-right: BUY PUT (bearish, low IV)
- Center: neutral/spread strategies

Y-axis: Implied Volatility (high at top, low at bottom)
X-axis: Directional bias (bullish left, bearish right)

Tickers are color-coded by sector:
- Green: Technology
- Blue: Communications
- Yellow: Consumer Cyclical
- Light Green: Consumer Non-Cyclical
- Gray: Industrial
- Red: Financial

For each ticker you can identify, return:
{
  "compass_data": [
    {
      "symbol": "GOOGL",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left area, suggesting bullish with low IV"
    }
  ],
  "extraction_confidence": 0.85
}

Only include symbols from: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN
```

### 3. Integration Points

#### Enhance Existing Collectors

**Discord Collector** (`collectors/discord_collector.py`):
- Detect Stock Compass images (filename pattern or image classification)
- Route compass images to vision extraction
- Extract levels from Imran's text posts

**KT Technical Collector** (via existing transcript pipeline):
- After transcript analysis, run level extraction
- Capture chart thumbnails/images for vision extraction

#### Analysis Pipeline Addition

In `backend/routes/trigger.py`, add symbol level extraction after content analysis:

```python
@router.post("/analyze/extract-levels")
async def extract_symbol_levels(background_tasks: BackgroundTasks):
    """Extract symbol levels from recent unprocessed content."""
    # 1. Get recent KT Technical and Discord content
    # 2. Run level extraction agent
    # 3. Update SymbolLevel and SymbolState tables
    # 4. Calculate confluence scores
    # 5. Generate trade setup suggestions where aligned
```

### 4. API Endpoints

```python
# backend/routes/symbols.py

@router.get("/api/symbols")
async def get_all_symbols():
    """Get all tracked symbols with current state summary."""

@router.get("/api/symbols/{symbol}")
async def get_symbol_detail(symbol: str):
    """Get full detail for one symbol: state, levels, confluence."""

@router.get("/api/symbols/{symbol}/levels")
async def get_symbol_levels(symbol: str, source: Optional[str] = None):
    """Get all active price levels for a symbol."""

@router.get("/api/symbols/confluence")
async def get_confluence_opportunities():
    """Get symbols where KT and Discord are directionally aligned."""

@router.post("/api/symbols/refresh")
async def refresh_symbol_data():
    """Manually trigger level extraction."""

@router.patch("/api/symbols/levels/{level_id}")
async def update_level(level_id: int, updates: LevelUpdate):
    """
    User override for AI extraction errors.
    Allows editing: price, level_type, direction, is_active (dismiss).
    Tracks who made the edit and when.
    """

@router.delete("/api/symbols/levels/{level_id}")
async def dismiss_level(level_id: int):
    """Mark a level as inactive (AI made an error)."""
```

### 6. MCP Tools

```python
# mcp/server.py additions

@tool
def get_symbol_analysis(symbol: str) -> Dict:
    """
    Get complete analysis for a tracked symbol.

    Returns KT Technical view (wave count, levels, bias),
    Discord view (quadrant, IV regime, strategy),
    and confluence assessment.
    """

@tool
def get_symbol_levels(symbol: str, source: Optional[str] = None) -> List[Dict]:
    """
    Get all active price levels for a symbol.

    Optionally filter by source (kt_technical or discord).
    Returns levels sorted by price with context.
    """

@tool
def get_confluence_opportunities() -> List[Dict]:
    """
    Get symbols where KT Technical and Discord are aligned.

    Returns symbols with high confluence scores,
    including suggested trade setups.
    """

@tool
def get_trade_setup(symbol: str) -> Dict:
    """
    Generate a trade setup for a symbol based on current state.

    Combines KT Technical levels with Discord positioning
    to suggest entry, stop, target, and structure.
    """
```

### 7. Dashboard UI

#### New "Symbols" Tab

**List View:**
```
┌─────────────────────────────────────────────────────────────────┐
│  TRACKED SYMBOLS                                   Updated: 2h  │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────┬─────────┬───────────┬────────────┬────────────────┐│
│  │ Symbol │ KT View │ Discord   │ Confluence │ Last Updated   ││
│  ├────────┼─────────┼───────────┼────────────┼────────────────┤│
│  │ GOOGL  │ 🟢 W5↑  │ 🟢 BuyC   │ ✅ 0.92    │ KT: Dec 7      ││
│  │ SPX    │ 🟢 W3↑  │ 🟡 Neut   │ 🔶 0.65    │ KT: Dec 7      ││
│  │ IWM    │ 🟡 W4↓  │ 🟢 BuyC   │ 🔶 0.58    │ KT: Dec 7      ││
│  │ NVDA   │ 🔴 Corr │ 🔴 BuyP   │ ✅ 0.88    │ ⚠️ Stale (18d) ││
│  │ BTC    │ 🟢 W5↑  │ 🟢 BuyC   │ ✅ 0.95    │ KT: Dec 10     ││
│  │ ...    │         │           │            │                ││
│  └────────┴─────────┴───────────┴────────────┴────────────────┘│
│                                                                 │
│  Legend: 🟢 Bullish  🟡 Neutral  🔴 Bearish                     │
│          ✅ High confluence (>0.8)  🔶 Medium  ⚪ Low           │
│          ⚠️ Stale = No update in 14+ days                       │
└─────────────────────────────────────────────────────────────────┘
```

**Detail View (click symbol):**
```
┌─────────────────────────────────────────────────────────────────┐
│  GOOGL - Alphabet Inc                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ KT TECHNICAL            │  │ DISCORD OPTIONS             │  │
│  │ Updated: Dec 7          │  │ Updated: Dec 12             │  │
│  ├─────────────────────────┤  ├─────────────────────────────┤  │
│  │ Wave: iv → v (bullish)  │  │ Quadrant: Buy Call          │  │
│  │ Phase: IMPULSE          │  │ IV: Cheap                   │  │
│  │ Degree: Intermediate    │  │ Strategy: Call spreads      │  │
│  │ Target: 328-330         │  │                             │  │
│  │ Support: 319 (0.236)    │  │                             │  │
│  │ Support: 313 (0.382)    │  │                             │  │
│  │ Invalidation: 270       │  │                             │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                 │
│  PRICE LEVELS                                                   │
│  ─────────────                                                  │
│  🎯 330.00  Target    "wave 5 to complete around 328 to 330"   │
│  🎯 328.00  Target    KT wave 5 zone                           │
│  🛡️ 319.05  Support   "support likely holding at 319" (0.236) │
│  🛡️ 313.04  Support   "deeper support at the 382 fib" (0.382) │
│  🛡️ 308.27  Support   KT 0.5 fib                               │
│  🚫 270.00  Invalid   "if we lose 270 the count is invalid"    │
│                                                                 │
│  [Hover any level to see full context snippet]                 │
│  [Click ✏️ on any level to edit/dismiss if AI made an error]   │
│                                                                 │
│  CONFLUENCE ANALYSIS                                            │
│  ───────────────────                                            │
│  Score: 0.92 (HIGH)                                            │
│                                                                 │
│  Both sources bullish on GOOGL:                                │
│  • KT: Wave 5 targeting 328-330, supported at 313-319          │
│  • Discord: Buy-call quadrant with cheap IV                    │
│                                                                 │
│  SUGGESTED SETUP                                                │
│  • Structure: Long calls or call spreads                       │
│  • Entry zone: 313-319 (0.236-0.382 fib zone)                  │
│  • Stop: Below 308 (0.5 fib)                                   │
│  • Target: 328-330 (wave 5)                                    │
│                                                                 │
│  [View KT Source] [View Discord Source] [Copy to Clipboard]    │
└─────────────────────────────────────────────────────────────────┘
```

### 8. Staleness & Validation Logic

**KT Technical Refresh Cadence:**
- KT publishes weekly blog/newsletter updates with refreshed wave counts and levels
- When new KT content is ingested, levels are refreshed automatically
- If no KT update for 14 days, levels are marked STALE with a clear warning
- Stale levels remain visible but with prominent "⚠️ No update in 14+ days - levels may be invalidated" warning

**Discord Refresh Cadence:**
- Stock Compass updates more frequently (multiple times per week)
- Text posts with level mentions refresh those specific levels
- 14-day staleness threshold applies here too

```python
# Run daily or on each analysis cycle

def check_source_freshness():
    """Check if sources have been updated recently and warn if stale."""
    kt_cutoff = datetime.utcnow() - timedelta(days=14)
    discord_cutoff = datetime.utcnow() - timedelta(days=14)

    # Check KT Technical freshness per symbol
    kt_stale_symbols = db.query(SymbolState).filter(
        SymbolState.kt_last_updated < kt_cutoff
    ).all()

    for state in kt_stale_symbols:
        state.kt_is_stale = True
        state.kt_stale_warning = f"No KT update since {state.kt_last_updated.strftime('%b %d')} - levels may be invalidated"

        # Mark associated levels as stale
        db.query(SymbolLevel).filter(
            SymbolLevel.symbol == state.symbol,
            SymbolLevel.source == 'kt_technical',
            SymbolLevel.is_stale == False
        ).update({
            'is_stale': True,
            'stale_reason': 'No source update in 14+ days'
        })

def refresh_levels_from_content(content_id: int, source: str, symbols_mentioned: List[str]):
    """
    When new content is ingested, refresh levels for mentioned symbols.
    This resets the staleness clock for that source.
    """
    now = datetime.utcnow()

    # Update SymbolState freshness
    for symbol in symbols_mentioned:
        state = db.query(SymbolState).filter_by(symbol=symbol).first()
        if state:
            if source == 'kt_technical':
                state.kt_last_updated = now
                state.kt_is_stale = False
                state.kt_stale_warning = None
            elif source == 'discord':
                state.discord_last_updated = now
                state.discord_is_stale = False

    # Refresh level confirmation dates and clear stale flag
    db.query(SymbolLevel).filter(
        SymbolLevel.symbol.in_(symbols_mentioned),
        SymbolLevel.source == source,
        SymbolLevel.is_active == True
    ).update({
        'last_confirmed_at': now,
        'is_stale': False,
        'stale_reason': None
    })

def invalidate_broken_levels():
    """Invalidate levels that price has clearly broken through."""
    for symbol_state in db.query(SymbolState).all():
        price = symbol_state.current_price
        if not price:
            continue

        # Get active support levels where price is now 5%+ below
        supports = db.query(SymbolLevel).filter(
            SymbolLevel.symbol == symbol_state.symbol,
            SymbolLevel.level_type == 'support',
            SymbolLevel.is_active == True,
            SymbolLevel.price > price * 1.05  # Price 5%+ below support
        ).all()

        for level in supports:
            level.is_active = False
            level.invalidated_at = datetime.utcnow()
            level.invalidation_reason = f"Price broke below {level.price}"
```

## File Changes

### New Files
- `agents/symbol_level_extractor.py` - Level extraction agent
- `backend/routes/symbols.py` - Symbol API endpoints
- `frontend/js/symbols.js` - Symbols tab JavaScript
- `frontend/css/components/_symbols.css` - Symbols tab styling
- `database/migrations/007_add_symbol_tracking.py` - Database migration
- `tests/test_prd039_symbols.py` - Unit tests

### Modified Files
- `backend/models.py` - Add SymbolLevel, SymbolState models
- `backend/app.py` - Register symbols router
- `mcp/server.py` - Add 5 new MCP tools
- `frontend/index.html` - Add Symbols tab
- `frontend/js/main.js` - Wire up Symbols tab
- `collectors/discord_collector.py` - Compass image detection
- `agents/transcript_harvester.py` - Trigger level extraction

## Testing

### Unit Tests (`tests/test_prd039_symbols.py`)
- Level extraction from sample transcripts (KT Technical patterns)
- Level extraction from sample Discord text posts
- Direction vector assignment (bullish_reversal, bearish_breakdown, etc.)
- Context snippet extraction (exact quotes preserved)
- Wave phase detection (impulse vs correction)
- Invalidation price extraction
- Chart image parsing (mock vision responses)
- Compass image parsing (mock vision responses)
- Confluence score calculation logic (requires direction alignment)
- Staleness marking after 14 days
- Level invalidation when manually marked
- Symbol alias resolution (GOOGLE → GOOGL, S&P → SPX, etc.)
- Transcript chunking for long videos (30+ min)
- Low confidence flagging (< 0.7)
- SymbolLevel and SymbolState model validation

### Integration Tests (`tests/test_prd039_integration.py`)
- End-to-end: KT content ingestion → level extraction → database storage
- End-to-end: Discord content ingestion → compass parsing → database storage
- API endpoint responses: `/api/symbols`, `/api/symbols/{symbol}`, `/api/symbols/confluence`
- MCP tool responses: `get_symbol_analysis`, `get_confluence_opportunities`, `get_trade_setup`
- Staleness refresh: new content resets staleness clock
- Multi-symbol extraction from single transcript

### UI Tests (`tests/frontend/symbols.spec.js` - Playwright)
- Symbols tab renders with all 11 tracked symbols
- Symbol list shows correct KT/Discord state indicators
- Symbol list shows confluence scores with correct styling
- Symbol list shows staleness warnings for outdated data
- Click symbol opens detail view
- Detail view shows KT Technical section with wave phase (IMPULSE/CORRECTION)
- Detail view shows Discord Options section
- Detail view shows price levels sorted correctly
- Detail view shows context snippets on hover
- Detail view shows confluence analysis
- Detail view shows suggested setup (only when sources aligned)
- Conflicting directions show warning instead of setup
- "View KT Source" and "View Discord Source" links work
- "Copy to Clipboard" copies setup text
- Edit level: clicking ✏️ opens edit modal, saves changes via API
- Dismiss level: clicking dismiss marks level inactive
- Stale symbol shows warning banner in detail view
- Low confidence levels (< 0.7) show review flag
- Empty state handled gracefully (no data for symbol)

## Success Metrics

1. **Extraction accuracy**: >85% of levels correctly extracted from transcripts, >80% from images
2. **Confluence detection**: High-confluence setups surfaced within 1 hour of content ingestion
3. **User value**: MCP tools enable quick trade brainstorming without manual research aggregation

## Dependencies

- Claude vision API (already available)
- Existing transcript/image analysis pipeline

### Cost & Rate Considerations

**Clarification:** Vision API calls are for **static images only**, not video frame extraction:
- KT chart images: ~1-2 images per weekly blog post
- Discord Stock Compass: ~2-3 images per week
- **Expected vision calls:** <20 per week (negligible cost)

Text extraction from transcripts uses the standard Claude API, which is already in use for synthesis.

**Safeguard:** If image volume unexpectedly increases, implement a daily cap of 50 vision API calls with alerting.

## Rollout

0. **Phase 0: Validation** (BEFORE building anything)
   - Take 2-3 real KT Technical transcripts and 2-3 Discord text posts
   - Run the extraction prompts manually against them
   - Verify: Does it correctly identify support vs resistance vs target?
   - Verify: Are direction vectors assigned correctly?
   - Verify: Are context snippets accurate quotes?
   - **Gate:** If extraction accuracy < 70%, refine prompts before proceeding

1. **Phase 1**: Database models + level extraction from transcripts (text-only)
2. **Phase 2**: Chart image vision parsing (KT Technical)
3. **Phase 3**: Compass image vision parsing (Discord)
4. **Phase 4**: Dashboard UI + MCP tools
5. **Phase 5**: Testing, documentation, production deployment

## Open Questions

1. Should we track historical levels (for backtesting) or only active levels?
2. Should confluence score factor in level freshness (newer = higher weight)?

## Future Enhancements (Post-MVP)

1. **Push Notifications**: When `confluence_score > 0.8` is detected, trigger a notification via email or webhook. Currently user must log in to see high-conviction setups.
2. **Historical Level Tracking**: Store invalidated/expired levels for backtesting analysis.
3. **Depth Chart Visualization**: Visual bar chart showing KT support levels vs Discord put walls at same price.

## Definition of Done

PRD-039 is complete when ALL of the following criteria are met:

### Database & Models
- [ ] `SymbolLevel` model implemented with all fields from spec
- [ ] `SymbolState` model implemented with all fields from spec
- [ ] Database migration `007_add_symbol_tracking.py` created and tested
- [ ] Migration runs successfully on both SQLite (dev) and PostgreSQL (prod)

### Phase 0 Validation (Gate)
- [ ] Extraction prompts tested on 2-3 real KT Technical transcripts
- [ ] Extraction prompts tested on 2-3 real Discord text posts
- [ ] Extraction accuracy ≥ 70% on validation samples
- [ ] Direction vectors correctly assigned (bullish_reversal vs bearish_breakdown etc.)
- [ ] Context snippets are accurate quotes from source

### Level Extraction Agent
- [ ] `symbol_level_extractor.py` extracts levels from KT Technical transcripts
- [ ] Agent extracts levels from Discord text posts
- [ ] Agent parses KT chart images using Claude vision
- [ ] Agent parses Discord Stock Compass images using Claude vision
- [ ] Long transcripts (30+ min) are chunked to avoid "lost in middle" errors
- [ ] Symbol alias resolution works (GOOGLE → GOOGL, etc.)
- [ ] Direction vectors extracted for each level
- [ ] Context snippets stored for verification
- [ ] Wave phase (impulse/correction) extracted from KT content
- [ ] Invalidation prices extracted where mentioned
- [ ] Extraction confidence scores are assigned appropriately (flag if < 0.7)

### Staleness Logic
- [ ] Levels automatically marked stale after 14 days without source update
- [ ] New content from source refreshes staleness clock for mentioned symbols
- [ ] Stale warning message clearly displayed in UI and API responses
- [ ] Staleness check runs on scheduled basis (daily)

### API Endpoints
- [ ] `GET /api/symbols` returns all tracked symbols with state summary
- [ ] `GET /api/symbols/{symbol}` returns full detail for one symbol
- [ ] `GET /api/symbols/{symbol}/levels` returns active levels for symbol
- [ ] `GET /api/symbols/confluence` returns aligned high-confluence symbols
- [ ] `POST /api/symbols/refresh` triggers manual level extraction
- [ ] `PATCH /api/symbols/levels/{level_id}` allows user to edit/correct levels
- [ ] `DELETE /api/symbols/levels/{level_id}` allows user to dismiss incorrect levels
- [ ] All endpoints require authentication (consistent with existing auth)

### MCP Tools
- [ ] `get_symbol_analysis` tool implemented and working in Claude Desktop
- [ ] `get_symbol_levels` tool implemented and working
- [ ] `get_confluence_opportunities` tool implemented and working
- [ ] `get_trade_setup` tool implemented and working
- [ ] Tools return well-formatted, actionable data

### Dashboard UI
- [ ] "Symbols" tab added to main navigation
- [ ] Symbol list view displays all 11 tracked symbols
- [ ] List shows KT view, Discord view, confluence score, last updated
- [ ] Stale symbols clearly marked with warning indicator
- [ ] Click symbol opens detail modal/view
- [ ] Detail view shows KT Technical section with wave phase (IMPULSE/CORRECTION)
- [ ] Detail view shows Discord Options section side-by-side
- [ ] Detail view shows all price levels sorted by price
- [ ] Detail view shows context snippets on hover (for verification)
- [ ] Detail view shows confluence analysis summary
- [ ] Detail view shows suggested trade setup when sources directionally aligned
- [ ] Conflicting directions show warning instead of trade setup
- [ ] Low confidence levels (< 0.7) show review flag
- [ ] User can edit/dismiss levels via ✏️ icon (corrects AI errors)
- [ ] "View Source" links navigate to original content
- [ ] "Copy to Clipboard" works for setup text
- [ ] UI follows existing design system (glassmorphism, animations)

### Testing
- [ ] All unit tests in `test_prd039_symbols.py` pass
- [ ] All integration tests in `test_prd039_integration.py` pass
- [ ] All Playwright UI tests in `symbols.spec.js` pass
- [ ] Tests run successfully in GitHub Actions CI

### Documentation
- [ ] CLAUDE.md updated with new MCP tools
- [ ] CLAUDE.md updated with new API endpoints
- [ ] PRD moved to `/docs/archived/` upon completion

### Production Verification
- [ ] Feature deployed to Railway production
- [ ] At least one real KT Technical content processed with levels extracted
- [ ] At least one real Discord Stock Compass parsed successfully
- [ ] MCP tools accessible and working in Claude Desktop
- [ ] Dashboard Symbols tab displays real data correctly
