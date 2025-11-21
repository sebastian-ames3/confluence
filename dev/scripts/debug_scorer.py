"""
Debug Confluence Scorer

Test the scorer on the Substack article to see detailed scoring breakdown.
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.models import SessionLocal, RawContent
from agents.confluence_scorer import ConfluenceScorerAgent

# Fetch Substack article
db = SessionLocal()
item = db.query(RawContent).filter(RawContent.id == 41).first()

print("=" * 80)
print("DEBUG: CONFLUENCE SCORER")
print("=" * 80)
print(f"Content: {item.content_text[:200]}...")
print(f"Length: {len(item.content_text)} chars")
print()

# Initialize scorer
scorer = ConfluenceScorerAgent()

# Score the content - need to structure it like Phase 2 agent output
scoring_input = {
    "extracted_text": item.content_text,  # Scorer looks for this field
    "source": "substack",
    "content_type": "article"
}

print("Scoring content...")
print("-" * 80)

result = scorer.analyze(scoring_input)

print()
print("=" * 80)
print("SCORING RESULTS")
print("=" * 80)
print(json.dumps(result, indent=2))

db.close()
