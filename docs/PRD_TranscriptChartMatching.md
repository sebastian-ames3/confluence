# PRD: Transcript-Chart Matching System

**Status:** Planning
**Priority:** High (Cost Optimization)
**Owner:** Sebastian Ames
**Created:** 2025-11-20
**Target:** Post-MVP Enhancement

---

## Executive Summary

Reduce Chart Intelligence costs by 85% on 42 Macro videos by only analyzing charts that are actually discussed in the video, rather than all 70-80 slides in the PDF.

**Problem:** 42 Macro PDFs contain 70-80 slides, but Darius typically discusses only 10-15 in the video. Currently we analyze all images (~$0.40/video).

**Solution:** Parse video transcript to identify which charts are discussed, then only analyze those specific charts.

**Impact:**
- Cost reduction: 85% ($0.40 → $0.06 per video)
- Monthly savings: ~$10-12 (daily videos)
- Maintains analysis quality (only analyzing what matters)

---

## Background

### Current State
- Chart Intelligence System extracts all 70-80 images from 42 Macro PDFs
- Smart filtering removes ~60% as text-only (logos, headers)
- Still analyzing ~25-30 charts per PDF
- Cost: ~$0.30-0.40 per PDF

### The Opportunity
- 42 Macro videos: Darius discusses ~10-15 specific charts
- The other 55-65 slides are skipped or mentioned briefly
- We're paying to analyze charts he never discusses

### Why This Matters
- Reduces wasted API calls on irrelevant charts
- Maintains full coverage of discussed content
- Scalable: Works for all 42 Macro video + PDF pairs

---

## User Stories

**As Sebastian**, I want the system to only analyze charts that Darius actually discusses in his videos, so that I'm not paying to analyze 70 slides when he only talks about 10.

**As the system**, when processing a 42 Macro video + PDF pair, I want to identify which charts are mentioned in the transcript and prioritize those for visual analysis.

---

## Technical Design

### Architecture

```
42 Macro Video → Transcript Harvester → TranscriptChartMatcher
                                              ↓
42 Macro PDF → Extract Images → Match to Mentions → Analyze Top 15
```

### Components

#### 1. TranscriptChartMatcher

**Purpose:** Match transcript mentions to PDF images

**Input:**
- Video transcript (string)
- List of extracted PDF images (metadata)

**Processing:**
1. Parse transcript for chart mentions using regex patterns:
   - "Looking at [title]"
   - "This shows [title]"
   - "The [asset] chart"
   - "Moving to [title]"
2. Extract topics/assets mentioned (S&P 500, VIX, CPI, etc.)
3. Match topics to image metadata (filename, page number)
4. Calculate match scores
5. Prioritize images by score

**Output:**
- Prioritized list of images to analyze
- Match scores and confidence levels
- Cost reduction percentage

**Pattern Matching Examples:**
```
"Looking at the S&P 500 chart..." → Extract: "S&P 500"
"Moving to CPI data..." → Extract: "CPI"
"The VIX is showing..." → Extract: "VIX"
```

#### 2. Enhanced PDF Analyzer Integration

**New Parameter:** `transcript: Optional[str] = None`

**Logic:**
```python
if transcript and source == "42macro":
    # Use transcript-chart matching
    matcher = TranscriptChartMatcher()
    prioritized = matcher.prioritize_for_analysis(
        transcript=transcript,
        all_images=extracted_images,
        max_analyze=15
    )
    images_to_analyze = prioritized["images_to_analyze"]
else:
    # Original behavior: analyze all (after filtering)
    images_to_analyze = extracted_images
```

### Matching Algorithm

**Phase 1: Mention Extraction**
```python
def extract_chart_mentions(transcript):
    segments = split_by_sentence(transcript)
    mentions = []

    for segment in segments:
        if has_chart_keyword(segment):
            topics = extract_topics(segment)
            mentions.append({
                "topics": topics,
                "confidence": calculate_confidence(segment)
            })

    return mentions
```

**Phase 2: Image Matching**
```python
def match_to_images(mentions, images):
    all_topics = extract_all_topics(mentions)

    for image in images:
        score = 0
        for topic in all_topics:
            if topic in image.filename.lower():
                score += 0.5
            # Could add page number matching, OCR matching, etc.

        if score > 0:
            prioritized.append((image, score))

    return sorted_by_score(prioritized)
```

**Phase 3: Fallback Logic**

If matching fails:
- **No mentions found**: Analyze first 15 images (by page number)
- **No matches found**: Analyze first 15 images (mentions exist but no filename matches)
- **Error occurs**: Fallback to analyzing all images

### Edge Cases

1. **Transcript unavailable:** Analyze all images (current behavior)
2. **No chart mentions in transcript:** Analyze first N images by page
3. **Ambiguous mentions:** Use confidence scores to prioritize
4. **Multiple mentions of same chart:** Deduplicate by topic
5. **Chart mentioned but not in PDF:** Skip gracefully

---

## Implementation Plan

### Phase 1: Core Matcher (Day 1)
- Create `TranscriptChartMatcher` class
- Implement mention extraction with regex patterns
- Implement topic extraction (assets, indicators)
- Test on sample transcripts

### Phase 2: Image Matching (Day 2)
- Implement match scoring algorithm
- Handle deduplication and prioritization
- Add fallback logic for edge cases
- Test on real 42 Macro PDF

### Phase 3: Integration (Day 2-3)
- Update `PDFAnalyzerAgent.analyze()` to accept transcript
- Integrate matcher into image analysis pipeline
- Test end-to-end with video + PDF pair
- Verify cost reduction

### Phase 4: Production Testing (Day 3)
- Test on 5 different 42 Macro videos
- Verify match accuracy
- Measure cost reduction
- Handle edge cases

---

## Testing Strategy

### Unit Tests
- Test mention extraction on sample transcripts
- Test topic extraction with various phrasings
- Test matching algorithm with mock data
- Test fallback logic

### Integration Tests
- Test with real 42 Macro video transcript
- Verify matched images are relevant
- Check that discussed charts are prioritized
- Confirm cost reduction achieved

### Success Criteria
- ✅ Extract 8+ chart mentions from typical transcript
- ✅ Match 80%+ of mentions to PDF images
- ✅ Reduce analyzed images from ~25 to ~15
- ✅ Cost reduction: 40-50% minimum
- ✅ No false negatives (discussed charts not analyzed)

---

## Cost Analysis

### Current State (Without Matching)
- Images extracted: ~142
- After filtering (92%): ~11 charts
- Vision API cost: 11 × $0.03 = **$0.33 per PDF**
- Monthly (30 videos): **$9.90/month**

### With Transcript Matching
- Prioritized charts: ~6-8 (only discussed)
- Vision API cost: 7 × $0.03 = **$0.21 per PDF**
- Monthly (30 videos): **$6.30/month**
- **Savings: $3.60/month (36%)**

### Best Case Scenario
If we only analyze exactly what's discussed (~6 charts):
- Cost: 6 × $0.03 = **$0.18 per PDF**
- Monthly: **$5.40/month**
- **Savings: $4.50/month (45%)**

---

## Risks & Mitigation

### Risk 1: False Negatives
**Problem:** Important chart discussed but not matched
**Mitigation:**
- Conservative matching (include medium-confidence matches)
- Always analyze first ~5 pages (usually key charts)
- Fallback to analyzing all if no matches

### Risk 2: Transcript Quality
**Problem:** Auto-generated transcripts miss key mentions
**Mitigation:**
- Use multiple patterns for matching
- Don't rely solely on exact phrases
- Include asset-based matching (SPX, VIX, etc.)

### Risk 3: Filename Mismatches
**Problem:** Chart discussed but filename doesn't match topic
**Mitigation:**
- Start with simple filename matching
- Future: Add OCR-based matching if needed
- Future: Use page number proximity if mentioned

### Risk 4: Over-Optimization
**Problem:** Match too aggressively, analyze too few charts
**Mitigation:**
- Set minimum threshold (always analyze at least 10 images)
- Include "buffer" images (before/after matched pages)
- Monitor false negative rate

---

## Future Enhancements

### Phase 2 (Optional)
- **Page number matching:** "On slide 15..." → analyze page 15
- **OCR-based matching:** Extract text from images, match to topics
- **Time-based prioritization:** Match transcript timestamps to PDF page order
- **Confidence refinement:** ML model to improve match accuracy

### Phase 3 (Optional)
- **Cross-reference validation:** Check if matched charts actually contain discussed assets
- **Feedback loop:** Track which matched charts score high in confluence
- **Auto-adjust thresholds:** Learn optimal matching params over time

---

## Dependencies

- ✅ Transcript Harvester Agent (already built)
- ✅ PDF Analyzer Agent (already built)
- ✅ Image extraction (already built)
- New: TranscriptChartMatcher module

---

## Success Metrics

**Must Have:**
- 30%+ cost reduction on 42 Macro videos
- No false negatives on key charts
- <5% error rate on matches

**Nice to Have:**
- 50%+ cost reduction
- 90%+ match accuracy
- Automatic fallback handling

**Track:**
- Cost per video (before/after)
- Number of images analyzed (before/after)
- Match accuracy (manual spot-checks)
- Confluence scores (should remain stable or improve)

---

## Timeline

**Day 1:** Build TranscriptChartMatcher core
**Day 2:** Integrate with PDF Analyzer + test
**Day 3:** Production testing on 5 videos
**Total:** 2-3 days

---

## Approval Checklist

Before implementing:
- [ ] PRD reviewed and approved
- [ ] Edge cases documented
- [ ] Fallback logic defined
- [ ] Cost analysis verified
- [ ] Success metrics agreed upon

---

**Version:** 1.0
**Last Updated:** 2025-11-20
