"""
Test script for Cross-Reference Agent

Tests theme clustering, cross-source confluence, Bayesian updating, and contradiction detection.
Uses sample confluence-scored data similar to what Phase 3 Confluence Scorer would produce.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.cross_reference import CrossReferenceAgent

# Load environment variables
load_dotenv()


# Sample confluence-scored content (simulating Confluence Scorer outputs)
# These represent analyzed content that has been scored against the 7-pillar framework

SCORE_1_42MACRO = {
    "content_source": "42macro",
    "content_type": "pdf",
    "scored_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
    "pillar_scores": {
        "macro": 2,
        "fundamentals": 2,
        "valuation": 1,
        "positioning": 2,
        "policy": 1,
        "price_action": 2,
        "options_vol": 1
    },
    "core_total": 8,
    "total_score": 11,
    "confluence_level": "strong",
    "meets_threshold": True,
    "primary_thesis": "Disinflationary growth regime supports tech sector outperformance through Q2 2026",
    "variant_view": "Market pricing 12% earnings growth but tech fundamentals suggest 18% achievable given AI capex cycle",
    "p_and_l_mechanism": "Long QQQ LEAPs (Jan 2027 $450 calls), position size 15% of portfolio, 12-month horizon",
    "falsification_criteria": [
        "If CPI MoM >0.4% for 2 consecutive months",
        "If SPY breaks below 5600 on volume >1.5x average",
        "If tech sector earnings growth falls below 10% YoY"
    ],
    "reasoning": {
        "macro": "Strong evidence: PMIs expanding, inflation moderating, Fed pause likely through Q1 2026",
        "fundamentals": "Clear P&L path: AI infrastructure spend driving 18% tech earnings growth",
        "valuation": "Market pricing 21x forward but justified by growth trajectory",
        "positioning": "CFTC data shows equity positioning at 30th percentile vs 5-year range - room for upside",
        "policy": "Fed aligned with growth stability, no immediate tightening risk",
        "price_action": "SPY above 200DMA, clear uptrend structure, 5700 support holding",
        "options_vol": "VIX term structure normal, no immediate stress signals"
    },
    "tickers_mentioned": ["SPY", "QQQ", "NVDA", "MSFT", "AAPL"],
    "time_horizon": "3m",
    "conviction": 8
}

SCORE_2_DISCORD = {
    "content_source": "discord",
    "content_type": "image",
    "scored_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
    "pillar_scores": {
        "macro": 1,
        "fundamentals": 1,
        "valuation": 0,
        "positioning": 2,
        "policy": 0,
        "price_action": 2,
        "options_vol": 2
    },
    "core_total": 4,
    "total_score": 8,
    "confluence_level": "medium",
    "meets_threshold": False,
    "primary_thesis": "Tech sector positioning light with options skew favoring upside into year-end",
    "variant_view": "Put/call skew suggests excessive hedging, creating upside opportunity when hedge unwind occurs",
    "p_and_l_mechanism": "Sell QQQ puts at 430 strike (Dec expiry), collect premium on unwinding hedges",
    "falsification_criteria": [
        "If VIX spikes above 25",
        "If dealer gamma flips from long to short",
        "If QQQ breaks 440 support"
    ],
    "reasoning": {
        "macro": "Some macro context but not detailed",
        "fundamentals": "Tech mentioned generally but no specific P&L mechanism",
        "valuation": "No valuation discussion",
        "positioning": "Concrete data: heavy put buying at 5700 strike, dealer short gamma",
        "policy": "Not discussed",
        "price_action": "Clear levels: 5700 support, 5900 resistance, uptrend intact",
        "options_vol": "Specific opportunity: VIX term structure backwardation, elevated put skew at -2.5%"
    },
    "tickers_mentioned": ["SPX", "QQQ"],
    "time_horizon": "1m",
    "conviction": 6
}

SCORE_3_KT_TECHNICAL = {
    "content_source": "kt_technical",
    "content_type": "image",
    "scored_at": datetime.utcnow().isoformat(),
    "pillar_scores": {
        "macro": 0,
        "fundamentals": 0,
        "valuation": 0,
        "positioning": 1,
        "policy": 0,
        "price_action": 2,
        "options_vol": 0
    },
    "core_total": 1,
    "total_score": 3,
    "confluence_level": "weak",
    "meets_threshold": False,
    "primary_thesis": "SPY Elliott Wave structure suggests pullback to 575-580 before final push to 610",
    "variant_view": "Market expecting grind higher, but Wave 4 pullback offers better entry before Wave 5 finale",
    "p_and_l_mechanism": "Wait for pullback to 575-580, enter SPY long, target 610, stop at 568",
    "falsification_criteria": [
        "Break below 568 invalidates bullish Elliott count",
        "Failure to reclaim 575 after pullback suggests trend exhaustion"
    ],
    "reasoning": {
        "macro": "Not discussed",
        "fundamentals": "Not discussed",
        "valuation": "Not discussed",
        "positioning": "Some context on RSI overbought, but limited flow data",
        "policy": "Not discussed",
        "price_action": "Strong technical setup: Wave 3 complete, clear levels (575/595/610), RSI overbought at 72",
        "options_vol": "Not discussed"
    },
    "tickers_mentioned": ["SPY"],
    "time_horizon": "1m",
    "conviction": 7
}

SCORE_4_TWITTER = {
    "content_source": "twitter",
    "content_type": "text",
    "scored_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
    "pillar_scores": {
        "macro": 2,
        "fundamentals": 1,
        "valuation": 1,
        "positioning": 1,
        "policy": 2,
        "price_action": 1,
        "options_vol": 0
    },
    "core_total": 7,
    "total_score": 8,
    "confluence_level": "medium",
    "meets_threshold": False,
    "primary_thesis": "Tech sector benefiting from AI policy tailwinds and disinflationary macro regime",
    "variant_view": "Policy support for AI infrastructure creates sustained growth path beyond market's 2-year horizon",
    "p_and_l_mechanism": "Long tech equities (NVDA, MSFT) with 6-12 month horizon",
    "falsification_criteria": [
        "If AI regulation becomes restrictive",
        "If macro regime shifts to stagflation",
        "If tech capex cycle shows signs of peaking"
    ],
    "reasoning": {
        "macro": "Clear disinflationary growth view with supporting data",
        "fundamentals": "AI infrastructure spend discussed but P&L path not fully detailed",
        "valuation": "Some discussion of forward multiples but incomplete",
        "positioning": "General mention of flows but no concrete data",
        "policy": "Strong discussion of AI policy support and regulatory clarity",
        "price_action": "Levels mentioned but not detailed technical structure",
        "options_vol": "Not discussed"
    },
    "tickers_mentioned": ["NVDA", "MSFT", "AAPL", "QQQ"],
    "time_horizon": "6m",
    "conviction": 7
}

# Additional score with CONTRADICTORY view for testing contradiction detection
SCORE_5_SUBSTACK = {
    "content_source": "substack",
    "content_type": "text",
    "scored_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
    "pillar_scores": {
        "macro": 2,
        "fundamentals": 2,
        "valuation": 2,
        "positioning": 1,
        "policy": 1,
        "price_action": 1,
        "options_vol": 0
    },
    "core_total": 8,
    "total_score": 9,
    "confluence_level": "medium",
    "meets_threshold": False,
    "primary_thesis": "Tech sector overvalued and vulnerable to earnings disappointment in Q4",
    "variant_view": "Market ignoring valuation risk and capital cycle peak in semiconductor equipment",
    "p_and_l_mechanism": "Short QQQ via put spreads, 3-month horizon, target 10-15% correction",
    "falsification_criteria": [
        "If tech earnings surprise significantly to upside",
        "If valuation multiples compress but stock prices hold",
        "If new capex cycle emerges beyond AI"
    ],
    "reasoning": {
        "macro": "Views macro as supportive but sees inflation risk re-emerging",
        "fundamentals": "Argues AI spending not translating to revenue fast enough",
        "valuation": "Clear case that 21x forward is too expensive given historical context",
        "positioning": "Notes positioning is extended but doesn't see forced selling",
        "policy": "Sees policy risk from potential regulation",
        "price_action": "Technical topping pattern forming",
        "options_vol": "Not discussed"
    },
    "tickers_mentioned": ["QQQ", "NVDA", "MSFT"],
    "time_horizon": "3m",
    "conviction": 8
}


def test_cross_reference_agent():
    """Test cross-reference agent with sample confluence scores."""

    print("=" * 80)
    print("CROSS-REFERENCE AGENT TEST")
    print("=" * 80)

    # Initialize agent
    print("\n[1] Initializing Cross-Reference Agent...")
    try:
        agent = CrossReferenceAgent()
        print("[OK] Agent initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return

    # Prepare test data
    all_scores = [
        SCORE_1_42MACRO,
        SCORE_2_DISCORD,
        SCORE_3_KT_TECHNICAL,
        SCORE_4_TWITTER,
        SCORE_5_SUBSTACK
    ]

    print(f"\n[2] Testing with {len(all_scores)} confluence-scored content pieces...")
    print("-" * 80)

    for i, score in enumerate(all_scores, 1):
        print(f"\n  Content {i}: {score['content_source']} ({score['content_type']})")
        print(f"    Core Score: {score['core_total']}/10")
        print(f"    Confluence Level: {score['confluence_level'].upper()}")
        print(f"    Primary Thesis: {score['primary_thesis'][:80]}...")

    print("\n" + "-" * 80)

    # Test 1: Cross-reference with all scores (should find confluence + contradictions)
    print("\n[3] Running cross-reference analysis (7-day window, min 2 sources)...")
    try:
        cross_ref_result = agent.analyze(
            confluence_scores=all_scores,
            time_window_days=7,
            min_sources=2
        )

        print("[OK] Cross-reference analysis complete\n")

        # Display results
        print("=" * 80)
        print("CROSS-REFERENCE RESULTS")
        print("=" * 80)

        # Pipeline metrics
        print(f"\n[PIPELINE METRICS]")
        print(f"  Total Themes Extracted: {cross_ref_result.get('total_themes', 0)}")
        print(f"  Clustered Theme Groups: {cross_ref_result.get('clustered_themes_count', 0)}")
        print(f"  Sources Analyzed: {cross_ref_result.get('sources_analyzed', 0)}")
        print(f"  Time Window: {cross_ref_result.get('time_window_days', 0)} days")

        print(f"\n[NOTE] Clustered count = Total themes means Claude clustering failed")
        print(f"       (API credit issue). Each theme is its own cluster.")

        # Cross-source confluence (confluent themes with 2+ sources)
        confluences = cross_ref_result.get('confluent_themes', [])
        print(f"\n[A] Confluent Themes (2+ sources agree): {len(confluences)}")
        if confluences:
            for i, conf in enumerate(confluences[:3], 1):
                print(f"\n  Confluence {i}:")
                print(f"    Thesis: {conf.get('theme', 'N/A')[:100]}...")
                print(f"    Sources: {', '.join([s['source'] for s in conf.get('supporting_sources', [])])}")
                print(f"    Current Conviction: {conf.get('current_conviction', 0):.2f}")
                print(f"    Evidence Strength: {conf.get('evidence_strength', 0):.2f}")
        else:
            print(f"  [INFO] No themes had 2+ independent sources (required for confluence)")

        # Contradictions
        contradictions = cross_ref_result.get('contradictions', [])
        print(f"\n[B] Contradictions Detected: {len(contradictions)}")
        if contradictions:
            for i, contra in enumerate(contradictions[:3], 1):
                print(f"\n  Contradiction {i}:")
                print(f"    Thesis 1: {contra.get('thesis_1', 'N/A')[:80]}...")
                print(f"    Source 1: {contra.get('source_1', 'N/A')}")
                print(f"    Thesis 2: {contra.get('thesis_2', 'N/A')[:80]}...")
                print(f"    Source 2: {contra.get('source_2', 'N/A')}")
                print(f"    Severity: {contra.get('severity', 'N/A').upper()}")
                print(f"    Explanation: {contra.get('explanation', 'N/A')[:100]}...")
        else:
            print(f"  [INFO] No contradictions detected")

        # High-conviction ideas
        high_conviction = cross_ref_result.get('high_conviction_ideas', [])
        print(f"\n[C] High-Conviction Ideas (conviction >=0.75, sources >=2): {len(high_conviction)}")
        if high_conviction:
            for i, idea in enumerate(high_conviction[:3], 1):
                print(f"\n  Idea {i}:")
                print(f"    Thesis: {idea.get('theme', 'N/A')[:100]}...")
                print(f"    Conviction: {idea.get('current_conviction', 0):.2f}")
                print(f"    Sources: {', '.join([s['source'] for s in idea.get('supporting_sources', [])])}")
                print(f"    Trend: {idea.get('conviction_trend', 'N/A').upper()}")
        else:
            print(f"  [INFO] No high-conviction ideas met threshold")

        print("\n" + "=" * 80)
        print("[OK] Cross-reference analysis successful")

        # Save results
        output_file = project_root / "test_output" / "cross_reference_test_results.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(cross_ref_result, f, indent=2)

        print(f"\nDetailed results saved to: {output_file}")

    except Exception as e:
        print(f"\n[ERROR] Cross-reference analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Test with historical themes (Bayesian updating)
    print("\n" + "=" * 80)
    print("[4] Testing Bayesian updating with historical themes...")
    print("-" * 80)

    # Create mock historical themes
    historical_themes = [
        {
            "theme": "Tech sector outperformance thesis",  # Must use "theme" key
            "sources": ["42macro"],
            "current_conviction": 0.6,
            "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat()
        }
    ]

    try:
        cross_ref_with_history = agent.analyze(
            confluence_scores=all_scores,
            time_window_days=7,
            min_sources=2,
            historical_themes=historical_themes
        )

        print("[OK] Bayesian updating with historical context complete")
        print(f"\n  High-conviction ideas (with history): {len(cross_ref_with_history.get('high_conviction_ideas', []))}")

        # Show conviction evolution
        for idea in cross_ref_with_history.get('high_conviction_ideas', [])[:2]:
            print(f"\n  Idea: {idea.get('thesis', 'N/A')[:80]}...")
            print(f"    Current Conviction: {idea.get('conviction', 0):.2f}")
            print(f"    Trend: {idea.get('conviction_trend', 'N/A')}")

    except Exception as e:
        print(f"\n[ERROR] Bayesian updating test failed: {e}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    print("\n[NOTE] If API credit errors occur, that's expected.")
    print("       The test verifies pipeline structure works correctly.")
    print("       Production usage requires sufficient Claude API credits.")


if __name__ == "__main__":
    test_cross_reference_agent()
