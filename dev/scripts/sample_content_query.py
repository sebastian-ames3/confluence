#!/usr/bin/env python
"""
Pull sample content from database for schema design analysis.

Usage:
    # Local SQLite (default)
    python dev/scripts/sample_content_query.py

    # Railway PostgreSQL - set DATABASE_URL first
    export DATABASE_URL="postgresql://user:pass@host:port/db"
    python dev/scripts/sample_content_query.py

    # Export to file
    python dev/scripts/sample_content_query.py --output sample_export.txt

    # Limit samples
    python dev/scripts/sample_content_query.py --limit 3
"""
import sys
import os
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    parser = argparse.ArgumentParser(description='Export sample content from database')
    parser.add_argument('--limit', type=int, default=3, help='Number of items per content type (default: 3)')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    parser.add_argument('--full-transcript', action='store_true', help='Show full transcripts (default: truncate to 3000 chars)')
    args = parser.parse_args()

    # Import after path setup
    from backend.models import SessionLocal, RawContent, AnalyzedContent, Source

    db = SessionLocal()

    # Check which database we're connected to
    db_url = os.getenv("DATABASE_URL", "sqlite:///database/confluence.db")
    if "postgresql" in db_url:
        db_type = "PostgreSQL (Railway)"
        # Mask the password in output
        masked_url = db_url.split("@")[1] if "@" in db_url else "connected"
    else:
        db_type = "SQLite (local)"
        masked_url = db_url

    # Output handling
    output_file = None
    if args.output:
        output_file = open(args.output, 'w', encoding='utf-8')

    def log(msg=""):
        print(msg)
        if output_file:
            output_file.write(msg + "\n")

    max_chars = 100000 if args.full_transcript else 3000

    log("=" * 80)
    log(f"SAMPLE CONTENT EXPORT")
    log(f"Database: {db_type}")
    log(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    log(f"Limit per type: {args.limit}")
    log("=" * 80)

    # =========================================================================
    # 42MACRO CONTENT
    # =========================================================================
    log("\n" + "=" * 80)
    log("42MACRO CONTENT SAMPLES")
    log("=" * 80)

    macro42 = db.query(Source).filter(Source.name == "42macro").first()
    if macro42:
        # Get videos with transcripts (most valuable for macro analysis)
        videos = db.query(RawContent).filter(
            RawContent.source_id == macro42.id,
            RawContent.content_type == "video",
            RawContent.content_text.isnot(None),
            RawContent.content_text != ""
        ).order_by(RawContent.collected_at.desc()).limit(args.limit).all()

        log(f"\n--- 42MACRO Video Transcripts ({len(videos)} samples) ---")
        for i, item in enumerate(videos, 1):
            log(f"\n{'='*60}")
            log(f"[42MACRO VIDEO #{i}] ID: {item.id}")
            log(f"Collected: {item.collected_at}")
            log(f"URL: {item.url}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    log(f"Title: {meta.get('title', 'unknown')}")
                    log(f"Report Type: {meta.get('report_type', 'unknown')}")
                except:
                    pass
            log(f"\n--- TRANSCRIPT START ---")
            if item.content_text:
                text = item.content_text[:max_chars]
                log(text)
                if len(item.content_text) > max_chars:
                    log(f"\n... [TRUNCATED - {len(item.content_text)} total chars] ...")
            else:
                log("(No transcript)")
            log("--- TRANSCRIPT END ---")

            # Get analysis if exists
            analysis = db.query(AnalyzedContent).filter(
                AnalyzedContent.raw_content_id == item.id
            ).first()
            if analysis:
                log(f"\n--- CURRENT ANALYSIS OUTPUT ---")
                log(f"Agent: {analysis.agent_type}")
                log(f"Sentiment: {analysis.sentiment}")
                log(f"Themes: {analysis.key_themes}")
                if analysis.analysis_result:
                    try:
                        result = json.loads(analysis.analysis_result)
                        log(f"Analysis Result:\n{json.dumps(result, indent=2)[:2000]}")
                    except:
                        log(f"Analysis Result (raw):\n{analysis.analysis_result[:2000]}")

        # Get PDFs
        pdfs = db.query(RawContent).filter(
            RawContent.source_id == macro42.id,
            RawContent.content_type == "pdf",
            RawContent.content_text.isnot(None),
            RawContent.content_text != ""
        ).order_by(RawContent.collected_at.desc()).limit(args.limit).all()

        log(f"\n--- 42MACRO PDF Text ({len(pdfs)} samples) ---")
        for i, item in enumerate(pdfs, 1):
            log(f"\n{'='*60}")
            log(f"[42MACRO PDF #{i}] ID: {item.id}")
            log(f"Collected: {item.collected_at}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    log(f"Title: {meta.get('title', 'unknown')}")
                    log(f"Report Type: {meta.get('report_type', 'unknown')}")
                except:
                    pass
            log(f"\n--- PDF TEXT START ---")
            if item.content_text:
                text = item.content_text[:max_chars]
                log(text)
                if len(item.content_text) > max_chars:
                    log(f"\n... [TRUNCATED - {len(item.content_text)} total chars] ...")
            log("--- PDF TEXT END ---")
    else:
        log("42macro source not found in database")

    # =========================================================================
    # DISCORD CONTENT
    # =========================================================================
    log("\n" + "=" * 80)
    log("DISCORD CONTENT SAMPLES")
    log("=" * 80)

    discord = db.query(Source).filter(Source.name == "discord").first()
    if discord:
        # Get videos with transcripts (Zoom recordings - most valuable)
        discord_videos = db.query(RawContent).filter(
            RawContent.source_id == discord.id,
            RawContent.content_type == "video",
            RawContent.content_text.isnot(None),
            RawContent.content_text != ""
        ).order_by(RawContent.collected_at.desc()).limit(args.limit).all()

        log(f"\n--- DISCORD Video Transcripts ({len(discord_videos)} samples) ---")
        for i, item in enumerate(discord_videos, 1):
            log(f"\n{'='*60}")
            log(f"[DISCORD VIDEO #{i}] ID: {item.id}")
            log(f"Collected: {item.collected_at}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    log(f"Channel: {meta.get('channel_name', 'unknown')}")
                    log(f"Platform: {meta.get('platform', 'unknown')}")
                except:
                    pass
            log(f"\n--- TRANSCRIPT START ---")
            if item.content_text:
                text = item.content_text[:max_chars]
                log(text)
                if len(item.content_text) > max_chars:
                    log(f"\n... [TRUNCATED - {len(item.content_text)} total chars] ...")
            log("--- TRANSCRIPT END ---")

        # Get text messages from high-priority channels
        messages = db.query(RawContent).filter(
            RawContent.source_id == discord.id,
            RawContent.content_type.in_(["discord_message", "text"]),
            RawContent.content_text.isnot(None),
            RawContent.content_text != ""
        ).order_by(RawContent.collected_at.desc()).limit(args.limit * 3).all()  # Get more messages

        log(f"\n--- DISCORD Messages ({len(messages)} samples) ---")
        for i, item in enumerate(messages, 1):
            log(f"\n{'='*60}")
            log(f"[DISCORD MSG #{i}] ID: {item.id}")
            log(f"Collected: {item.collected_at}")
            channel = "unknown"
            author = "unknown"
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    channel = meta.get('channel_name', 'unknown')
                    author = meta.get('author', 'unknown')
                    log(f"Channel: {channel}")
                    log(f"Author: {author}")
                    log(f"Priority: {meta.get('priority', 'unknown')}")
                    if meta.get('video_transcripts'):
                        log(f"Embedded video transcripts: {len(meta['video_transcripts'])}")
                        for j, vt in enumerate(meta['video_transcripts'][:2]):
                            log(f"\n  --- Embedded Transcript #{j+1} ---")
                            transcript = vt.get('transcript', '')[:2000]
                            log(f"  {transcript}")
                except:
                    pass
            log(f"\n--- MESSAGE CONTENT ---")
            if item.content_text:
                log(item.content_text[:2000])
            log("--- END MESSAGE ---")

            # Get analysis if exists
            analysis = db.query(AnalyzedContent).filter(
                AnalyzedContent.raw_content_id == item.id
            ).first()
            if analysis:
                log(f"\n--- CURRENT ANALYSIS OUTPUT ---")
                log(f"Agent: {analysis.agent_type}")
                log(f"Sentiment: {analysis.sentiment}")
                log(f"Themes: {analysis.key_themes}")
                if analysis.analysis_result:
                    log(f"Analysis Result:\n{analysis.analysis_result[:1500]}")
    else:
        log("Discord source not found in database")

    # =========================================================================
    # CONTENT TYPE SUMMARY
    # =========================================================================
    log("\n" + "=" * 80)
    log("DATABASE SUMMARY")
    log("=" * 80)

    sources = db.query(Source).all()
    for source in sources:
        total = db.query(RawContent).filter(RawContent.source_id == source.id).count()
        with_text = db.query(RawContent).filter(
            RawContent.source_id == source.id,
            RawContent.content_text.isnot(None),
            RawContent.content_text != ""
        ).count()
        types = db.query(RawContent.content_type).filter(
            RawContent.source_id == source.id
        ).distinct().all()
        type_list = [t[0] for t in types]
        log(f"\n{source.name}:")
        log(f"  Total items: {total}")
        log(f"  With text content: {with_text}")
        log(f"  Content types: {type_list}")

    analyzed_count = db.query(AnalyzedContent).count()
    log(f"\nTotal analyzed content records: {analyzed_count}")

    db.close()

    if output_file:
        output_file.close()
        log(f"\nOutput saved to: {args.output}")


if __name__ == "__main__":
    main()
