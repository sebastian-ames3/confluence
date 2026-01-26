#!/usr/bin/env python
"""
Pull sample content from database for schema design analysis.
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models import SessionLocal, RawContent, AnalyzedContent, Source
from datetime import datetime, timedelta

def main():
    db = SessionLocal()

    print("=" * 80)
    print("SAMPLE CONTENT FOR SCHEMA DESIGN")
    print("=" * 80)

    # =========================================================================
    # 42MACRO CONTENT
    # =========================================================================
    print("\n" + "=" * 80)
    print("42MACRO CONTENT SAMPLES")
    print("=" * 80)

    macro42 = db.query(Source).filter(Source.name == "42macro").first()
    if macro42:
        # Get PDFs (research reports)
        pdfs = db.query(RawContent).filter(
            RawContent.source_id == macro42.id,
            RawContent.content_type == "pdf"
        ).order_by(RawContent.collected_at.desc()).limit(3).all()

        print(f"\n--- 42MACRO PDFs ({len(pdfs)} samples) ---")
        for i, item in enumerate(pdfs, 1):
            print(f"\n[PDF #{i}] ID: {item.id}")
            print(f"Collected: {item.collected_at}")
            print(f"URL: {item.url}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    print(f"Metadata: {json.dumps(meta, indent=2)[:500]}")
                except:
                    print(f"Metadata (raw): {item.json_metadata[:300]}")
            print(f"\nContent Text (first 2000 chars):")
            print("-" * 40)
            if item.content_text:
                print(item.content_text[:2000])
            else:
                print("(No text content)")
            print("-" * 40)

            # Get analysis if exists
            analysis = db.query(AnalyzedContent).filter(
                AnalyzedContent.raw_content_id == item.id
            ).first()
            if analysis:
                print(f"\nAnalysis Result:")
                print(f"  Agent: {analysis.agent_type}")
                print(f"  Sentiment: {analysis.sentiment}")
                print(f"  Themes: {analysis.key_themes}")
                print(f"  Full Analysis (first 1000 chars):")
                if analysis.analysis_result:
                    print(analysis.analysis_result[:1000])

        # Get videos (Macro Minute, etc.)
        videos = db.query(RawContent).filter(
            RawContent.source_id == macro42.id,
            RawContent.content_type == "video"
        ).order_by(RawContent.collected_at.desc()).limit(2).all()

        print(f"\n--- 42MACRO Videos ({len(videos)} samples) ---")
        for i, item in enumerate(videos, 1):
            print(f"\n[VIDEO #{i}] ID: {item.id}")
            print(f"Collected: {item.collected_at}")
            print(f"URL: {item.url}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    print(f"Metadata: {json.dumps(meta, indent=2)[:500]}")
                except:
                    pass
            print(f"\nTranscript (first 2000 chars):")
            print("-" * 40)
            if item.content_text:
                print(item.content_text[:2000])
            else:
                print("(No transcript)")
            print("-" * 40)
    else:
        print("42macro source not found")

    # =========================================================================
    # DISCORD CONTENT
    # =========================================================================
    print("\n" + "=" * 80)
    print("DISCORD CONTENT SAMPLES")
    print("=" * 80)

    discord = db.query(Source).filter(Source.name == "discord").first()
    if discord:
        # Get text messages
        messages = db.query(RawContent).filter(
            RawContent.source_id == discord.id,
            RawContent.content_type.in_(["discord_message", "text"])
        ).order_by(RawContent.collected_at.desc()).limit(10).all()

        print(f"\n--- DISCORD Messages ({len(messages)} samples) ---")
        for i, item in enumerate(messages, 1):
            print(f"\n[MSG #{i}] ID: {item.id}")
            print(f"Collected: {item.collected_at}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    print(f"Channel: {meta.get('channel_name', 'unknown')}")
                    print(f"Author: {meta.get('author', 'unknown')}")
                    print(f"Priority: {meta.get('priority', 'unknown')}")
                    if meta.get('video_transcripts'):
                        print(f"Has video transcripts: {len(meta['video_transcripts'])}")
                except:
                    pass
            print(f"\nContent (first 1500 chars):")
            print("-" * 40)
            if item.content_text:
                print(item.content_text[:1500])
            else:
                print("(No text content)")
            print("-" * 40)

            # Get analysis if exists
            analysis = db.query(AnalyzedContent).filter(
                AnalyzedContent.raw_content_id == item.id
            ).first()
            if analysis:
                print(f"\nAnalysis:")
                print(f"  Agent: {analysis.agent_type}")
                print(f"  Sentiment: {analysis.sentiment}")
                print(f"  Themes: {analysis.key_themes}")
                if analysis.analysis_result:
                    print(f"  Full Analysis (first 800 chars):")
                    print(analysis.analysis_result[:800])

        # Get videos from Discord (Zoom recordings, etc.)
        discord_videos = db.query(RawContent).filter(
            RawContent.source_id == discord.id,
            RawContent.content_type == "video"
        ).order_by(RawContent.collected_at.desc()).limit(3).all()

        print(f"\n--- DISCORD Videos ({len(discord_videos)} samples) ---")
        for i, item in enumerate(discord_videos, 1):
            print(f"\n[DISCORD VIDEO #{i}] ID: {item.id}")
            print(f"Collected: {item.collected_at}")
            if item.json_metadata:
                try:
                    meta = json.loads(item.json_metadata)
                    print(f"Channel: {meta.get('channel_name', 'unknown')}")
                    print(f"Platform: {meta.get('platform', 'unknown')}")
                except:
                    pass
            print(f"\nTranscript (first 2000 chars):")
            print("-" * 40)
            if item.content_text:
                print(item.content_text[:2000])
            else:
                print("(No transcript)")
            print("-" * 40)
    else:
        print("Discord source not found")

    # =========================================================================
    # CONTENT TYPE SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("CONTENT TYPE SUMMARY")
    print("=" * 80)

    sources = db.query(Source).all()
    for source in sources:
        count = db.query(RawContent).filter(RawContent.source_id == source.id).count()
        types = db.query(RawContent.content_type).filter(
            RawContent.source_id == source.id
        ).distinct().all()
        type_list = [t[0] for t in types]
        print(f"\n{source.name}: {count} items")
        print(f"  Types: {type_list}")

    db.close()

if __name__ == "__main__":
    main()
