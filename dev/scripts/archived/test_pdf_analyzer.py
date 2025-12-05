"""
Test script for PDF Analyzer Agent

Tests PDF extraction and analysis on real sample PDFs from:
- 42 Macro (Around The Horn reports)
- Discord (Options Insight weekly reports)
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.pdf_analyzer import PDFAnalyzerAgent

# Load environment variables
load_dotenv()


def test_pdf_analyzer():
    """Test PDF analyzer with sample PDFs."""

    print("=" * 80)
    print("PDF ANALYZER AGENT TEST")
    print("=" * 80)

    # Initialize agent
    print("\n[1] Initializing PDF Analyzer Agent...")
    try:
        agent = PDFAnalyzerAgent()
        print("[OK] Agent initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return

    # Find sample PDFs
    downloads_dir = project_root / "downloads"
    discord_pdfs = list((downloads_dir / "discord").glob("*.pdf"))
    macro42_pdfs = list((downloads_dir / "42macro").glob("*.pdf"))

    all_pdfs = discord_pdfs + macro42_pdfs

    print(f"\n[2] Found {len(all_pdfs)} sample PDFs:")
    print(f"    - Discord: {len(discord_pdfs)} PDFs")
    print(f"    - 42 Macro: {len(macro42_pdfs)} PDFs")

    if not all_pdfs:
        print("\n[ERROR] No PDFs found for testing")
        print(f"Expected PDFs in: {downloads_dir}")
        return

    # Test each PDF
    print("\n[3] Testing PDF Analysis...")
    print("-" * 80)

    results = []

    for i, pdf_path in enumerate(all_pdfs[:3], 1):  # Test first 3 PDFs
        print(f"\n[Test {i}/{min(3, len(all_pdfs))}] {pdf_path.name}")
        print(f"Source: {pdf_path.parent.name}")

        # Determine source
        if "discord" in str(pdf_path):
            source = "discord"
        elif "42macro" in str(pdf_path):
            source = "42macro"
        else:
            source = "unknown"

        try:
            # Analyze PDF
            analysis = agent.analyze(
                pdf_path=str(pdf_path),
                source=source,
                metadata={}
            )

            # Display results
            print(f"\n  Report Type: {analysis.get('report_type', 'unknown')}")
            print(f"  Pages: {analysis.get('page_count', 0)}")
            print(f"  Tables Extracted: {len(analysis.get('tables', []))}")
            print(f"  Text Length: {len(analysis.get('extracted_text', ''))} characters")

            print(f"\n  Key Themes ({len(analysis.get('key_themes', []))}):")
            for theme in analysis.get('key_themes', [])[:5]:
                print(f"    - {theme}")

            print(f"\n  Tickers Mentioned ({len(analysis.get('tickers_mentioned', []))}):")
            for ticker in analysis.get('tickers_mentioned', [])[:10]:
                print(f"    - {ticker}")

            print(f"\n  Sentiment: {analysis.get('sentiment', 'unknown')}")
            print(f"  Conviction: {analysis.get('conviction', 0)}/10")
            print(f"  Time Horizon: {analysis.get('time_horizon', 'unknown')}")

            if analysis.get('market_regime'):
                print(f"  Market Regime: {analysis['market_regime']}")

            if analysis.get('positioning'):
                print(f"\n  Positioning:")
                for asset, pos in analysis['positioning'].items():
                    print(f"    - {asset.capitalize()}: {pos}")

            if analysis.get('catalysts'):
                print(f"\n  Catalysts ({len(analysis['catalysts'])}):")
                for catalyst in analysis['catalysts'][:3]:
                    print(f"    - {catalyst}")

            if analysis.get('falsification_criteria'):
                print(f"\n  Falsification Criteria:")
                for criterion in analysis['falsification_criteria'][:3]:
                    print(f"    - {criterion}")

            print(f"\n  [OK] Analysis successful")

            results.append({
                "pdf": pdf_path.name,
                "source": source,
                "success": True,
                "themes_count": len(analysis.get('key_themes', [])),
                "tickers_count": len(analysis.get('tickers_mentioned', [])),
                "tables_count": len(analysis.get('tables', [])),
                "conviction": analysis.get('conviction', 0)
            })

        except Exception as e:
            print(f"\n  [ERROR] Analysis failed: {e}")
            results.append({
                "pdf": pdf_path.name,
                "source": source,
                "success": False,
                "error": str(e)
            })

        print("-" * 80)

    # Summary
    print("\n[4] Test Summary")
    print("=" * 80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTotal PDFs Tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print(f"\nSuccessful Analyses:")
        for r in successful:
            print(f"  [OK] {r['pdf']} ({r['source']})")
            print(f"    - Themes: {r['themes_count']}, Tickers: {r['tickers_count']}, "
                  f"Tables: {r['tables_count']}, Conviction: {r['conviction']}/10")

    if failed:
        print(f"\nFailed Analyses:")
        for r in failed:
            print(f"  [ERROR] {r['pdf']} ({r['source']})")
            print(f"    Error: {r['error']}")

    # Save detailed results to JSON
    output_file = project_root / "test_output" / "pdf_analyzer_test_results.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")
    print("\n" + "=" * 80)

    if len(successful) == len(results):
        print("[OK] ALL TESTS PASSED")
    elif len(successful) > 0:
        print(f"[WARN] PARTIAL SUCCESS ({len(successful)}/{len(results)} passed)")
    else:
        print("[ERROR] ALL TESTS FAILED")

    print("=" * 80)


if __name__ == "__main__":
    test_pdf_analyzer()
