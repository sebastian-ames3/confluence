"""
Migration 007: Add Symbol-Level Confluence Tracking (PRD-039)

Creates two new tables:
1. symbol_levels: Price levels from KT Technical and Discord for tracked symbols
2. symbol_states: Consolidated state per symbol (wave counts, positioning, confluence)

Tracked symbols: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN
"""


def upgrade(db):
    """
    Apply the migration (create tables).

    Args:
        db: DatabaseManager instance
    """
    print("Applying migration 007: Add symbol tracking tables (PRD-039)...")

    with db.get_connection() as conn:
        # Create symbol_levels table
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbol_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10) NOT NULL,
                    source VARCHAR(20) NOT NULL,

                    -- Level details
                    level_type VARCHAR(20) NOT NULL,
                    price FLOAT NOT NULL,
                    price_upper FLOAT,
                    significance VARCHAR(10),

                    -- Direction vector
                    direction VARCHAR(20)
                        CHECK (direction IN ('bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral')),

                    -- Context
                    wave_context VARCHAR(100),
                    options_context VARCHAR(100),
                    fib_level VARCHAR(10),
                    context_snippet VARCHAR(200),

                    -- Extraction metadata
                    confidence FLOAT DEFAULT 0.8,
                    extracted_from_content_id INTEGER REFERENCES raw_content(id),
                    extraction_method VARCHAR(20),

                    -- Validity tracking
                    is_active BOOLEAN DEFAULT 1,
                    invalidation_price FLOAT,
                    invalidated_at TIMESTAMP,
                    invalidation_reason VARCHAR(100),

                    -- Staleness
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_stale BOOLEAN DEFAULT 0,
                    stale_reason VARCHAR(100)
                )
            """)
            print("  Created table: symbol_levels")
        except Exception as e:
            print(f"  Error creating symbol_levels: {e}")

        # Create indexes for symbol_levels
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_source ON symbol_levels(symbol, source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_active ON symbol_levels(symbol, is_active)")
            print("  Created indexes for symbol_levels")
        except Exception as e:
            print(f"  Error creating indexes: {e}")

        # Create symbol_states table
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbol_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10) NOT NULL UNIQUE,

                    -- KT Technical state
                    kt_wave_degree VARCHAR(20),
                    kt_wave_position VARCHAR(20),
                    kt_wave_direction VARCHAR(10),
                    kt_wave_phase VARCHAR(15),
                    kt_bias VARCHAR(10),
                    kt_primary_target FLOAT,
                    kt_primary_support FLOAT,
                    kt_invalidation FLOAT,
                    kt_notes TEXT,
                    kt_last_updated TIMESTAMP,
                    kt_is_stale BOOLEAN DEFAULT 0,
                    kt_stale_warning VARCHAR(100),
                    kt_source_content_id INTEGER REFERENCES raw_content(id),

                    -- Discord Options state
                    discord_quadrant VARCHAR(20),
                    discord_iv_regime VARCHAR(15),
                    discord_strategy_rec VARCHAR(100),
                    discord_key_strikes TEXT,
                    discord_notes TEXT,
                    discord_last_updated TIMESTAMP,
                    discord_is_stale BOOLEAN DEFAULT 0,
                    discord_source_content_id INTEGER REFERENCES raw_content(id),

                    -- Confluence scoring
                    sources_directionally_aligned BOOLEAN,
                    confluence_score FLOAT,
                    confluence_summary TEXT,
                    trade_setup_suggestion TEXT,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  Created table: symbol_states")
        except Exception as e:
            print(f"  Error creating symbol_states: {e}")

        # Create index for symbol_states
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_states_symbol ON symbol_states(symbol)")
            print("  Created index for symbol_states")
        except Exception as e:
            print(f"  Error creating index: {e}")

        # Initialize symbol_states with the 11 tracked symbols
        tracked_symbols = ['SPX', 'QQQ', 'IWM', 'BTC', 'SMH', 'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'MSFT', 'AMZN']
        try:
            for symbol in tracked_symbols:
                conn.execute("""
                    INSERT OR IGNORE INTO symbol_states (symbol) VALUES (?)
                """, (symbol,))
            print(f"  Initialized {len(tracked_symbols)} tracked symbols in symbol_states")
        except Exception as e:
            print(f"  Error initializing symbols: {e}")

    print("SUCCESS: Migration 007 applied successfully")
    print("   - Created symbol_levels table")
    print("   - Created symbol_states table")
    print("   - Initialized 11 tracked symbols")


def downgrade(db):
    """
    Revert the migration (drop tables).

    Args:
        db: DatabaseManager instance
    """
    print("Reverting migration 007: Removing symbol tracking tables...")

    with db.get_connection() as conn:
        try:
            conn.execute("DROP TABLE IF EXISTS symbol_levels")
            conn.execute("DROP TABLE IF EXISTS symbol_states")
            print("  Dropped symbol_levels and symbol_states tables")
        except Exception as e:
            print(f"  Error dropping tables: {e}")

    print("SUCCESS: Migration 007 reverted successfully")
