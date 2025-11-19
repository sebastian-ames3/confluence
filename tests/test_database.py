"""
Database Tests

Comprehensive tests for database schema, utilities, and ORM models.
"""
import pytest
import sqlite3
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.db import DatabaseManager
from backend.models import (
    Source, RawContent, AnalyzedContent, ConfluenceScore,
    Theme, ThemeEvidence, BayesianUpdate
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_db():
    """Create a temporary test database."""
    db_path = "test_confluence.db"
    db = DatabaseManager(db_path)

    # Initialize schema
    db.initialize_schema()

    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_source(test_db):
    """Create a sample source."""
    source_id = test_db.insert("sources", {
        "name": "42macro",
        "type": "web",
        "config": json.dumps({"url": "https://app.42macro.com"}),
        "active": True
    })
    return source_id


# ============================================================================
# Schema Tests
# ============================================================================

def test_schema_initialization(test_db):
    """Test that all tables are created correctly."""
    expected_tables = [
        "sources",
        "raw_content",
        "analyzed_content",
        "confluence_scores",
        "themes",
        "theme_evidence",
        "bayesian_updates"
    ]

    for table in expected_tables:
        # Check table exists by querying it
        result = test_db.execute_query(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        assert len(result) == 1, f"Table {table} should exist"


def test_foreign_keys_enabled(test_db):
    """Test that foreign key constraints are enabled."""
    result = test_db.execute_query("PRAGMA foreign_keys")
    assert result[0][0] == 1, "Foreign keys should be enabled"


# ============================================================================
# CRUD Operations Tests
# ============================================================================

def test_insert_source(test_db):
    """Test inserting a source."""
    source_id = test_db.insert("sources", {
        "name": "discord_test",
        "type": "discord",
        "active": True
    })

    assert source_id > 0, "Should return valid ID"

    # Verify insertion
    sources = test_db.select("sources", filters={"id": source_id})
    assert len(sources) == 1
    assert sources[0]["name"] == "discord_test"


def test_update_source(test_db, sample_source):
    """Test updating a source."""
    success = test_db.update("sources", sample_source, {"active": False})
    assert success, "Update should succeed"

    # Verify update
    sources = test_db.select("sources", filters={"id": sample_source})
    assert sources[0]["active"] == 0  # SQLite stores boolean as 0/1


def test_delete_source(test_db, sample_source):
    """Test deleting a source."""
    success = test_db.delete("sources", sample_source)
    assert success, "Delete should succeed"

    # Verify deletion
    sources = test_db.select("sources", filters={"id": sample_source})
    assert len(sources) == 0


def test_select_with_filters(test_db):
    """Test selecting with filters."""
    # Insert multiple sources
    test_db.insert("sources", {"name": "source1", "type": "web", "active": True})
    test_db.insert("sources", {"name": "source2", "type": "discord", "active": False})
    test_db.insert("sources", {"name": "source3", "type": "web", "active": True})

    # Filter by type
    web_sources = test_db.select("sources", filters={"type": "web"})
    assert len(web_sources) == 2

    # Filter by active
    active_sources = test_db.select("sources", filters={"active": True})
    assert len(active_sources) == 2


def test_select_with_order_and_limit(test_db):
    """Test selecting with ordering and limit."""
    # Insert sources
    for i in range(5):
        test_db.insert("sources", {
            "name": f"source{i}",
            "type": "web",
            "active": True
        })

    # Test limit
    results = test_db.select("sources", limit=3)
    assert len(results) == 3

    # Test order by (ascending)
    results = test_db.select("sources", order_by="name", limit=2)
    assert results[0]["name"] == "source0"

    # Test order by (descending)
    results = test_db.select("sources", order_by="-name", limit=2)
    assert results[0]["name"] == "source4"


# ============================================================================
# Relationship Tests
# ============================================================================

def test_foreign_key_cascade_delete(test_db, sample_source):
    """Test that deleting a source cascades to raw_content."""
    # Insert raw content
    content_id = test_db.insert("raw_content", {
        "source_id": sample_source,
        "content_type": "text",
        "content_text": "Test content",
        "processed": False
    })

    # Verify content exists
    content = test_db.select("raw_content", filters={"id": content_id})
    assert len(content) == 1

    # Delete source
    test_db.delete("sources", sample_source)

    # Verify content was cascade deleted
    content = test_db.select("raw_content", filters={"id": content_id})
    assert len(content) == 0, "Raw content should be cascade deleted"


def test_analyzed_content_relationship(test_db, sample_source):
    """Test analyzed_content to raw_content relationship."""
    # Insert raw content
    raw_id = test_db.insert("raw_content", {
        "source_id": sample_source,
        "content_type": "pdf",
        "file_path": "/path/to/file.pdf",
        "processed": False
    })

    # Insert analyzed content
    analyzed_id = test_db.insert("analyzed_content", {
        "raw_content_id": raw_id,
        "agent_type": "pdf",
        "analysis_result": json.dumps({"themes": ["Fed pivot"]}),
        "key_themes": "Fed pivot, inflation",
        "sentiment": "bullish",
        "conviction": 8
    })

    # Verify relationship
    analyzed = test_db.select("analyzed_content", filters={"id": analyzed_id})
    assert len(analyzed) == 1
    assert analyzed[0]["raw_content_id"] == raw_id


# ============================================================================
# Confluence Score Tests
# ============================================================================

def test_confluence_score_constraints(test_db, sample_source):
    """Test that confluence score constraints are enforced."""
    # Create necessary parent records
    raw_id = test_db.insert("raw_content", {
        "source_id": sample_source,
        "content_type": "text",
        "content_text": "Test",
        "processed": True
    })

    analyzed_id = test_db.insert("analyzed_content", {
        "raw_content_id": raw_id,
        "agent_type": "classifier",
        "analysis_result": json.dumps({}),
        "sentiment": "neutral"
    })

    # Valid score (all pillars 0-2)
    score_id = test_db.insert("confluence_scores", {
        "analyzed_content_id": analyzed_id,
        "macro_score": 2,
        "fundamentals_score": 1,
        "valuation_score": 2,
        "positioning_score": 1,
        "policy_score": 2,
        "price_action_score": 2,
        "options_vol_score": 1,
        "core_total": 8,
        "total_score": 11,
        "meets_threshold": True,
        "reasoning": "Strong macro and valuation alignment"
    })

    assert score_id > 0, "Valid score should be inserted"

    # Test invalid score (out of range) - should fail constraint
    with pytest.raises(sqlite3.IntegrityError):
        test_db.insert("confluence_scores", {
            "analyzed_content_id": analyzed_id,
            "macro_score": 3,  # Invalid! Must be 0-2
            "fundamentals_score": 1,
            "valuation_score": 1,
            "positioning_score": 1,
            "policy_score": 1,
            "price_action_score": 1,
            "options_vol_score": 1,
            "core_total": 8,
            "total_score": 10,
            "meets_threshold": False,
            "reasoning": "Test"
        })


# ============================================================================
# Theme and Evidence Tests
# ============================================================================

def test_theme_lifecycle(test_db):
    """Test creating and updating a theme."""
    # Create theme
    theme_id = test_db.insert("themes", {
        "name": "Tech Sector Rotation",
        "description": "Rotation from growth to value in tech",
        "current_conviction": 0.7,
        "status": "active",
        "evidence_count": 0
    })

    assert theme_id > 0

    # Update conviction
    test_db.update("themes", theme_id, {
        "current_conviction": 0.85,
        "evidence_count": 3
    })

    # Verify update
    theme = test_db.select("themes", filters={"id": theme_id})[0]
    assert theme["current_conviction"] == 0.85
    assert theme["evidence_count"] == 3


def test_theme_evidence_link(test_db, sample_source):
    """Test linking analyzed content to themes via theme_evidence."""
    # Create theme
    theme_id = test_db.insert("themes", {
        "name": "Fed Pivot",
        "current_conviction": 0.6,
        "status": "active"
    })

    # Create analyzed content
    raw_id = test_db.insert("raw_content", {
        "source_id": sample_source,
        "content_type": "text",
        "content_text": "Test"
    })

    analyzed_id = test_db.insert("analyzed_content", {
        "raw_content_id": raw_id,
        "agent_type": "classifier",
        "analysis_result": json.dumps({"theme": "Fed pivot"})
    })

    # Link them
    evidence_id = test_db.insert("theme_evidence", {
        "theme_id": theme_id,
        "analyzed_content_id": analyzed_id,
        "supports_theme": True,
        "evidence_strength": 0.8
    })

    assert evidence_id > 0

    # Verify link
    evidence = test_db.select("theme_evidence", filters={"theme_id": theme_id})
    assert len(evidence) == 1
    assert evidence[0]["evidence_strength"] == 0.8


def test_bayesian_update_tracking(test_db):
    """Test tracking Bayesian updates for themes."""
    # Create theme
    theme_id = test_db.insert("themes", {
        "name": "Inflation Reversal",
        "current_conviction": 0.5,
        "status": "active"
    })

    # Record Bayesian update
    update_id = test_db.insert("bayesian_updates", {
        "theme_id": theme_id,
        "prior_conviction": 0.5,
        "posterior_conviction": 0.65,
        "update_reason": "New CPI data came in lower than expected"
    })

    assert update_id > 0

    # Verify update
    updates = test_db.select("bayesian_updates", filters={"theme_id": theme_id})
    assert len(updates) == 1
    assert updates[0]["posterior_conviction"] == 0.65


# ============================================================================
# Utility Function Tests
# ============================================================================

def test_row_to_dict(test_db, sample_source):
    """Test converting Row objects to dictionaries."""
    row = test_db.execute_query("SELECT * FROM sources WHERE id = ?", (sample_source,), fetch="one")
    data = test_db.row_to_dict(row)

    assert isinstance(data, dict)
    assert "name" in data
    assert "type" in data
    assert data["id"] == sample_source


def test_get_table_info(test_db):
    """Test getting table column information."""
    columns = test_db.get_table_info("sources")

    assert len(columns) > 0
    column_names = [col["name"] for col in columns]
    assert "id" in column_names
    assert "name" in column_names
    assert "type" in column_names


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_content_pipeline(test_db):
    """Test complete flow: source -> raw -> analyzed -> scored -> theme."""
    # 1. Create source
    source_id = test_db.insert("sources", {
        "name": "test_pipeline",
        "type": "web",
        "active": True
    })

    # 2. Collect raw content
    raw_id = test_db.insert("raw_content", {
        "source_id": source_id,
        "content_type": "pdf",
        "file_path": "/test.pdf",
        "metadata": json.dumps({"author": "Test Author"}),
        "processed": False
    })

    # 3. Analyze content
    analyzed_id = test_db.insert("analyzed_content", {
        "raw_content_id": raw_id,
        "agent_type": "pdf",
        "analysis_result": json.dumps({"summary": "Bullish on tech"}),
        "key_themes": "tech rotation, AI growth",
        "tickers_mentioned": "NVDA, MSFT",
        "sentiment": "bullish",
        "conviction": 9,
        "time_horizon": "3m"
    })

    # Mark as processed
    test_db.update("raw_content", raw_id, {"processed": True})

    # 4. Score confluence
    score_id = test_db.insert("confluence_scores", {
        "analyzed_content_id": analyzed_id,
        "macro_score": 2,
        "fundamentals_score": 2,
        "valuation_score": 1,
        "positioning_score": 1,
        "policy_score": 2,
        "price_action_score": 2,
        "options_vol_score": 2,
        "core_total": 8,
        "total_score": 12,
        "meets_threshold": True,
        "reasoning": "Strong alignment across pillars",
        "falsification_criteria": json.dumps(["If NVDA drops below $100"])
    })

    # 5. Create/link to theme
    theme_id = test_db.insert("themes", {
        "name": "AI Infrastructure Boom",
        "description": "AI growth driving infrastructure demand",
        "current_conviction": 0.8,
        "status": "active",
        "evidence_count": 1
    })

    test_db.insert("theme_evidence", {
        "theme_id": theme_id,
        "analyzed_content_id": analyzed_id,
        "supports_theme": True,
        "evidence_strength": 0.9
    })

    # 6. Verify full chain exists
    theme = test_db.select("themes", filters={"id": theme_id})[0]
    assert theme["name"] == "AI Infrastructure Boom"

    evidence = test_db.select("theme_evidence", filters={"theme_id": theme_id})
    assert len(evidence) == 1

    score = test_db.select("confluence_scores", filters={"id": score_id})[0]
    assert score["meets_threshold"] == 1

    analyzed = test_db.select("analyzed_content", filters={"id": analyzed_id})[0]
    assert analyzed["conviction"] == 9

    raw = test_db.select("raw_content", filters={"id": raw_id})[0]
    assert raw["processed"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
