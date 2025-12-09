"""
Theme Tracking Routes (PRD-024)

API endpoints for managing and querying investment themes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import json

from backend.models import get_db, Theme

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/themes", tags=["themes"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ThemeListItem(BaseModel):
    """Summary of a theme for list views."""
    id: int
    name: str
    aliases: List[str] = []
    status: str
    first_mentioned_at: Optional[str]
    first_source: Optional[str]
    source_count: int = 0
    evidence_count: int = 0
    last_updated_at: Optional[str]
    catalysts: List[Dict] = []


class SourceEvidence(BaseModel):
    """Evidence from a single source."""
    date: str
    summary: str
    raw_content_id: Optional[int] = None
    strength: str = "moderate"  # "strong", "moderate", "weak"


class ThemeDetail(BaseModel):
    """Full theme detail with all evidence."""
    id: int
    name: str
    aliases: List[str] = []
    status: str
    description: Optional[str]
    first_mentioned_at: Optional[str]
    first_source: Optional[str]
    evolved_from: Optional[Dict] = None
    evolved_into: List[Dict] = []
    source_evidence: Dict[str, List[Dict]] = {}
    catalysts: List[Dict] = []
    last_updated_at: Optional[str]
    created_at: str


class ThemeMergeRequest(BaseModel):
    """Request to merge two themes."""
    theme_id_to_merge: int


class ThemeStatusUpdate(BaseModel):
    """Request to update theme status."""
    status: str
    reason: Optional[str] = None


class ThemeCreate(BaseModel):
    """Request to create a new theme."""
    name: str
    description: Optional[str] = None
    aliases: List[str] = []
    first_source: Optional[str] = None
    source_evidence: Dict[str, List[Dict]] = {}
    catalysts: List[Dict] = []


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("")
async def list_themes(
    status: Optional[str] = Query(None, description="Filter by status: emerging, active, evolved, dormant"),
    source: Optional[str] = Query(None, description="Filter by source discussing the theme"),
    since: Optional[str] = Query(None, description="Filter by first_mentioned_at >= this date"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all themes with optional filters.

    Returns summary information suitable for list views.
    """
    try:
        query = db.query(Theme)

        # Apply filters
        if status:
            query = query.filter(Theme.status == status)

        if since:
            try:
                since_date = datetime.fromisoformat(since)
                query = query.filter(Theme.first_mentioned_at >= since_date)
            except ValueError:
                pass  # Ignore invalid date format

        # Order by last_updated_at descending
        query = query.order_by(desc(Theme.last_updated_at), desc(Theme.created_at))

        # Apply limit
        themes = query.limit(limit).all()

        # Filter by source if specified (requires parsing source_evidence JSON)
        if source:
            filtered_themes = []
            for theme in themes:
                if theme.source_evidence:
                    try:
                        evidence = json.loads(theme.source_evidence)
                        if source in evidence:
                            filtered_themes.append(theme)
                    except json.JSONDecodeError:
                        pass
            themes = filtered_themes

        # Build response
        theme_list = []
        for theme in themes:
            # Parse JSON fields
            aliases = []
            if theme.aliases:
                try:
                    aliases = json.loads(theme.aliases)
                except json.JSONDecodeError:
                    pass

            source_evidence = {}
            source_count = 0
            evidence_count = 0
            if theme.source_evidence:
                try:
                    source_evidence = json.loads(theme.source_evidence)
                    source_count = len(source_evidence)
                    evidence_count = sum(len(v) for v in source_evidence.values())
                except json.JSONDecodeError:
                    pass

            catalysts = []
            if theme.catalysts:
                try:
                    catalysts = json.loads(theme.catalysts)
                except json.JSONDecodeError:
                    pass

            theme_list.append({
                "id": theme.id,
                "name": theme.name,
                "aliases": aliases,
                "status": theme.status,
                "first_mentioned_at": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
                "first_source": theme.first_source,
                "source_count": source_count,
                "evidence_count": evidence_count,
                "last_updated_at": theme.last_updated_at.isoformat() if theme.last_updated_at else None,
                "catalysts": catalysts
            })

        return {
            "themes": theme_list,
            "count": len(theme_list)
        }

    except Exception as e:
        logger.error(f"Error listing themes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{theme_id}")
async def get_theme(theme_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get full theme detail with all evidence.
    """
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()

        if not theme:
            raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")

        # Parse JSON fields
        aliases = []
        if theme.aliases:
            try:
                aliases = json.loads(theme.aliases)
            except json.JSONDecodeError:
                pass

        source_evidence = {}
        if theme.source_evidence:
            try:
                source_evidence = json.loads(theme.source_evidence)
            except json.JSONDecodeError:
                pass

        catalysts = []
        if theme.catalysts:
            try:
                catalysts = json.loads(theme.catalysts)
            except json.JSONDecodeError:
                pass

        # Get evolved_from theme if exists
        evolved_from = None
        if theme.evolved_from_theme_id:
            parent = db.query(Theme).filter(Theme.id == theme.evolved_from_theme_id).first()
            if parent:
                evolved_from = {"id": parent.id, "name": parent.name}

        # Get themes this evolved into
        evolved_into = []
        children = db.query(Theme).filter(Theme.evolved_from_theme_id == theme.id).all()
        for child in children:
            evolved_into.append({"id": child.id, "name": child.name})

        return {
            "id": theme.id,
            "name": theme.name,
            "aliases": aliases,
            "status": theme.status,
            "description": theme.description,
            "first_mentioned_at": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
            "first_source": theme.first_source,
            "evolved_from": evolved_from,
            "evolved_into": evolved_into,
            "source_evidence": source_evidence,
            "catalysts": catalysts,
            "last_updated_at": theme.last_updated_at.isoformat() if theme.last_updated_at else None,
            "created_at": theme.created_at.isoformat() if theme.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theme {theme_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_theme(request: ThemeCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Create a new theme.
    """
    try:
        # Check if theme with same name exists
        existing = db.query(Theme).filter(Theme.name == request.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Theme with name '{request.name}' already exists")

        now = datetime.utcnow()

        theme = Theme(
            name=request.name,
            description=request.description,
            aliases=json.dumps(request.aliases) if request.aliases else None,
            first_source=request.first_source,
            source_evidence=json.dumps(request.source_evidence) if request.source_evidence else None,
            catalysts=json.dumps(request.catalysts) if request.catalysts else None,
            status="emerging",
            first_mentioned_at=now,
            last_updated_at=now,
            current_conviction=0.5,  # Legacy field
            evidence_count=sum(len(v) for v in request.source_evidence.values()) if request.source_evidence else 0
        )

        db.add(theme)
        db.commit()
        db.refresh(theme)

        logger.info(f"Created theme: {theme.name} (id={theme.id})")

        return {
            "status": "success",
            "theme_id": theme.id,
            "name": theme.name
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating theme: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{theme_id}/merge")
async def merge_themes(
    theme_id: int,
    request: ThemeMergeRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Merge another theme into this one.

    The theme_id_to_merge will have its evidence moved to theme_id,
    and its name added as an alias.
    """
    try:
        # Get both themes
        primary = db.query(Theme).filter(Theme.id == theme_id).first()
        secondary = db.query(Theme).filter(Theme.id == request.theme_id_to_merge).first()

        if not primary:
            raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")
        if not secondary:
            raise HTTPException(status_code=404, detail=f"Theme {request.theme_id_to_merge} not found")
        if theme_id == request.theme_id_to_merge:
            raise HTTPException(status_code=400, detail="Cannot merge theme with itself")

        # Parse existing data
        primary_aliases = json.loads(primary.aliases) if primary.aliases else []
        primary_evidence = json.loads(primary.source_evidence) if primary.source_evidence else {}
        primary_catalysts = json.loads(primary.catalysts) if primary.catalysts else []

        secondary_aliases = json.loads(secondary.aliases) if secondary.aliases else []
        secondary_evidence = json.loads(secondary.source_evidence) if secondary.source_evidence else {}
        secondary_catalysts = json.loads(secondary.catalysts) if secondary.catalysts else []

        # Add secondary name and aliases to primary aliases
        if secondary.name not in primary_aliases:
            primary_aliases.append(secondary.name)
        for alias in secondary_aliases:
            if alias not in primary_aliases:
                primary_aliases.append(alias)

        # Merge evidence
        for source, evidence_list in secondary_evidence.items():
            if source not in primary_evidence:
                primary_evidence[source] = []
            primary_evidence[source].extend(evidence_list)

        # Merge catalysts (deduplicate by date+event)
        existing_catalyst_keys = {(c.get("date"), c.get("event")) for c in primary_catalysts}
        for catalyst in secondary_catalysts:
            key = (catalyst.get("date"), catalyst.get("event"))
            if key not in existing_catalyst_keys:
                primary_catalysts.append(catalyst)

        # Update primary theme
        primary.aliases = json.dumps(primary_aliases)
        primary.source_evidence = json.dumps(primary_evidence)
        primary.catalysts = json.dumps(primary_catalysts)
        primary.evidence_count = sum(len(v) for v in primary_evidence.values())
        primary.last_updated_at = datetime.utcnow()

        # Update primary status if it was emerging and now has more sources
        if primary.status == "emerging" and len(primary_evidence) >= 2:
            primary.status = "active"

        # Delete secondary theme
        db.delete(secondary)
        db.commit()

        logger.info(f"Merged theme {secondary.name} (id={request.theme_id_to_merge}) into {primary.name} (id={theme_id})")

        return {
            "status": "success",
            "message": f"Merged '{secondary.name}' into '{primary.name}'",
            "primary_theme_id": theme_id,
            "aliases_added": [secondary.name] + secondary_aliases,
            "evidence_merged": sum(len(v) for v in secondary_evidence.values())
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error merging themes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{theme_id}/status")
async def update_theme_status(
    theme_id: int,
    request: ThemeStatusUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update theme lifecycle status.
    """
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()

        if not theme:
            raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")

        valid_statuses = ["emerging", "active", "evolved", "dormant"]
        if request.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        old_status = theme.status
        theme.status = request.status
        theme.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Updated theme {theme.name} status: {old_status} -> {request.status}")

        return {
            "status": "success",
            "theme_id": theme_id,
            "old_status": old_status,
            "new_status": request.status
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating theme status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{theme_id}/evidence")
async def add_evidence(
    theme_id: int,
    source: str,
    summary: str,
    strength: str = "moderate",
    raw_content_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Add evidence to a theme from a specific source.
    """
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()

        if not theme:
            raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")

        # Parse existing evidence
        evidence = json.loads(theme.source_evidence) if theme.source_evidence else {}

        # Add new evidence
        if source not in evidence:
            evidence[source] = []

        now = datetime.utcnow()
        new_evidence = {
            "date": now.strftime("%Y-%m-%d"),
            "summary": summary,
            "strength": strength
        }
        if raw_content_id:
            new_evidence["raw_content_id"] = raw_content_id

        evidence[source].append(new_evidence)

        # Update theme
        theme.source_evidence = json.dumps(evidence)
        theme.last_updated_at = now
        theme.evidence_count = sum(len(v) for v in evidence.values())

        # Update status if emerging and now has multiple sources
        if theme.status == "emerging" and len(evidence) >= 2:
            theme.status = "active"

        db.commit()

        logger.info(f"Added evidence to theme {theme.name} from {source}")

        return {
            "status": "success",
            "theme_id": theme_id,
            "source": source,
            "total_evidence": theme.evidence_count
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding evidence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate")
async def migrate_themes_schema(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Migrate themes table to add missing columns (PRD-024).
    Adds aliases, source_evidence, catalysts, first_source columns if missing.
    """
    from sqlalchemy import text

    migrations = []

    # Columns to check and add
    columns_to_add = [
        ("aliases", "TEXT"),
        ("source_evidence", "TEXT"),
        ("catalysts", "TEXT"),
        ("first_source", "VARCHAR"),
        ("evolved_from_theme_id", "INTEGER"),
        ("last_updated_at", "DATETIME"),
    ]

    for col_name, col_type in columns_to_add:
        try:
            db.execute(text(f"SELECT {col_name} FROM themes LIMIT 1"))
            migrations.append({"column": col_name, "status": "exists"})
        except Exception:
            try:
                db.execute(text(f"ALTER TABLE themes ADD COLUMN {col_name} {col_type}"))
                db.commit()
                migrations.append({"column": col_name, "status": "added"})
                logger.info(f"Added column {col_name} to themes table")
            except Exception as e:
                migrations.append({"column": col_name, "status": "error", "error": str(e)})

    return {
        "status": "success",
        "migrations": migrations
    }


@router.get("/summary")
async def get_theme_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get summary statistics about themes.
    """
    try:
        themes = db.query(Theme).all()

        by_status = {"emerging": 0, "active": 0, "evolved": 0, "dormant": 0}
        for theme in themes:
            if theme.status in by_status:
                by_status[theme.status] += 1

        # Get active themes with their evidence counts
        active_themes = []
        for theme in themes:
            if theme.status in ["emerging", "active"]:
                source_evidence = {}
                if theme.source_evidence:
                    try:
                        source_evidence = json.loads(theme.source_evidence)
                    except json.JSONDecodeError:
                        pass

                catalysts = []
                if theme.catalysts:
                    try:
                        catalysts = json.loads(theme.catalysts)
                    except json.JSONDecodeError:
                        pass

                # Find next catalyst
                next_catalyst = None
                today = datetime.utcnow().date()
                for c in catalysts:
                    try:
                        c_date = datetime.strptime(c.get("date", ""), "%Y-%m-%d").date()
                        if c_date >= today:
                            if next_catalyst is None or c_date < datetime.strptime(next_catalyst, "%Y-%m-%d").date():
                                next_catalyst = c.get("date")
                    except ValueError:
                        pass

                active_themes.append({
                    "id": theme.id,
                    "name": theme.name,
                    "status": theme.status,
                    "sources": list(source_evidence.keys()),
                    "evidence_count": sum(len(v) for v in source_evidence.values()),
                    "next_catalyst": next_catalyst
                })

        return {
            "total_themes": len(themes),
            "by_status": by_status,
            "active_themes": sorted(active_themes, key=lambda x: x["evidence_count"], reverse=True)
        }

    except Exception as e:
        logger.error(f"Error getting theme summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
