"""
Test Analysis Pipeline - 3 Items

Analyzes 1 YouTube video, 1 42 Macro item, and 1 Substack article.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.models import SessionLocal, RawContent, Source
from agents.content_classifier import ContentClassifierAgent
from agents.confluence_scorer import ConfluenceScorerAgent
from agents.transcript_harvester import TranscriptHarvesterAgent
from agents.pdf_analyzer import PDFAnalyzerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_3_items():
    """Test analysis on 3 items from different sources."""

    print("=" * 80)
    print("TESTING ANALYSIS PIPELINE - 3 ITEMS")
    print("=" * 80)

    db = SessionLocal()

    try:
        # Fetch 1 item from each source
        sources_to_test = ["youtube", "42macro", "substack"]
        items_to_analyze = []

        for source_name in sources_to_test:
            source = db.query(Source).filter(Source.name == source_name).first()
            if source:
                item = db.query(RawContent).filter(
                    RawContent.source_id == source.id,
                    RawContent.processed == False
                ).first()

                if item:
                    items_to_analyze.append({
                        "id": item.id,
                        "source": source_name,
                        "content_type": item.content_type,
                        "content_text": item.content_text,
                        "url": item.url,
                        "file_path": item.file_path
                    })
                    print(f"[OK] Found {source_name} item (ID: {item.id})")
                else:
                    print(f"[WARNING] No unprocessed {source_name} items found")
            else:
                print(f"[WARNING] Source {source_name} not found in database")

        print()
        print(f"Total items to analyze: {len(items_to_analyze)}")
        print("=" * 80)
        print()

        # Initialize agents
        classifier = ContentClassifierAgent()
        scorer = ConfluenceScorerAgent()
        transcript_harvester = TranscriptHarvesterAgent()
        pdf_analyzer = PDFAnalyzerAgent()

        results = []

        # Analyze each item
        for i, item in enumerate(items_to_analyze, 1):
            print(f"\n[{i}/{len(items_to_analyze)}] Analyzing {item['source']} (ID: {item['id']})")
            print("-" * 80)

            try:
                # Step 1: Classify
                print(f"  Step 1: Classifying content...")
                classification = classifier.classify(item)

                print(f"    Classification: {classification.get('classification', 'unknown')}")
                print(f"    Priority: {classification.get('priority', 'unknown')}")
                print(f"    Route to: {', '.join(classification.get('route_to_agents', []))}")

                # Step 2: Extract content based on classification
                route_to = classification.get('route_to_agents', [])
                extracted_content = None

                if 'transcript_harvester' in route_to:
                    print(f"  Step 2: Extracting video transcript...")
                    if item.get('url'):
                        extracted_content = await transcript_harvester.harvest(
                            video_url=item['url'],
                            source=item['source']
                        )
                        transcript_text = extracted_content.get('transcript', '') if extracted_content else ''
                        print(f"    Transcript length: {len(transcript_text)} chars")
                    else:
                        print(f"    [WARNING] No URL found for transcript extraction")

                elif 'pdf_analyzer' in route_to:
                    print(f"  Step 2: Extracting PDF content...")
                    if item.get('file_path'):
                        extracted_content = pdf_analyzer.analyze(
                            pdf_path=item['file_path'],
                            source=item['source']
                        )
                        pdf_text = extracted_content.get('extracted_text', '') if extracted_content else ''
                        print(f"    PDF text length: {len(pdf_text)} chars")
                    else:
                        print(f"    [WARNING] No file path found for PDF extraction")

                else:
                    # Simple text - use as is
                    print(f"  Step 2: Using raw text...")
                    extracted_content = {
                        'content': item.get('content_text', ''),
                        'source': item['source']
                    }
                    print(f"    Text length: {len(item.get('content_text', ''))} chars")

                # Step 3: Score for confluence
                print(f"  Step 3: Scoring for confluence...")

                if extracted_content:
                    # Prepare full content for scoring
                    if 'transcript' in extracted_content:
                        # Transcript
                        full_content = extracted_content.get('transcript', '')
                    elif 'extracted_text' in extracted_content:
                        # PDF
                        full_content = extracted_content.get('extracted_text', '')
                    else:
                        # Raw text
                        full_content = extracted_content.get('content', '')

                    scoring_input = {
                        "source": item['source'],
                        "content_type": item['content_type'],
                        "content_text": full_content,
                        "url": item.get('url', ''),
                        "file_path": item.get('file_path', ''),
                        "metadata": extracted_content
                    }

                    score = scorer.analyze(scoring_input)

                    print(f"    Core Score: {score.get('core_score', 0)}/10")
                    print(f"    Total Score: {score.get('total_score', 0)}/14")
                    print(f"    Conviction: {score.get('conviction_tier', 'unknown')}")
                    print(f"    Meets Threshold: {score.get('meets_threshold', False)}")

                    results.append({
                        "item": item,
                        "classification": classification,
                        "extracted_content": extracted_content,
                        "score": score
                    })

                    print(f"  [SUCCESS] Analysis complete")
                else:
                    print(f"  [WARNING] No content extracted - skipping scoring")

            except Exception as e:
                print(f"  [ERROR] Analysis failed: {e}")
                logger.exception("Detailed error:")

        # Summary
        print()
        print("=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print(f"Analyzed: {len(results)}/{len(items_to_analyze)} items")

        high_confidence = [r for r in results if r['score'].get('meets_threshold', False)]
        print(f"High confidence items: {len(high_confidence)}")

        if high_confidence:
            print("\nHigh Confidence Items:")
            for r in high_confidence:
                item = r['item']
                score = r['score']
                print(f"  - {item['source']} (ID {item['id']}): {score.get('total_score', 0)}/14")
                print(f"    Primary thesis: {score.get('primary_thesis', 'N/A')[:100]}")

        print()
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_3_items())
