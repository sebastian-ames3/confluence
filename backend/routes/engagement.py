"""
Engagement Routes (PRD-038)

API endpoints for user feedback on synthesis and themes.
Uses async patterns per PRD-035.

Security:
- All endpoints require JWT or Basic Auth
- Rate limited to prevent abuse
- Comments sanitized per PRD-037
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import logging

from backend.models import (
    get_async_db,
    SynthesisFeedback,
    ThemeFeedback,
    Synthesis,
    Theme
)
from backend.utils.auth import verify_jwt_or_basic
from backend.utils.rate_limiter import limiter, RATE_LIMITS
from backend.utils.sanitization import sanitize_content_text

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class SimpleFeedbackRequest(BaseModel):
    """Simple thumbs up/down feedback."""
    is_positive: bool  # True = thumbs up, False = thumbs down


class DetailedSynthesisFeedbackRequest(BaseModel):
    """Detailed synthesis feedback from modal."""
    accuracy_rating: int = Field(..., ge=1, le=5)
    usefulness_rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class DetailedThemeFeedbackRequest(BaseModel):
    """Detailed theme feedback from modal."""
    quality_rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


# ============================================================================
# Synthesis Feedback Endpoints
# ============================================================================

@router.post("/engagement/synthesis/{synthesis_id}/simple")
@limiter.limit(RATE_LIMITS["default"])
async def submit_simple_synthesis_feedback(
    request: Request,
    synthesis_id: int,
    feedback: SimpleFeedbackRequest,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Submit simple thumbs up/down feedback for a synthesis.
    Updates existing feedback if user already submitted for this synthesis.
    """
    # Verify synthesis exists
    result = await db.execute(
        select(Synthesis).where(Synthesis.id == synthesis_id)
    )
    synthesis = result.scalar_one_or_none()
    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")

    # Check for existing feedback from this user
    result = await db.execute(
        select(SynthesisFeedback).where(
            and_(
                SynthesisFeedback.synthesis_id == synthesis_id,
                SynthesisFeedback.user == user
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.is_helpful = feedback.is_positive
        existing.updated_at = datetime.utcnow()
        feedback_id = existing.id
        message = "Feedback updated"
    else:
        # Create new
        new_feedback = SynthesisFeedback(
            synthesis_id=synthesis_id,
            is_helpful=feedback.is_positive,
            user=user
        )
        db.add(new_feedback)
        await db.flush()
        feedback_id = new_feedback.id
        message = "Feedback submitted"

    await db.commit()

    logger.info(f"User {user} submitted simple feedback for synthesis {synthesis_id}: {feedback.is_positive}")

    return {
        "status": "success",
        "message": message,
        "feedback_id": feedback_id
    }


@router.post("/engagement/synthesis/{synthesis_id}/detailed")
@limiter.limit(RATE_LIMITS["default"])
async def submit_detailed_synthesis_feedback(
    request: Request,
    synthesis_id: int,
    feedback: DetailedSynthesisFeedbackRequest,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Submit detailed feedback for a synthesis via modal.
    Updates existing feedback if user already submitted.
    """
    # Verify synthesis exists
    result = await db.execute(
        select(Synthesis).where(Synthesis.id == synthesis_id)
    )
    synthesis = result.scalar_one_or_none()
    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")

    # Sanitize comment (PRD-037)
    sanitized_comment = None
    if feedback.comment:
        sanitized_comment = sanitize_content_text(feedback.comment, max_length=2000)

    # Check for existing feedback
    result = await db.execute(
        select(SynthesisFeedback).where(
            and_(
                SynthesisFeedback.synthesis_id == synthesis_id,
                SynthesisFeedback.user == user
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.accuracy_rating = feedback.accuracy_rating
        existing.usefulness_rating = feedback.usefulness_rating
        existing.comment = sanitized_comment
        existing.updated_at = datetime.utcnow()
        feedback_id = existing.id
        message = "Detailed feedback updated"
    else:
        new_feedback = SynthesisFeedback(
            synthesis_id=synthesis_id,
            accuracy_rating=feedback.accuracy_rating,
            usefulness_rating=feedback.usefulness_rating,
            comment=sanitized_comment,
            user=user
        )
        db.add(new_feedback)
        await db.flush()
        feedback_id = new_feedback.id
        message = "Detailed feedback submitted"

    await db.commit()

    logger.info(f"User {user} submitted detailed feedback for synthesis {synthesis_id}")

    return {
        "status": "success",
        "message": message,
        "feedback_id": feedback_id
    }


@router.get("/engagement/synthesis/{synthesis_id}/my-feedback")
@limiter.limit(RATE_LIMITS["default"])
async def get_my_synthesis_feedback(
    request: Request,
    synthesis_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get current user's feedback for a synthesis."""
    result = await db.execute(
        select(SynthesisFeedback).where(
            and_(
                SynthesisFeedback.synthesis_id == synthesis_id,
                SynthesisFeedback.user == user
            )
        )
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        return {"status": "not_found", "feedback": None}

    return {
        "status": "found",
        "feedback": {
            "id": feedback.id,
            "is_helpful": feedback.is_helpful,
            "accuracy_rating": feedback.accuracy_rating,
            "usefulness_rating": feedback.usefulness_rating,
            "comment": feedback.comment,
            "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None
        }
    }


# ============================================================================
# Theme Feedback Endpoints
# ============================================================================

@router.post("/engagement/theme/{theme_id}/simple")
@limiter.limit(RATE_LIMITS["default"])
async def submit_simple_theme_feedback(
    request: Request,
    theme_id: int,
    feedback: SimpleFeedbackRequest,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Submit simple relevance feedback for a theme.
    Updates existing feedback if user already submitted.
    """
    # Verify theme exists
    result = await db.execute(
        select(Theme).where(Theme.id == theme_id)
    )
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Check for existing feedback
    result = await db.execute(
        select(ThemeFeedback).where(
            and_(
                ThemeFeedback.theme_id == theme_id,
                ThemeFeedback.user == user
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.is_relevant = feedback.is_positive
        existing.updated_at = datetime.utcnow()
        feedback_id = existing.id
        message = "Feedback updated"
    else:
        new_feedback = ThemeFeedback(
            theme_id=theme_id,
            is_relevant=feedback.is_positive,
            user=user
        )
        db.add(new_feedback)
        await db.flush()
        feedback_id = new_feedback.id
        message = "Feedback submitted"

    await db.commit()

    logger.info(f"User {user} submitted simple feedback for theme {theme_id}: {feedback.is_positive}")

    return {
        "status": "success",
        "message": message,
        "feedback_id": feedback_id
    }


@router.post("/engagement/theme/{theme_id}/detailed")
@limiter.limit(RATE_LIMITS["default"])
async def submit_detailed_theme_feedback(
    request: Request,
    theme_id: int,
    feedback: DetailedThemeFeedbackRequest,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Submit detailed quality feedback for a theme.
    Updates existing feedback if user already submitted.
    """
    # Verify theme exists
    result = await db.execute(
        select(Theme).where(Theme.id == theme_id)
    )
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Sanitize comment (PRD-037)
    sanitized_comment = None
    if feedback.comment:
        sanitized_comment = sanitize_content_text(feedback.comment, max_length=2000)

    # Check for existing feedback
    result = await db.execute(
        select(ThemeFeedback).where(
            and_(
                ThemeFeedback.theme_id == theme_id,
                ThemeFeedback.user == user
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.quality_rating = feedback.quality_rating
        existing.comment = sanitized_comment
        existing.updated_at = datetime.utcnow()
        feedback_id = existing.id
        message = "Detailed feedback updated"
    else:
        new_feedback = ThemeFeedback(
            theme_id=theme_id,
            quality_rating=feedback.quality_rating,
            comment=sanitized_comment,
            user=user
        )
        db.add(new_feedback)
        await db.flush()
        feedback_id = new_feedback.id
        message = "Detailed feedback submitted"

    await db.commit()

    logger.info(f"User {user} submitted detailed feedback for theme {theme_id}")

    return {
        "status": "success",
        "message": message,
        "feedback_id": feedback_id
    }


@router.get("/engagement/theme/{theme_id}/my-feedback")
@limiter.limit(RATE_LIMITS["default"])
async def get_my_theme_feedback(
    request: Request,
    theme_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get current user's feedback for a theme."""
    result = await db.execute(
        select(ThemeFeedback).where(
            and_(
                ThemeFeedback.theme_id == theme_id,
                ThemeFeedback.user == user
            )
        )
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        return {"status": "not_found", "feedback": None}

    return {
        "status": "found",
        "feedback": {
            "id": feedback.id,
            "is_relevant": feedback.is_relevant,
            "quality_rating": feedback.quality_rating,
            "comment": feedback.comment,
            "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None
        }
    }
