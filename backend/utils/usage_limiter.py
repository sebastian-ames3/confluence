"""
API Usage Limiter - Prevents Cost Explosions

Simple counter-based budget caps to protect against runaway API costs.
Does not query external billing APIs - just tracks analyses performed.
"""
import logging
from datetime import datetime, date
from typing import Dict, Optional, Tuple
from backend.utils.db import get_db

logger = logging.getLogger(__name__)


class UsageLimiter:
    """
    Enforces daily API usage limits with graceful degradation.

    Hard Limits (Daily):
    - Vision analyses: 20 per day (~$0.70)
    - Transcript analyses: 10 per day (~$0.20)
    - Text analyses: 150 per day (~$3.75)

    Total estimated budget: ~$4.65/day = ~$140/month

    Note: Actual costs may vary based on content length and complexity.
    Estimates based on Claude Sonnet 4 pricing ($3/1M input, $15/1M output).
    """

    # Daily limits
    MAX_VISION_DAILY = 20
    MAX_TRANSCRIPT_DAILY = 10  # Increased since transcripts are cheap
    MAX_TEXT_DAILY = 150       # Increased - text is cheap

    # Estimated costs (USD) - Based on Claude Sonnet 4 pricing
    # Input: $3/1M tokens, Output: $15/1M tokens
    COST_PER_VISION = 0.035    # ~1,500 image tokens + analysis
    COST_PER_TRANSCRIPT = 0.02 # YouTube API is FREE, only text analysis cost
    COST_PER_TEXT = 0.025      # ~4,000 input + 800 output tokens

    def __init__(self):
        self.db = get_db()
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create api_usage table if it doesn't exist."""
        try:
            self.db.execute_query(
                "SELECT COUNT(*) FROM api_usage LIMIT 1",
                fetch="one"
            )
        except Exception:
            # Table doesn't exist, create it
            logger.info("Creating api_usage table...")
            migration_sql = """
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                vision_analyses INTEGER DEFAULT 0,
                transcript_analyses INTEGER DEFAULT 0,
                text_analyses INTEGER DEFAULT 0,
                estimated_cost_usd REAL DEFAULT 0.0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_api_usage_date ON api_usage(date DESC);
            """
            with self.db.get_connection() as conn:
                conn.executescript(migration_sql)
            logger.info("api_usage table created successfully")

    def get_today_usage(self) -> Dict[str, int]:
        """
        Get current usage for today.

        Returns:
            Dict with keys: vision_analyses, transcript_analyses, text_analyses, estimated_cost_usd
        """
        today = date.today().isoformat()

        row = self.db.execute_query(
            "SELECT * FROM api_usage WHERE date = ?",
            (today,),
            fetch="one"
        )

        if row:
            return {
                "vision_analyses": row["vision_analyses"],
                "transcript_analyses": row["transcript_analyses"],
                "text_analyses": row["text_analyses"],
                "estimated_cost_usd": row["estimated_cost_usd"]
            }
        else:
            return {
                "vision_analyses": 0,
                "transcript_analyses": 0,
                "text_analyses": 0,
                "estimated_cost_usd": 0.0
            }

    def can_use_vision(self, count: int = 1) -> Tuple[bool, str]:
        """
        Check if vision API can be used.

        Args:
            count: Number of vision calls requested

        Returns:
            (allowed, reason) tuple
        """
        usage = self.get_today_usage()
        current = usage["vision_analyses"]

        if current + count > self.MAX_VISION_DAILY:
            reason = f"Vision limit reached: {current}/{self.MAX_VISION_DAILY} used today. Skipping to prevent cost overrun."
            return False, reason

        return True, "OK"

    def can_use_transcript(self, count: int = 1) -> Tuple[bool, str]:
        """
        Check if transcript API can be used.

        Args:
            count: Number of transcript calls requested

        Returns:
            (allowed, reason) tuple
        """
        usage = self.get_today_usage()
        current = usage["transcript_analyses"]

        if current + count > self.MAX_TRANSCRIPT_DAILY:
            reason = f"Transcript limit reached: {current}/{self.MAX_TRANSCRIPT_DAILY} used today. Skipping to prevent cost overrun."
            return False, reason

        return True, "OK"

    def can_use_text(self, count: int = 1) -> Tuple[bool, str]:
        """
        Check if text API can be used.

        Args:
            count: Number of text calls requested

        Returns:
            (allowed, reason) tuple
        """
        usage = self.get_today_usage()
        current = usage["text_analyses"]

        if current + count > self.MAX_TEXT_DAILY:
            reason = f"Text analysis limit reached: {current}/{self.MAX_TEXT_DAILY} used today. Skipping to prevent cost overrun."
            return False, reason

        return True, "OK"

    def record_vision_use(self, count: int = 1, notes: Optional[str] = None):
        """Record vision API usage."""
        self._increment_usage("vision_analyses", count, self.COST_PER_VISION, notes)

    def record_transcript_use(self, count: int = 1, notes: Optional[str] = None):
        """Record transcript API usage."""
        self._increment_usage("transcript_analyses", count, self.COST_PER_TRANSCRIPT, notes)

    def record_text_use(self, count: int = 1, notes: Optional[str] = None):
        """Record text API usage."""
        self._increment_usage("text_analyses", count, self.COST_PER_TEXT, notes)

    def _increment_usage(self, field: str, count: int, cost_per_unit: float, notes: Optional[str] = None):
        """
        Increment usage counter for today.

        Args:
            field: 'vision_analyses', 'transcript_analyses', or 'text_analyses'
            count: Number to increment by
            cost_per_unit: Estimated cost per unit
            notes: Optional notes about this usage
        """
        today = date.today().isoformat()

        # Get or create today's record
        row = self.db.execute_query(
            "SELECT * FROM api_usage WHERE date = ?",
            (today,),
            fetch="one"
        )

        if row:
            # Update existing record
            new_count = row[field] + count
            new_cost = row["estimated_cost_usd"] + (count * cost_per_unit)

            update_data = {
                field: new_count,
                "estimated_cost_usd": new_cost,
                "updated_at": datetime.now().isoformat()
            }

            if notes:
                existing_notes = row["notes"] or ""
                update_data["notes"] = f"{existing_notes}\n{datetime.now().strftime('%H:%M:%S')}: {notes}"

            self.db.update("api_usage", row["id"], update_data)

            logger.info(f"API usage recorded: {field} +{count} (total: {new_count}, est. cost today: ${new_cost:.2f})")
        else:
            # Create new record for today
            insert_data = {
                "date": today,
                field: count,
                "estimated_cost_usd": count * cost_per_unit,
                "notes": notes if notes else None
            }

            self.db.insert("api_usage", insert_data)

            logger.info(f"API usage recorded: {field} +{count} (est. cost today: ${count * cost_per_unit:.2f})")

    def get_budget_status(self) -> Dict:
        """
        Get comprehensive budget status for today.

        Returns:
            Dict with usage stats, limits, and warnings
        """
        usage = self.get_today_usage()

        vision_pct = (usage["vision_analyses"] / self.MAX_VISION_DAILY) * 100
        transcript_pct = (usage["transcript_analyses"] / self.MAX_TRANSCRIPT_DAILY) * 100
        text_pct = (usage["text_analyses"] / self.MAX_TEXT_DAILY) * 100

        max_daily_budget = (
            self.MAX_VISION_DAILY * self.COST_PER_VISION +
            self.MAX_TRANSCRIPT_DAILY * self.COST_PER_TRANSCRIPT +
            self.MAX_TEXT_DAILY * self.COST_PER_TEXT
        )

        return {
            "date": date.today().isoformat(),
            "usage": usage,
            "limits": {
                "vision": self.MAX_VISION_DAILY,
                "transcript": self.MAX_TRANSCRIPT_DAILY,
                "text": self.MAX_TEXT_DAILY
            },
            "usage_percent": {
                "vision": round(vision_pct, 1),
                "transcript": round(transcript_pct, 1),
                "text": round(text_pct, 1)
            },
            "budget": {
                "spent_today": round(usage["estimated_cost_usd"], 2),
                "max_daily": round(max_daily_budget, 2),
                "max_monthly": round(max_daily_budget * 30, 2)
            },
            "warnings": self._get_warnings(usage)
        }

    def _get_warnings(self, usage: Dict) -> list:
        """Generate warning messages based on usage."""
        warnings = []

        vision_pct = (usage["vision_analyses"] / self.MAX_VISION_DAILY) * 100
        transcript_pct = (usage["transcript_analyses"] / self.MAX_TRANSCRIPT_DAILY) * 100
        text_pct = (usage["text_analyses"] / self.MAX_TEXT_DAILY) * 100

        if vision_pct >= 90:
            warnings.append(f"⚠️ Vision API at {vision_pct:.0f}% of daily limit")
        if transcript_pct >= 90:
            warnings.append(f"⚠️ Transcript API at {transcript_pct:.0f}% of daily limit")
        if text_pct >= 90:
            warnings.append(f"⚠️ Text API at {text_pct:.0f}% of daily limit")

        return warnings


# Singleton instance
_limiter_instance = None


def get_usage_limiter() -> UsageLimiter:
    """
    Get usage limiter singleton instance.

    Returns:
        UsageLimiter instance

    Example:
        from backend.utils.usage_limiter import get_usage_limiter

        limiter = get_usage_limiter()
        can_use, reason = limiter.can_use_vision(count=15)
        if can_use:
            # Perform vision analysis
            limiter.record_vision_use(count=15, notes="42Macro PDF analysis")
    """
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = UsageLimiter()
    return _limiter_instance
