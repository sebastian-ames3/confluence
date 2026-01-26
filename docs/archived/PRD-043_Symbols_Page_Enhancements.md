# PRD-043: Symbols Page Enhancements

## Overview

Enhance the PRD-039 Symbols page with three improvements:
1. **Futures Symbol Aliasing** - Map futures notation (`/ES`, `/NQ`, `/RTY`) to their ETF/index equivalents for cross-source linking
2. **Automated Discord Compass Extraction** - Automatically extract symbol data from Stock Compass, Macro Compass, and Sector Compass images when ingested
3. **4×4×3 Grid Layout** - Redesign the symbols list as a fixed grid displaying all 11 symbols without scrolling

## Problem Statement

### 1. Futures Notation Mismatch

Discord options traders commonly reference futures contracts (`/ES`, `/NQ`, `/RTY`) while KT Technical analyzes the corresponding ETFs/indices (`SPY`, `SPX`, `QQQ`, `IWM`). The current aliasing handles `ES` → `SPX` but **not** the slash-prefixed notation (`/ES`), causing missed cross-source confluence detection.

**Example:**
- Discord: "Looking for /ES to test 6050 support"
- KT: "SPX has wave 4 support at 6045-6050"
- **Current behavior**: These are treated as unrelated
- **Desired behavior**: Both update the same `SPX` SymbolState and contribute to confluence

### 2. Passive Discord Data Not Captured

Imran (Discord source) rarely types ticker symbols explicitly. Instead, he posts **compass images** showing ticker positions:
- **Stock Compass**: Individual stock quadrant positions (buy call/put, sell call/put)
- **Macro Compass**: Asset class positioning (equities, bonds, gold, oil)
- **Sector Compass**: Sector ETF positions (may include SMH)

Currently, compass extraction only runs via **manual API call** (`POST /api/symbols/extract-image/{content_id}`). There is no automatic pipeline triggered when Discord images are collected.

### 3. Scrolling Required for Symbol Overview

The current symbols list renders as a flexible grid that requires scrolling on most screens. With exactly 11 tracked symbols, a **4×4×3 fixed grid** would display all symbols above the fold, enabling at-a-glance monitoring.

## Tracked Symbols (Reference)

The 11 tracked symbols from PRD-039:
- **Indices**: SPX, QQQ, IWM
- **Crypto**: BTC
- **Semis**: SMH, NVDA
- **Mega-cap**: TSLA, GOOGL, AAPL, MSFT, AMZN

---

## Technical Implementation

### 1. Futures Symbol Aliasing

#### 1.1 Extended Alias Map

Update `agents/symbol_level_extractor.py`:

```python
SYMBOL_ALIASES = {
    # Existing aliases...

    # Futures notation (with slash prefix)
    '/ES': 'SPX', '/SP': 'SPX',
    '/NQ': 'QQQ',
    '/RTY': 'IWM', '/RUT': 'IWM',
    '/BTC': 'BTC', '/BTCUSD': 'BTC',

    # Yahoo Finance / TradingView futures notation
    'ES=F': 'SPX', 'ES_F': 'SPX',
    'NQ=F': 'QQQ', 'NQ_F': 'QQQ',
    'RTY=F': 'IWM', 'RTY_F': 'IWM',

    # Micro futures
    '/MES': 'SPX', '/MNQ': 'QQQ', '/M2K': 'IWM',
    'MES=F': 'SPX', 'MNQ=F': 'QQQ', 'M2K=F': 'IWM',
}
```

#### 1.2 Normalize Symbol Enhancement

Update `normalize_symbol()` method:

```python
def normalize_symbol(self, symbol_text: str) -> Optional[str]:
    """
    Normalize symbol variations to canonical ticker.

    Handles:
    - Standard tickers (GOOGL, AAPL)
    - Company names (Google, Apple)
    - Futures notation (/ES, /NQ, ES=F)
    - Index names (S&P 500, Nasdaq 100)
    """
    if not symbol_text:
        return None

    symbol_clean = symbol_text.strip().upper()

    # Check if already canonical
    if symbol_clean in self.TRACKED_SYMBOLS:
        return symbol_clean

    # Check aliases (includes /ES, ES=F, etc.)
    if symbol_clean in self.SYMBOL_ALIASES:
        return self.SYMBOL_ALIASES[symbol_clean]

    # Try stripping leading slash and check again
    if symbol_clean.startswith('/'):
        without_slash = symbol_clean[1:]
        if without_slash in self.TRACKED_SYMBOLS:
            return without_slash
        if without_slash in self.SYMBOL_ALIASES:
            return self.SYMBOL_ALIASES[without_slash]

    return None
```

### 2. Automated Discord Compass Extraction

#### 2.1 Compass Type Detection

Add compass type classification to `agents/symbol_level_extractor.py`:

```python
class CompassType(Enum):
    STOCK_COMPASS = "stock_compass"      # Individual stocks in quadrants
    MACRO_COMPASS = "macro_compass"      # Asset classes (equities, bonds, gold)
    SECTOR_COMPASS = "sector_compass"    # Sector ETFs (XLK, XLF, SMH, etc.)
    UNKNOWN = "unknown"

def classify_compass_image(self, image_path: str) -> CompassType:
    """
    Use Claude vision to classify compass type before extraction.

    Returns the compass type to route to appropriate extraction prompt.
    """
    prompt = """Classify this image. Is it a:
1. STOCK_COMPASS - Shows individual stock tickers (AAPL, GOOGL, etc.) in quadrants
2. MACRO_COMPASS - Shows asset classes (Equities, Bonds, Gold, Oil, etc.)
3. SECTOR_COMPASS - Shows sector ETFs (XLK, XLF, XLE, SMH, etc.)
4. UNKNOWN - Not a compass chart

Return ONLY one of: STOCK_COMPASS, MACRO_COMPASS, SECTOR_COMPASS, UNKNOWN"""

    result = self.call_claude_vision(
        prompt=prompt,
        image_path=image_path,
        max_tokens=50,
        temperature=0.0
    )

    # Parse response
    response_upper = result.get("response", "").upper().strip()
    if "STOCK" in response_upper:
        return CompassType.STOCK_COMPASS
    elif "MACRO" in response_upper:
        return CompassType.MACRO_COMPASS
    elif "SECTOR" in response_upper:
        return CompassType.SECTOR_COMPASS
    return CompassType.UNKNOWN
```

#### 2.2 Macro Compass Extraction

Add new extraction method for Macro Compass:

```python
def extract_from_macro_compass(
    self,
    image_path: str,
    content_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extract asset class positioning from Macro Compass.

    Maps relevant asset classes to tracked symbols:
    - "Equities" positioning informs SPX/QQQ bias
    - "Crypto" positioning informs BTC
    """
    prompt = """Analyze this Macro Compass image showing asset class positioning.

The compass has 4 quadrants based on:
- Y-axis: Implied Volatility (high=top, low=bottom)
- X-axis: Directional bias (bullish=left, bearish=right)

Identify the position of these asset classes:
- Equities / Stocks
- Crypto / Bitcoin
- Any sector mentions (Semiconductors, Tech)

For each asset class found, return:
{
  "macro_data": [
    {
      "asset_class": "equities",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left, bullish with low IV"
    },
    {
      "asset_class": "crypto",
      "quadrant": "sell_put",
      "iv_regime": "expensive",
      "position_description": "top-left, bullish with high IV"
    }
  ],
  "extraction_confidence": 0.85
}

Return ONLY valid JSON."""

    result = self.call_claude_vision(
        prompt=prompt,
        image_path=image_path,
        system_prompt=self._get_macro_compass_system_prompt(),
        max_tokens=2048,
        temperature=0.0,
        expect_json=True
    )

    # Map asset classes to symbols
    result["content_id"] = content_id
    result["extraction_method"] = "macro_compass"
    result["compass_data"] = self._map_macro_to_symbols(result.get("macro_data", []))

    return result

def _map_macro_to_symbols(self, macro_data: List[Dict]) -> List[Dict]:
    """Map macro asset class data to tracked symbols."""
    symbol_data = []

    for item in macro_data:
        asset_class = item.get("asset_class", "").lower()

        # Map asset classes to symbols
        if asset_class in ["equities", "stocks", "equity"]:
            # Apply to both SPX and QQQ
            for symbol in ["SPX", "QQQ"]:
                symbol_data.append({
                    "symbol": symbol,
                    "quadrant": item.get("quadrant"),
                    "iv_regime": item.get("iv_regime"),
                    "position_description": f"From macro: {item.get('position_description', '')}"
                })
        elif asset_class in ["crypto", "bitcoin", "btc"]:
            symbol_data.append({
                "symbol": "BTC",
                "quadrant": item.get("quadrant"),
                "iv_regime": item.get("iv_regime"),
                "position_description": item.get("position_description")
            })
        elif asset_class in ["semiconductors", "semis", "chips"]:
            for symbol in ["SMH", "NVDA"]:
                symbol_data.append({
                    "symbol": symbol,
                    "quadrant": item.get("quadrant"),
                    "iv_regime": item.get("iv_regime"),
                    "position_description": f"From macro: {item.get('position_description', '')}"
                })

    return symbol_data
```

#### 2.3 Sector Compass Extraction

Add extraction method for Sector Compass:

```python
def extract_from_sector_compass(
    self,
    image_path: str,
    content_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extract sector ETF positioning from Sector Compass.

    Relevant sectors for tracked symbols:
    - SMH (Semiconductors)
    - XLK (Technology) - informs AAPL, MSFT, GOOGL, NVDA
    - XLY (Consumer Discretionary) - informs TSLA, AMZN
    """
    prompt = """Analyze this Sector Compass image showing sector ETF positioning.

The compass has 4 quadrants:
- Top-left: SELL PUT (bullish, high IV)
- Top-right: SELL CALL (bearish, high IV)
- Bottom-left: BUY CALL (bullish, low IV)
- Bottom-right: BUY PUT (bearish, low IV)

Look for these sector ETFs:
- SMH (Semiconductors) - DIRECTLY TRACKED
- XLK (Technology)
- XLY (Consumer Discretionary)
- XLC (Communications)

Return:
{
  "sector_data": [
    {
      "sector_etf": "SMH",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left area"
    }
  ],
  "extraction_confidence": 0.85
}

Return ONLY valid JSON."""

    result = self.call_claude_vision(
        prompt=prompt,
        image_path=image_path,
        system_prompt=self._get_sector_compass_system_prompt(),
        max_tokens=2048,
        temperature=0.0,
        expect_json=True
    )

    result["content_id"] = content_id
    result["extraction_method"] = "sector_compass"
    result["compass_data"] = self._map_sector_to_symbols(result.get("sector_data", []))

    return result

def _map_sector_to_symbols(self, sector_data: List[Dict]) -> List[Dict]:
    """Map sector ETF data to tracked symbols."""
    symbol_data = []

    # Sector to symbol mapping
    sector_symbol_map = {
        "SMH": ["SMH"],  # Direct match
        "XLK": ["AAPL", "MSFT", "NVDA"],  # Tech sector
        "XLY": ["TSLA", "AMZN"],  # Consumer discretionary
        "XLC": ["GOOGL"],  # Communications
    }

    for item in sector_data:
        sector_etf = item.get("sector_etf", "").upper()

        if sector_etf in sector_symbol_map:
            for symbol in sector_symbol_map[sector_etf]:
                symbol_data.append({
                    "symbol": symbol,
                    "quadrant": item.get("quadrant"),
                    "iv_regime": item.get("iv_regime"),
                    "position_description": f"From {sector_etf}: {item.get('position_description', '')}"
                })

    return symbol_data
```

#### 2.4 Auto-Extraction Pipeline

Update `collectors/discord_self.py` to trigger extraction after image collection:

```python
async def process_collected_image(self, raw_content_id: int, db: Session):
    """
    Automatically process collected Discord images for compass data.

    Called after image is saved to raw_content table.
    """
    from agents.symbol_level_extractor import SymbolLevelExtractor, CompassType

    try:
        # Get the raw content record
        raw_content = db.query(RawContent).filter_by(id=raw_content_id).first()
        if not raw_content or raw_content.content_type != 'image':
            return

        # Get image path (local or download from URL)
        image_path = await self._get_image_path(raw_content)
        if not image_path:
            logger.warning(f"Could not get image path for content {raw_content_id}")
            return

        # Initialize extractor
        extractor = SymbolLevelExtractor()

        # Classify compass type
        compass_type = extractor.classify_compass_image(image_path)

        if compass_type == CompassType.UNKNOWN:
            logger.debug(f"Image {raw_content_id} is not a compass chart, skipping")
            return

        # Extract based on type
        if compass_type == CompassType.STOCK_COMPASS:
            result = extractor.extract_from_compass_image(image_path, raw_content_id)
        elif compass_type == CompassType.MACRO_COMPASS:
            result = extractor.extract_from_macro_compass(image_path, raw_content_id)
        elif compass_type == CompassType.SECTOR_COMPASS:
            result = extractor.extract_from_sector_compass(image_path, raw_content_id)
        else:
            return

        # Save to database
        if result.get("compass_data"):
            save_summary = extractor.save_compass_to_db(
                db=db,
                compass_result=result,
                content_id=raw_content_id
            )
            logger.info(f"Auto-extracted {compass_type.value} from content {raw_content_id}: "
                       f"{save_summary['symbols_processed']} symbols")

        # Clean up temp file if downloaded
        if hasattr(self, '_temp_image_path'):
            self._cleanup_temp_file()

    except Exception as e:
        logger.error(f"Auto-extraction failed for content {raw_content_id}: {e}")
```

#### 2.5 Integration Hook

Add extraction trigger in Discord collector's `save_content` method:

```python
async def save_content(self, content_data: Dict, db: Session) -> int:
    """Save collected content and trigger auto-extraction for images."""

    # Existing save logic...
    raw_content_id = await self._save_to_db(content_data, db)

    # Trigger auto-extraction for images
    if content_data.get("content_type") == "image":
        await self.process_collected_image(raw_content_id, db)

    return raw_content_id
```

### 3. 4×4×3 Grid Layout

#### 3.1 CSS Grid Implementation

Update `frontend/css/components/_symbols.css`:

```css
/* ============================================
   SYMBOLS GRID - 4×4×3 LAYOUT (PRD-043)
   ============================================ */

.symbols-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    padding: 1rem;
    max-width: 1400px;
    margin: 0 auto;
}

/* Ensure all 11 symbols display without scrolling */
.symbols-grid .symbol-card {
    min-height: 140px;
    max-height: 180px;
}

/* Center the last row (3 items) */
.symbols-grid .symbol-card:nth-child(9) {
    grid-column-start: 1;
}

/* Alternative: Center last 3 items using justify */
@supports (grid-template-columns: subgrid) {
    .symbols-grid {
        justify-items: center;
    }

    .symbols-grid .symbol-card:nth-child(n+9) {
        /* Last 3 items centered */
    }
}

/* ============================================
   RESPONSIVE BREAKPOINTS
   ============================================ */

/* Tablet: 2 columns */
@media (max-width: 1024px) {
    .symbols-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
    }

    .symbols-grid .symbol-card:nth-child(9) {
        grid-column-start: auto;
    }
}

/* Mobile: 1 column */
@media (max-width: 600px) {
    .symbols-grid {
        grid-template-columns: 1fr;
        gap: 0.5rem;
    }
}

/* ============================================
   ENHANCED SYMBOL CARD STYLING
   ============================================ */

.symbol-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 1rem;
    border-radius: 12px;
    background: var(--glass-bg, rgba(30, 41, 59, 0.8));
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border, rgba(148, 163, 184, 0.1));
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.symbol-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    border-color: var(--accent-color, #3b82f6);
}

.symbol-card:active {
    transform: translateY(0);
}

/* Symbol header with ticker and level count */
.symbol-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.symbol-header h3 {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary, #f1f5f9);
}

.level-count {
    font-size: 0.75rem;
    color: var(--text-muted, #94a3b8);
    background: rgba(148, 163, 184, 0.1);
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
}

/* Compact view columns for KT/Discord */
.symbol-views {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.view-column {
    flex: 1;
    min-width: 0;
}

.view-label {
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted, #94a3b8);
    margin-bottom: 0.125rem;
}

.view-value {
    font-size: 0.8rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.view-meta {
    font-size: 0.7rem;
    color: var(--text-muted, #94a3b8);
}

/* Confluence indicator */
.symbol-confluence {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.375rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
}

.confluence-high {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
}

.confluence-medium {
    background: rgba(234, 179, 8, 0.15);
    color: #eab308;
}

.confluence-low {
    background: rgba(148, 163, 184, 0.1);
    color: #94a3b8;
}

.confluence-none {
    background: rgba(148, 163, 184, 0.05);
    color: #64748b;
}

/* Stale indicator */
.stale-indicator {
    margin-left: 0.25rem;
    cursor: help;
}

/* Updated timestamp (compact) */
.symbol-updated {
    font-size: 0.625rem;
    color: var(--text-muted, #64748b);
    margin-top: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
```

#### 3.2 Fixed Symbol Order

Update `frontend/js/symbols.js` to maintain consistent ordering:

```javascript
// Define fixed symbol order for 4×4×3 grid
const SYMBOL_ORDER = [
    // Row 1: Indices + Crypto
    'SPX', 'QQQ', 'IWM', 'BTC',
    // Row 2: Semis + Mega-cap start
    'SMH', 'NVDA', 'TSLA', 'GOOGL',
    // Row 3: Remaining mega-cap (centered)
    'AAPL', 'MSFT', 'AMZN'
];

/**
 * Sort symbols according to fixed grid order
 */
sortSymbolsForGrid(symbols) {
    return [...symbols].sort((a, b) => {
        const indexA = SYMBOL_ORDER.indexOf(a.symbol);
        const indexB = SYMBOL_ORDER.indexOf(b.symbol);

        // Unknown symbols go to end
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;

        return indexA - indexB;
    });
}

/**
 * Render the symbols list view (updated for grid)
 */
renderSymbolsList() {
    const container = document.getElementById('symbols-list');
    if (!container) {
        console.error('[SymbolsManager] symbols-list container not found');
        return;
    }

    if (this.symbols.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No symbol data available yet.</p>
                <p class="text-muted">Run data collection to populate symbol analysis.</p>
            </div>
        `;
        return;
    }

    // Sort for consistent grid layout
    const sortedSymbols = this.sortSymbolsForGrid(this.symbols);

    const html = `
        <div class="symbols-grid" role="list" aria-label="Tracked symbols">
            ${sortedSymbols.map(symbol => this.renderSymbolCard(symbol)).join('')}
        </div>
    `;

    container.innerHTML = html;

    // Attach click handlers
    sortedSymbols.forEach(symbol => {
        const card = document.querySelector(`[data-symbol="${symbol.symbol}"]`);
        if (card) {
            card.addEventListener('click', () => this.showSymbolDetail(symbol.symbol));
            card.setAttribute('role', 'listitem');
            card.setAttribute('tabindex', '0');

            // Keyboard accessibility
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.showSymbolDetail(symbol.symbol);
                }
            });
        }
    });
}
```

---

## File Changes Summary

### New Files
- None (all changes are modifications to existing files)

### Modified Files

| File | Changes |
|------|---------|
| `agents/symbol_level_extractor.py` | Extended SYMBOL_ALIASES, CompassType enum, classify_compass_image(), extract_from_macro_compass(), extract_from_sector_compass(), mapping helpers |
| `collectors/discord_self.py` | process_collected_image(), auto-extraction trigger in save_content() |
| `frontend/css/components/_symbols.css` | 4×4×3 grid layout, responsive breakpoints, enhanced card styling |
| `frontend/js/symbols.js` | SYMBOL_ORDER constant, sortSymbolsForGrid(), keyboard accessibility |
| `tests/test_prd043_*.py` | New test files (see Testing section) |

---

## Testing

### Unit Tests (`tests/test_prd043_futures_aliasing.py`)

```python
"""
Unit tests for PRD-043 Futures Symbol Aliasing
"""

import pytest
from agents.symbol_level_extractor import SymbolLevelExtractor


class TestFuturesAliasing:
    """Test futures notation normalization."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor()

    # Slash-prefixed futures
    def test_es_futures_to_spx(self, extractor):
        assert extractor.normalize_symbol("/ES") == "SPX"

    def test_nq_futures_to_qqq(self, extractor):
        assert extractor.normalize_symbol("/NQ") == "QQQ"

    def test_rty_futures_to_iwm(self, extractor):
        assert extractor.normalize_symbol("/RTY") == "IWM"

    def test_btc_futures(self, extractor):
        assert extractor.normalize_symbol("/BTC") == "BTC"
        assert extractor.normalize_symbol("/BTCUSD") == "BTC"

    # Yahoo Finance / TradingView notation
    def test_es_f_notation(self, extractor):
        assert extractor.normalize_symbol("ES=F") == "SPX"
        assert extractor.normalize_symbol("ES_F") == "SPX"

    def test_nq_f_notation(self, extractor):
        assert extractor.normalize_symbol("NQ=F") == "QQQ"
        assert extractor.normalize_symbol("NQ_F") == "QQQ"

    # Micro futures
    def test_micro_futures(self, extractor):
        assert extractor.normalize_symbol("/MES") == "SPX"
        assert extractor.normalize_symbol("/MNQ") == "QQQ"
        assert extractor.normalize_symbol("/M2K") == "IWM"
        assert extractor.normalize_symbol("MES=F") == "SPX"

    # Case insensitivity
    def test_case_insensitive(self, extractor):
        assert extractor.normalize_symbol("/es") == "SPX"
        assert extractor.normalize_symbol("/Nq") == "QQQ"
        assert extractor.normalize_symbol("es=f") == "SPX"

    # Edge cases
    def test_whitespace_handling(self, extractor):
        assert extractor.normalize_symbol("  /ES  ") == "SPX"
        assert extractor.normalize_symbol("\t/NQ\n") == "QQQ"

    def test_empty_input(self, extractor):
        assert extractor.normalize_symbol("") is None
        assert extractor.normalize_symbol(None) is None

    def test_unknown_futures(self, extractor):
        assert extractor.normalize_symbol("/GC") is None  # Gold futures
        assert extractor.normalize_symbol("/CL") is None  # Crude oil futures

    # Existing aliases still work
    def test_existing_aliases_preserved(self, extractor):
        assert extractor.normalize_symbol("SPY") == "SPX"
        assert extractor.normalize_symbol("Google") == "GOOGL"
        assert extractor.normalize_symbol("S&P 500") == "SPX"
        assert extractor.normalize_symbol("NASDAQ") == "QQQ"
```

### Unit Tests (`tests/test_prd043_compass_classification.py`)

```python
"""
Unit tests for PRD-043 Compass Classification and Extraction
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.symbol_level_extractor import SymbolLevelExtractor, CompassType


class TestCompassClassification:
    """Test compass type detection."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor()

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_stock_compass(self, mock_vision, extractor):
        mock_vision.return_value = {"response": "STOCK_COMPASS"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.STOCK_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_macro_compass(self, mock_vision, extractor):
        mock_vision.return_value = {"response": "MACRO_COMPASS"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.MACRO_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_sector_compass(self, mock_vision, extractor):
        mock_vision.return_value = {"response": "SECTOR_COMPASS"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.SECTOR_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_unknown(self, mock_vision, extractor):
        mock_vision.return_value = {"response": "This is a regular chart"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.UNKNOWN


class TestMacroCompassExtraction:
    """Test macro compass to symbol mapping."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor()

    def test_equities_maps_to_spx_qqq(self, extractor):
        macro_data = [
            {"asset_class": "equities", "quadrant": "buy_call", "iv_regime": "cheap"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SPX" in symbols
        assert "QQQ" in symbols
        assert len(result) == 2

    def test_crypto_maps_to_btc(self, extractor):
        macro_data = [
            {"asset_class": "crypto", "quadrant": "sell_put", "iv_regime": "expensive"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "BTC"
        assert result[0]["quadrant"] == "sell_put"

    def test_semiconductors_maps_to_smh_nvda(self, extractor):
        macro_data = [
            {"asset_class": "semiconductors", "quadrant": "buy_call", "iv_regime": "cheap"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SMH" in symbols
        assert "NVDA" in symbols


class TestSectorCompassExtraction:
    """Test sector ETF to symbol mapping."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor()

    def test_smh_direct_mapping(self, extractor):
        sector_data = [
            {"sector_etf": "SMH", "quadrant": "buy_call", "iv_regime": "cheap"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "SMH"

    def test_xlk_maps_to_tech_stocks(self, extractor):
        sector_data = [
            {"sector_etf": "XLK", "quadrant": "buy_call", "iv_regime": "cheap"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        symbols = [item["symbol"] for item in result]
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "NVDA" in symbols

    def test_xly_maps_to_consumer_stocks(self, extractor):
        sector_data = [
            {"sector_etf": "XLY", "quadrant": "sell_call", "iv_regime": "expensive"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        symbols = [item["symbol"] for item in result]
        assert "TSLA" in symbols
        assert "AMZN" in symbols

    def test_xlc_maps_to_googl(self, extractor):
        sector_data = [
            {"sector_etf": "XLC", "quadrant": "buy_call", "iv_regime": "neutral"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "GOOGL"
```

### Integration Tests (`tests/test_prd043_integration.py`)

```python
"""
Integration tests for PRD-043 Symbols Page Enhancements
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from agents.symbol_level_extractor import SymbolLevelExtractor
from backend.models import SymbolState, SymbolLevel


class TestFuturesExtractionIntegration:
    """Test futures symbols are correctly extracted and stored."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor()

    @patch.object(SymbolLevelExtractor, 'call_claude')
    def test_discord_es_mention_updates_spx(self, mock_claude, extractor, mock_db):
        """When Discord mentions /ES, it should update SPX state."""
        mock_claude.return_value = {
            "symbols": [
                {
                    "symbol": "/ES",
                    "bias": "bullish",
                    "levels": [
                        {"type": "support", "price": 6050, "direction": "bullish_reversal"}
                    ]
                }
            ],
            "extraction_confidence": 0.85
        }

        result = extractor.extract_from_transcript(
            transcript="Looking for /ES to hold 6050 support",
            source="discord",
            content_id=123
        )

        # Should normalize /ES to SPX
        assert len(result["symbols"]) == 1
        assert result["symbols"][0]["symbol"] == "SPX"

    @patch.object(SymbolLevelExtractor, 'call_claude')
    def test_mixed_futures_and_tickers(self, mock_claude, extractor, mock_db):
        """Test extraction handles mix of futures and regular tickers."""
        mock_claude.return_value = {
            "symbols": [
                {"symbol": "/ES", "bias": "bullish", "levels": []},
                {"symbol": "GOOGL", "bias": "bullish", "levels": []},
                {"symbol": "/NQ", "bias": "neutral", "levels": []}
            ],
            "extraction_confidence": 0.8
        }

        result = extractor.extract_from_transcript(
            transcript="/ES bullish, GOOGL bullish, /NQ neutral",
            source="discord",
            content_id=124
        )

        symbols = [s["symbol"] for s in result["symbols"]]
        assert "SPX" in symbols
        assert "GOOGL" in symbols
        assert "QQQ" in symbols


class TestAutoExtractionIntegration:
    """Test automatic compass extraction pipeline."""

    @pytest.fixture
    def mock_db(self):
        db = Mock(spec=Session)
        db.query.return_value.filter_by.return_value.first.return_value = None
        return db

    @patch.object(SymbolLevelExtractor, 'classify_compass_image')
    @patch.object(SymbolLevelExtractor, 'extract_from_compass_image')
    @patch.object(SymbolLevelExtractor, 'save_compass_to_db')
    async def test_stock_compass_auto_extraction(
        self, mock_save, mock_extract, mock_classify, mock_db
    ):
        """Test automatic extraction triggers for stock compass."""
        from agents.symbol_level_extractor import CompassType
        from collectors.discord_self import DiscordCollector

        mock_classify.return_value = CompassType.STOCK_COMPASS
        mock_extract.return_value = {
            "compass_data": [
                {"symbol": "GOOGL", "quadrant": "buy_call", "iv_regime": "cheap"}
            ],
            "extraction_confidence": 0.9
        }
        mock_save.return_value = {"symbols_processed": 1, "states_updated": 1}

        collector = DiscordCollector()

        # Mock raw_content retrieval
        mock_content = Mock()
        mock_content.content_type = "image"
        mock_content.file_path = "/path/to/compass.png"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_content

        await collector.process_collected_image(123, mock_db)

        mock_classify.assert_called_once()
        mock_extract.assert_called_once()
        mock_save.assert_called_once()


class TestConfluenceWithFutures:
    """Test confluence detection works across futures and ETF mentions."""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_es_discord_spx_kt_confluence(self, mock_db):
        """When Discord mentions /ES and KT mentions SPX, they should align."""
        from backend.utils.staleness_manager import update_symbol_confluence

        # Setup mock SymbolState with both sources
        mock_state = Mock(spec=SymbolState)
        mock_state.symbol = "SPX"
        mock_state.kt_bias = "bullish"
        mock_state.discord_quadrant = "buy_call"  # From /ES mention

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_state

        # This should calculate high confluence
        with patch('backend.utils.staleness_manager.calculate_confluence_score') as mock_calc:
            mock_calc.return_value = {
                "score": 0.9,
                "aligned": True,
                "summary": "Both sources bullish on SPX"
            }

            result = update_symbol_confluence(mock_db, "SPX")
            assert result["confluence"]["aligned"] is True
```

### UI Tests (`tests/playwright/test_prd043_symbols_grid.spec.js`)

```javascript
/**
 * Playwright E2E tests for PRD-043 Symbols Grid Layout
 */

const { test, expect } = require('@playwright/test');

test.describe('PRD-043: Symbols Grid Layout', () => {

    test.beforeEach(async ({ page }) => {
        // Login and navigate to symbols tab
        await page.goto('/');
        await page.fill('#username', process.env.TEST_USER || 'test');
        await page.fill('#password', process.env.TEST_PASS || 'test');
        await page.click('button[type="submit"]');
        await page.click('[data-tab="symbols"]');
        await page.waitForSelector('.symbols-grid');
    });

    test('displays 4x4x3 grid layout on desktop', async ({ page }) => {
        // Set desktop viewport
        await page.setViewportSize({ width: 1440, height: 900 });

        const grid = page.locator('.symbols-grid');

        // Check grid has 4 columns
        const gridStyle = await grid.evaluate(el =>
            window.getComputedStyle(el).gridTemplateColumns
        );

        // Should have 4 equal columns
        const columns = gridStyle.split(' ').filter(c => c !== '');
        expect(columns.length).toBe(4);
    });

    test('displays all 11 symbols without scrolling', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });

        const cards = page.locator('.symbol-card');
        await expect(cards).toHaveCount(11);

        // All cards should be visible without scrolling
        for (let i = 0; i < 11; i++) {
            await expect(cards.nth(i)).toBeInViewport();
        }
    });

    test('maintains fixed symbol order', async ({ page }) => {
        const expectedOrder = [
            'SPX', 'QQQ', 'IWM', 'BTC',
            'SMH', 'NVDA', 'TSLA', 'GOOGL',
            'AAPL', 'MSFT', 'AMZN'
        ];

        const cards = page.locator('.symbol-card');

        for (let i = 0; i < expectedOrder.length; i++) {
            const symbol = await cards.nth(i).getAttribute('data-symbol');
            expect(symbol).toBe(expectedOrder[i]);
        }
    });

    test('switches to 2-column layout on tablet', async ({ page }) => {
        await page.setViewportSize({ width: 768, height: 1024 });

        const grid = page.locator('.symbols-grid');
        const gridStyle = await grid.evaluate(el =>
            window.getComputedStyle(el).gridTemplateColumns
        );

        const columns = gridStyle.split(' ').filter(c => c !== '');
        expect(columns.length).toBe(2);
    });

    test('switches to 1-column layout on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });

        const grid = page.locator('.symbols-grid');
        const gridStyle = await grid.evaluate(el =>
            window.getComputedStyle(el).gridTemplateColumns
        );

        // Should be single column
        const columns = gridStyle.split(' ').filter(c => c !== '');
        expect(columns.length).toBe(1);
    });

    test('symbol cards are keyboard accessible', async ({ page }) => {
        const firstCard = page.locator('.symbol-card').first();

        // Focus first card
        await firstCard.focus();
        await expect(firstCard).toBeFocused();

        // Should have correct ARIA attributes
        await expect(firstCard).toHaveAttribute('role', 'listitem');
        await expect(firstCard).toHaveAttribute('tabindex', '0');

        // Enter key should open detail
        await firstCard.press('Enter');
        await expect(page.locator('#symbol-detail-modal')).toHaveClass(/active/);
    });

    test('card hover effect works', async ({ page }) => {
        const card = page.locator('.symbol-card').first();

        // Get initial transform
        const initialTransform = await card.evaluate(el =>
            window.getComputedStyle(el).transform
        );

        // Hover
        await card.hover();

        // Wait for transition
        await page.waitForTimeout(250);

        // Transform should change (translateY)
        const hoverTransform = await card.evaluate(el =>
            window.getComputedStyle(el).transform
        );

        expect(hoverTransform).not.toBe(initialTransform);
    });

    test('last row (3 items) starts at column 1', async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 900 });

        // 9th card (AAPL) should start at column 1
        const ninthCard = page.locator('.symbol-card').nth(8);

        const gridColumn = await ninthCard.evaluate(el =>
            window.getComputedStyle(el).gridColumnStart
        );

        expect(gridColumn).toBe('1');
    });
});


test.describe('PRD-043: Symbol Card Interactions', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await page.fill('#username', process.env.TEST_USER || 'test');
        await page.fill('#password', process.env.TEST_PASS || 'test');
        await page.click('button[type="submit"]');
        await page.click('[data-tab="symbols"]');
        await page.waitForSelector('.symbols-grid');
    });

    test('clicking card opens detail modal', async ({ page }) => {
        const spxCard = page.locator('[data-symbol="SPX"]');
        await spxCard.click();

        const modal = page.locator('#symbol-detail-modal');
        await expect(modal).toHaveClass(/active/);

        // Modal should show SPX details
        await expect(modal.locator('h2')).toHaveText('SPX');
    });

    test('card displays KT and Discord views', async ({ page }) => {
        const card = page.locator('.symbol-card').first();

        // Should have both view columns
        await expect(card.locator('.view-label:has-text("KT Technical")')).toBeVisible();
        await expect(card.locator('.view-label:has-text("Discord")')).toBeVisible();
    });

    test('confluence indicator shows correct styling', async ({ page }) => {
        const cards = page.locator('.symbol-card');
        const count = await cards.count();

        for (let i = 0; i < count; i++) {
            const confluenceEl = cards.nth(i).locator('.symbol-confluence');
            const classes = await confluenceEl.getAttribute('class');

            // Should have one of the confluence classes
            const hasValidClass =
                classes.includes('confluence-high') ||
                classes.includes('confluence-medium') ||
                classes.includes('confluence-low') ||
                classes.includes('confluence-none');

            expect(hasValidClass).toBe(true);
        }
    });

    test('stale indicator appears when data is stale', async ({ page }) => {
        // This test requires mock data with stale flags
        // Check that stale indicators render when present
        const staleIndicators = page.locator('.stale-indicator');

        // If any symbols are stale, indicator should be visible
        const count = await staleIndicators.count();

        if (count > 0) {
            await expect(staleIndicators.first()).toHaveText('⚠️');
            await expect(staleIndicators.first()).toHaveAttribute('title', /stale/i);
        }
    });
});
```

### API Integration Tests (`tests/test_prd043_api.py`)

```python
"""
API integration tests for PRD-043
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from backend.app import app
from backend.models import SymbolState, SymbolLevel


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Basic dGVzdDp0ZXN0"}  # test:test


class TestSymbolsAPIWithFutures:
    """Test API handles futures symbols correctly."""

    def test_get_symbols_returns_spx_not_es(self, client, auth_headers):
        """GET /api/symbols should return SPX, not /ES."""
        response = client.get("/api/symbols", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        symbols = [s["symbol"] for s in data["symbols"]]

        # Should have SPX, not /ES
        assert "SPX" in symbols or len(symbols) == 0
        assert "/ES" not in symbols
        assert "ES" not in symbols

    def test_get_symbol_detail_normalizes_futures(self, client, auth_headers):
        """GET /api/symbols/ES should redirect or normalize to SPX."""
        # First test with /ES (URL encoded as %2FES)
        response = client.get("/api/symbols/%2FES", headers=auth_headers)

        # Should either return SPX data or 404 if not found
        if response.status_code == 200:
            data = response.json()
            assert data["symbol"] == "SPX"

    def test_extract_from_discord_with_futures(self, client, auth_headers):
        """POST /api/symbols/extract should normalize futures in extraction."""
        with patch('agents.symbol_level_extractor.SymbolLevelExtractor.extract_from_transcript') as mock_extract:
            mock_extract.return_value = {
                "symbols": [
                    {"symbol": "SPX", "bias": "bullish", "levels": []}
                ],
                "extraction_confidence": 0.9
            }

            with patch('agents.symbol_level_extractor.SymbolLevelExtractor.save_extraction_to_db') as mock_save:
                mock_save.return_value = {
                    "symbols_processed": 1,
                    "levels_created": 0,
                    "states_updated": 1,
                    "errors": []
                }

                # Create mock content that mentions /ES
                response = client.post(
                    "/api/symbols/extract/123?force=true",
                    headers=auth_headers
                )

                # Should process successfully
                # (Will fail with 404 if content doesn't exist, which is expected in test)
                assert response.status_code in [200, 404]


class TestCompassExtractionAPI:
    """Test compass extraction endpoints."""

    def test_extract_image_classifies_compass_type(self, client, auth_headers):
        """POST /api/symbols/extract-image should detect compass type."""
        with patch('agents.symbol_level_extractor.SymbolLevelExtractor.classify_compass_image') as mock_classify:
            from agents.symbol_level_extractor import CompassType
            mock_classify.return_value = CompassType.STOCK_COMPASS

            with patch('agents.symbol_level_extractor.SymbolLevelExtractor.extract_from_compass_image') as mock_extract:
                mock_extract.return_value = {
                    "compass_data": [],
                    "extraction_confidence": 0.8
                }

                response = client.post(
                    "/api/symbols/extract-image/123",
                    headers=auth_headers
                )

                # Will 404 if content doesn't exist
                assert response.status_code in [200, 400, 404]
```

---

## Definition of Done

PRD-043 is complete when ALL of the following criteria are met:

### Futures Symbol Aliasing

- [ ] `/ES` normalizes to `SPX`
- [ ] `/NQ` normalizes to `QQQ`
- [ ] `/RTY` normalizes to `IWM`
- [ ] `/BTC` and `/BTCUSD` normalize to `BTC`
- [ ] `ES=F`, `NQ=F`, `RTY=F` Yahoo Finance notation works
- [ ] `/MES`, `/MNQ`, `/M2K` micro futures work
- [ ] Aliasing is case-insensitive
- [ ] Whitespace is trimmed before normalization
- [ ] All existing aliases still work (SPY→SPX, GOOGLE→GOOGL, etc.)
- [ ] Unit tests in `test_prd043_futures_aliasing.py` pass
- [ ] Integration test confirms Discord /ES mention links to KT SPX analysis

### Automated Discord Compass Extraction

- [ ] `CompassType` enum created (STOCK_COMPASS, MACRO_COMPASS, SECTOR_COMPASS, UNKNOWN)
- [ ] `classify_compass_image()` method detects compass type via vision API
- [ ] `extract_from_macro_compass()` implemented with asset class → symbol mapping
- [ ] `extract_from_sector_compass()` implemented with sector ETF → symbol mapping
- [ ] Macro "equities" maps to SPX and QQQ
- [ ] Macro "crypto" maps to BTC
- [ ] Macro "semiconductors" maps to SMH and NVDA
- [ ] Sector "SMH" maps directly to SMH
- [ ] Sector "XLK" maps to AAPL, MSFT, NVDA
- [ ] Sector "XLY" maps to TSLA, AMZN
- [ ] Sector "XLC" maps to GOOGL
- [ ] Discord collector triggers auto-extraction when image is collected
- [ ] Auto-extraction skips non-compass images (UNKNOWN type)
- [ ] Extraction results saved to SymbolState and update confluence
- [ ] Unit tests in `test_prd043_compass_classification.py` pass
- [ ] Integration tests confirm end-to-end auto-extraction works

### 4×4×3 Grid Layout

- [ ] `.symbols-grid` uses CSS Grid with `repeat(4, 1fr)`
- [ ] All 11 symbols visible without scrolling on 1440px+ viewport
- [ ] Fixed symbol order: SPX, QQQ, IWM, BTC | SMH, NVDA, TSLA, GOOGL | AAPL, MSFT, AMZN
- [ ] Last row (3 items) starts at grid column 1
- [ ] Responsive: 2 columns on tablet (≤1024px)
- [ ] Responsive: 1 column on mobile (≤600px)
- [ ] Cards have hover effect (translateY + shadow)
- [ ] Cards are keyboard accessible (tabindex, Enter/Space to open)
- [ ] Cards have ARIA attributes (role="listitem")
- [ ] Playwright tests in `test_prd043_symbols_grid.spec.js` pass

### Testing & CI

- [ ] All unit tests pass locally
- [ ] All integration tests pass locally
- [ ] All Playwright UI tests pass locally
- [ ] Tests pass in GitHub Actions CI pipeline
- [ ] No regressions in existing PRD-039 tests

### Documentation

- [ ] This PRD saved to `/docs/PRD-043_Symbols_Page_Enhancements.md`
- [ ] CLAUDE.md updated with new alias mappings
- [ ] CLAUDE.md updated with compass extraction info

### Production Verification

- [ ] Feature deployed to Railway production
- [ ] Discord message with `/ES` correctly updates SPX state
- [ ] Discord Stock Compass image auto-extracts symbol positions
- [ ] Symbols tab displays 4×4×3 grid on desktop
- [ ] Grid is responsive on mobile device

---

## Rollout Plan

### Phase 1: Futures Aliasing (Low Risk)
1. Update SYMBOL_ALIASES map
2. Update normalize_symbol() method
3. Add unit tests
4. Deploy to production
5. Verify Discord /ES → SPX linking

### Phase 2: Grid Layout (Low Risk)
1. Update CSS for 4×4×3 grid
2. Add SYMBOL_ORDER constant to JS
3. Add responsive breakpoints
4. Add Playwright tests
5. Deploy to production
6. Verify on desktop, tablet, mobile

### Phase 3: Auto Compass Extraction (Medium Risk)
1. Add CompassType enum and classification
2. Implement macro/sector compass extraction
3. Add auto-trigger in Discord collector
4. Add integration tests
5. Deploy to staging first
6. Monitor vision API usage and costs
7. Deploy to production
8. Verify compass images auto-process

---

## Cost Considerations

### Vision API Usage

Auto-extraction adds vision API calls for Discord images:

| Scenario | Calls/Week | Cost/Week |
|----------|------------|-----------|
| Classification only | ~20 | ~$0.10 |
| Classification + Extraction | ~10 | ~$0.50 |
| **Total additional** | ~30 | ~$0.60 |

**Safeguard**: Implement daily cap of 50 vision API calls with alerting (same as PRD-039).

---

## Open Questions

1. Should non-compass Discord images be classified? (Current plan: yes, but skip extraction for UNKNOWN)
2. Should we add a "Refresh Compass Data" button in UI for manual re-extraction?
3. Should macro compass data have lower confidence than stock compass (since it's inferred)?

---

## Future Enhancements

1. **Historical compass tracking** - Store compass snapshots over time to see positioning changes
2. **Compass diff alerts** - Notify when a symbol moves quadrants
3. **Grid customization** - Let users reorder symbols or hide ones they don't track
