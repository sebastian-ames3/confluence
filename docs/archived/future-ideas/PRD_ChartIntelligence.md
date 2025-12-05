# PRD: Chart Intelligence System

**Status:** Planning
**Priority:** High
**Owner:** Sebastian Ames
**Created:** 2025-11-20
**Target:** Post-MVP Enhancement

---

## Executive Summary

Enhance the Confluence Hub analysis pipeline to extract and analyze visual data (charts, graphs, tables) from collected content across all sources. This ensures we capture ALL institutional-grade data, not just text narratives.

**Current Gap:** We only analyze text content. Sources like 42 Macro, KT Technical, and Substack contain critical data in charts that we're missing.

**Solution:** Multi-modal analysis pipeline with specialized tools for different visual content types.

---

## Problem Statement

### What We're Missing Today

**42 Macro PDFs:**
- ❌ Only extracting cover page text (~300 chars)
- ❌ Missing all 70-80 slides of macro data
- ❌ Missing positioning charts, regime indicators, flow data
- ❌ Currently scoring 0/14 due to lack of data

**KT Technical Blogs:**
- ❌ Missing price charts with technical levels
- ❌ Missing support/resistance analysis
- ❌ Missing visual positioning data

**Substack Articles:**
- ❌ Missing 1-2 embedded charts per article
- ❌ Missing data visualizations authors reference

**Impact:** Confluence scoring gives 0-2/14 scores when actual content has strong macro thesis with supporting data.

---

## Goals & Success Metrics

### Primary Goals

1. **Extract ALL visual content** from PDFs, blogs, and web articles
2. **Analyze visual data** with appropriate specialized tools
3. **Combine text + visual analysis** for comprehensive scoring
4. **Increase confluence scores** for data-rich content (from 0-2/14 → 6-12/14)

### Success Metrics

- 42 Macro content scores >6/14 (currently 0/14)
- Chart extraction rate: 95%+ of embedded visuals captured
- Analysis accuracy: 90%+ for single charts, 80%+ for multi-panel
- Cost per analysis: <$0.50 per PDF/article
- Processing time: <3 minutes per PDF/article

---

## User Stories

**As Sebastian, I want:**
- All chart data from 42 Macro PDFs analyzed so I don't miss critical positioning/regime signals
- KT Technical price charts analyzed so I capture technical confluence
- Substack charts analyzed when present so I have complete context
- Combined text + visual analysis so I see if narrative matches data
- Confidence scores so I know when to manually review complex content

---

## Technical Architecture

### Phase 1: Image Extraction

**Component:** `ImageExtractor` module

**Inputs:**
- PDF file path
- HTML content (for blogs/substacks)

**Processing:**
1. **PDFs:** Extract all embedded images using `PyMuPDF`
2. **Web:** Parse HTML for `<img>` tags, download images
3. Save to temporary directory with metadata

**Outputs:**
- List of extracted image paths
- Metadata: source file, page number, image type

### Phase 2: Content Classification

**Component:** `VisualContentClassifier`

**Inputs:**
- Extracted image

**Processing:**
- Analyze image structure (without full vision analysis)
- Classify as:
  - `table` - Grid of numbers/text
  - `single_chart` - One time-series, bar, pie chart
  - `multi_panel` - Multiple charts in one image
  - `text_only` - Screenshot of text (skip)

**Outputs:**
- Content type classification
- Routing decision (which tool to use)

### Phase 3: Specialized Analysis

**Component:** `ChartIntelligenceOrchestrator`

**3A: Table Analysis (for probability tables, data grids)**
- Tool: Tesseract OCR + table parser
- Extract structured data as CSV/JSON
- Parse numbers, dates, headers
- Cost: ~$0.01 per table

**3B: Single Chart Analysis (for simple time-series, bar charts)**
- Tool: Claude Vision API
- Extract: trend, key levels, annotations, insight
- Cost: ~$0.012 per chart

**3C: Multi-Panel Analysis (for dashboards with 5-10 charts)**
- Tool: Image segmentation + Claude Vision
- Split into sub-images
- Analyze each panel separately
- Combine insights
- Cost: ~$0.05-0.10 per multi-panel

**3D: Skip Handler**
- For images with no data value (logos, text screenshots)
- No analysis performed
- Cost: $0

### Phase 4: Transcript-Chart Matching

**Component:** `TranscriptChartMatcher` (42 Macro specific)

**Inputs:**
- Video transcript
- Extracted PDF images

**Processing:**
1. Parse transcript for chart title mentions
   - Pattern: "Looking at [TITLE]...", "This shows [TITLE]..."
2. Match titles to image filenames/metadata
3. Prioritize matched charts for analysis

**Outputs:**
- Priority list: Charts Darius discussed (analyze these)
- Secondary list: Charts he skipped (optional analysis)

### Phase 5: Combined Analysis & Scoring

**Component:** Updated `ConfluenceScorerAgent`

**Inputs:**
- Text analysis results
- Chart analysis results (structured JSON)

**Processing:**
1. Merge insights from both modalities
2. Cross-validate: Does text narrative match chart data?
3. Score across 7 pillars using combined evidence
4. Flag discrepancies (text bullish but chart bearish)

**Outputs:**
- Enhanced confluence score
- Evidence map (which pillars supported by text vs charts)
- Confidence level

---

## Data Models

### Extracted Image Metadata
```json
{
  "image_id": "uuid",
  "source_content_id": 123,
  "file_path": "/tmp/images/macro_slide_45.png",
  "source_file": "42macro_20251120.pdf",
  "page_number": 45,
  "extraction_timestamp": "2025-11-20T12:00:00Z",
  "content_type": "multi_panel",
  "analyzed": true,
  "analysis_timestamp": "2025-11-20T12:01:30Z"
}
```

### Chart Analysis Result
```json
{
  "image_id": "uuid",
  "analysis_type": "single_chart",
  "chart_type": "time_series",
  "data": {
    "title": "CPI YoY%",
    "metric": "cpi_yoy",
    "current_value": 2.1,
    "trend": "declining",
    "key_levels": [2.0, 2.5, 3.0],
    "time_period": "2020-2025",
    "interpretation": "Disinflation trend continuing"
  },
  "confluence_pillars": ["macro", "policy"],
  "confidence": 0.95
}
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create `ImageExtractor` module
- [ ] Implement PDF image extraction (PyMuPDF)
- [ ] Implement web image extraction (requests + BeautifulSoup)
- [ ] Test on existing 8 42 Macro PDFs
- [ ] Verify extraction completeness

### Phase 2: Classification (Week 1-2)
- [ ] Create `VisualContentClassifier`
- [ ] Implement lightweight classification logic
- [ ] Test on extracted images
- [ ] Tune classification rules

### Phase 3: Analysis Tools (Week 2-3)
- [ ] Implement Table Analyzer (OCR + parser)
- [ ] Implement Single Chart Analyzer (Claude Vision)
- [ ] Implement Multi-Panel Analyzer (segmentation + vision)
- [ ] Test each tool on sample images
- [ ] Measure accuracy and cost

### Phase 4: Orchestration (Week 3)
- [ ] Create `ChartIntelligenceOrchestrator`
- [ ] Route images to appropriate analyzers
- [ ] Implement transcript-chart matching for 42 Macro
- [ ] Handle errors and edge cases
- [ ] Cleanup temporary files

### Phase 5: Integration (Week 4)
- [ ] Update `PDFAnalyzerAgent` to use Chart Intelligence
- [ ] Update collectors to extract images during collection
- [ ] Update `ConfluenceScorerAgent` to accept visual analysis
- [ ] Update database schema for image metadata
- [ ] Test end-to-end pipeline

### Phase 6: Validation (Week 4)
- [ ] Run on existing collected content
- [ ] Manually verify sample analyses
- [ ] Compare scores before/after Chart Intelligence
- [ ] Tune prompts and thresholds
- [ ] Document accuracy metrics

---

## Cost Analysis

### Per-Source Cost Breakdown

**42 Macro (PDF + Video):**
- Extract images: $0 (local processing)
- Classify images: $0 (local heuristics)
- Analyze 10-15 matched charts: $0.12-0.18
- Video transcript: $0.10-0.30
- **Total: ~$0.40 per weekly report**
- **Monthly (4 reports): $1.60**

**KT Technical (Blog post):**
- Extract 2-3 charts: $0
- Analyze charts: $0.024-0.036
- Text analysis: $0.05
- **Total: ~$0.08 per post**
- **Monthly (10 posts): $0.80**

**Substack (Article):**
- Extract 0-2 charts: $0
- Analyze if present: $0-0.024
- Text analysis: $0.05
- **Total: ~$0.05-0.07 per article**
- **Monthly (20 articles): $1.20**

**Total Monthly Cost: ~$3.60** (vs $1.50 text-only currently)
**Cost Increase: +$2.10/month for comprehensive visual analysis**

---

## Storage Requirements

### Temporary Storage (During Analysis)
- All extracted images: 20-30MB per PDF
- Deleted after analysis complete
- Peak usage: ~150MB (5 PDFs in parallel)

### Persistent Storage
- Analysis results (JSON): 50KB per source
- Analyzed images (optional): 2-3MB per source if retained
- **Recommended: Delete images, keep JSON only**
- **Monthly storage: ~10MB** (JSON only)

---

## Risks & Mitigations

### Risk 1: OCR Accuracy on Dense Tables
**Mitigation:** Use Claude Vision as fallback if OCR confidence <80%

### Risk 2: Multi-Panel Segmentation Failures
**Mitigation:** If segmentation fails, analyze entire image as-is

### Risk 3: Cost Overruns
**Mitigation:** Monitor per-analysis cost, adjust sampling if needed

### Risk 4: Transcript-Chart Matching Failures
**Mitigation:** Fallback to analyzing top 15 charts by page number

### Risk 5: Storage Bloat
**Mitigation:** Mandatory cleanup in finally blocks, monitor disk usage

---

## Dependencies

**Python Libraries:**
- `PyMuPDF` (fitz) - PDF image extraction
- `Pillow` - Image processing
- `pytesseract` - OCR for tables
- `BeautifulSoup4` - HTML parsing for web images
- `requests` - Image downloading
- Existing: `anthropic` SDK for Claude Vision

**External Services:**
- Claude Vision API (Sonnet 4)
- Tesseract OCR (local)

**System Requirements:**
- Tesseract installed on system
- 500MB temp disk space
- No additional compute requirements

---

## Open Questions

1. Should we analyze ALL 70 slides or only what Darius discusses?
   - **Decision:** Analyze matched slides only, keep cost at ~$0.40/video

2. Should we keep analyzed images or delete everything?
   - **Decision:** Delete all images, keep JSON analysis only

3. How to handle multi-panel charts (7+ charts in one image)?
   - **Decision:** Segment and analyze separately for accuracy

4. What's the confidence threshold for manual review?
   - **To be determined:** Test and tune during Phase 6

5. Should KT Technical images be analyzed even without text mention?
   - **Decision:** Yes, always analyze (charts are the main content)

---

## Success Criteria

**Launch Criteria:**
- ✅ Extracts 95%+ of visual content from all sources
- ✅ Analysis accuracy >85% on validation set
- ✅ Cost per analysis <$0.50
- ✅ Processing time <3min per source
- ✅ Zero manual intervention required
- ✅ Confluence scores increase to 6+/14 for data-rich content

**Post-Launch Monitoring:**
- Track analysis accuracy via spot-checks
- Monitor cost per source
- Measure confluence score improvements
- Collect feedback on false positives/negatives

---

## Timeline

**Week 1:** Foundation + Classification
**Week 2-3:** Analysis Tools
**Week 3:** Orchestration
**Week 4:** Integration + Validation
**Total: 4 weeks to production**

---

## Approval

This PRD requires approval before implementation begins.

- [ ] Sebastian - Product Owner
- [ ] Claude - Technical Lead

**Approved by:** _________________
**Date:** _________________
