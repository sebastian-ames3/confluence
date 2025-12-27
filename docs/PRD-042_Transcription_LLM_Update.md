# PRD-042: Transcription LLM Update

**Status**: In Progress
**Priority**: High
**Estimated Complexity**: Medium

## Overview

Update the video transcription pipeline to use more efficient and accurate LLMs:
1. Replace OpenAI Whisper with AssemblyAI for transcription (58% cost reduction, better accuracy)
2. Add speaker diarization for financial video attribution (critical for compliance)
3. Update Claude model from Sonnet 4 to Sonnet 4.5 (lowest hallucination rate)

## Problem Statement

Current transcription pipeline has limitations:

1. **No speaker attribution**: Whisper doesn't identify who said what - critical for financial videos where host vs analyst opinions differ
2. **Cost inefficiency**: Whisper at $0.006/min vs AssemblyAI at $0.0025/min (58% savings)
3. **Accuracy concerns**: Whisper has ~30% more hallucinations than AssemblyAI Universal
4. **Model currency**: Claude Sonnet 4 is not the latest; Sonnet 4.5 has the lowest hallucination rate for quoting text (important for financial compliance)

## Solution

### 1. AssemblyAI Integration (Primary Transcription)

Replace OpenAI Whisper with AssemblyAI Universal:
- Enable speaker diarization for all financial videos
- Normalize output to existing segment format with added `speaker` field
- Keep Whisper as fallback when `ASSEMBLYAI_API_KEY` is not set

### 2. Claude Model Upgrade

Update default model across all agents:
- From: `claude-sonnet-4-20250514`
- To: `claude-sonnet-4-5-20250514`

### 3. Enhanced Analysis

Leverage speaker diarization in transcript analysis:
- Attribute quotes to specific speakers
- Track sentiment per speaker (host vs guest)
- Maintain backwards compatibility with existing transcripts

## Design Decisions

### 1. Fallback Strategy
- **Primary**: AssemblyAI (when `ASSEMBLYAI_API_KEY` is set)
- **Fallback**: OpenAI Whisper (existing behavior)
- This de-risks migration and allows A/B testing

### 2. Segment Format Compatibility
Current Whisper format:
```json
{"id": 0, "start": 0.0, "end": 4.5, "text": "Welcome to the show."}
```

New format with speaker (backwards compatible):
```json
{"id": 0, "start": 0.0, "end": 4.5, "text": "Welcome to the show.", "speaker": "A"}
```

### 3. No Chunking for AssemblyAI
AssemblyAI has no file size limit and handles long audio natively. The `_transcribe_chunked()` method is only needed for Whisper fallback.

### 4. Cost Comparison
| Provider | Cost/min | 60-min video |
|----------|----------|--------------|
| Whisper | $0.006 | $0.36 |
| AssemblyAI | $0.0025 | $0.15 |
| **Savings** | **58%** | **$0.21/video** |

## Technical Implementation

### 42.1 Dependencies

**File:** `requirements.txt`

```
# Transcription
assemblyai>=0.30.0  # AssemblyAI SDK (PRD-042)
```

### 42.2 Claude Model Update

**File:** `agents/base_agent.py`

Update default model in `__init__`:
```python
def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250514"):
```

### 42.3 AssemblyAI Client Initialization

**File:** `agents/transcript_harvester.py`

Add AssemblyAI client alongside OpenAI:
```python
def __init__(self, ...):
    # ... existing code ...

    # Initialize AssemblyAI client if API key available
    self.assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
    self.assemblyai_client = None
    if self.assemblyai_api_key:
        import assemblyai as aai
        aai.settings.api_key = self.assemblyai_api_key
        self.assemblyai_client = aai.Transcriber()
        logger.info("AssemblyAI client initialized (primary transcription)")
    else:
        logger.info("AssemblyAI key not found, using Whisper as primary")
```

### 42.4 AssemblyAI Transcription Method

**File:** `agents/transcript_harvester.py`

New method for AssemblyAI transcription with speaker diarization:
```python
async def _transcribe_assemblyai(self, audio_file: Path) -> Dict[str, Any]:
    """
    Transcribe audio using AssemblyAI with speaker diarization.

    Args:
        audio_file: Path to audio file

    Returns:
        Transcript with timestamps and speaker labels
    """
    import assemblyai as aai

    config = aai.TranscriptionConfig(
        speaker_labels=True,  # Enable speaker diarization
        language_code="en"
    )

    transcript = self.assemblyai_client.transcribe(
        str(audio_file),
        config=config
    )

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI transcription failed: {transcript.error}")

    # Convert to standard segment format with speaker labels
    segments = []
    for i, utterance in enumerate(transcript.utterances or []):
        segments.append({
            "id": i,
            "start": utterance.start / 1000,  # Convert ms to seconds
            "end": utterance.end / 1000,
            "text": utterance.text,
            "speaker": utterance.speaker  # "A", "B", etc.
        })

    return {
        "text": transcript.text,
        "segments": segments,
        "duration": transcript.audio_duration,
        "speaker_count": len(set(u.speaker for u in transcript.utterances or [])),
        "transcription_provider": "assemblyai"
    }
```

### 42.5 Updated Transcribe Method

**File:** `agents/transcript_harvester.py`

Update main `transcribe()` to use AssemblyAI as primary:
```python
async def transcribe(self, audio_file: Path) -> Dict[str, Any]:
    """
    Transcribe audio using AssemblyAI (primary) or Whisper (fallback).
    """
    # Try AssemblyAI first if available
    if self.assemblyai_client:
        try:
            logger.info("Transcribing with AssemblyAI (speaker diarization enabled)")
            return await self._transcribe_assemblyai(audio_file)
        except Exception as e:
            logger.warning(f"AssemblyAI failed, falling back to Whisper: {e}")

    # Fallback to Whisper
    return await self._transcribe_whisper(audio_file)
```

### 42.6 Enhanced Analysis Prompt

**File:** `agents/transcript_harvester.py`

Update `analyze_transcript()` to leverage speaker information:
```python
# Build analysis prompt with speaker context
if any(seg.get("speaker") for seg in transcript.get("segments", [])):
    speaker_instruction = """
- For key_quotes: Include the speaker label (e.g., "Speaker A said...")
- Note if different speakers have conflicting views
- Identify which speaker appears to be the host vs guest/analyst
"""
else:
    speaker_instruction = ""

user_prompt = f"""Analyze this financial market analysis video transcript.
...
{speaker_instruction}
...
"""
```

### 42.7 Key Quotes Schema Update

Update key_quotes to optionally include speaker:
```python
"key_quotes": [
    {"timestamp": "HH:MM:SS", "text": "quote text", "speaker": "A"},
    ...
]
```

## File Changes

### Modified Files
| File | Change |
|------|--------|
| `requirements.txt` | Add `assemblyai>=0.30.0` |
| `agents/base_agent.py` | Update default model to `claude-sonnet-4-5-20250514` |
| `agents/transcript_harvester.py` | Add AssemblyAI client, transcription method, update prompts |
| `dev/scripts/macro42_local.py` | Use AssemblyAI for local transcription |
| `tests/test_42macro_transcript.py` | Add tests for AssemblyAI and speaker diarization |

### No New Files Required

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ASSEMBLYAI_API_KEY` | No (fallback to Whisper) | AssemblyAI API key for transcription |
| `OPENAI_API_KEY` | Yes (for Whisper fallback) | OpenAI API key |
| `CLAUDE_API_KEY` | Yes | Claude API key for analysis |

## Testing

### Unit Tests (`tests/test_prd042_transcription.py`)

```python
class TestAssemblyAITranscription:
    def test_assemblyai_client_initialized_with_key(self):
        """AssemblyAI client created when API key present"""

    def test_whisper_fallback_without_key(self):
        """Falls back to Whisper when ASSEMBLYAI_API_KEY not set"""

    def test_segment_format_includes_speaker(self):
        """Segments include speaker field from diarization"""

    def test_speaker_count_in_response(self):
        """Response includes speaker_count metadata"""

class TestSpeakerDiarization:
    def test_utterances_converted_to_segments(self):
        """AssemblyAI utterances normalized to segment format"""

    def test_timestamps_converted_from_ms(self):
        """Milliseconds converted to seconds for compatibility"""

    def test_analysis_prompt_includes_speaker_instruction(self):
        """Analysis prompt enhanced when speakers detected"""

class TestClaudeModelUpdate:
    def test_default_model_is_sonnet_4_5(self):
        """BaseAgent defaults to claude-sonnet-4-5-20250514"""

    def test_transcript_harvester_uses_sonnet_4_5(self):
        """TranscriptHarvester inherits updated model"""

class TestBackwardsCompatibility:
    def test_existing_transcripts_still_analyzed(self):
        """Transcripts without speaker field still work"""

    def test_whisper_output_format_unchanged(self):
        """Whisper fallback maintains original format"""
```

### Integration Tests

- API accepts transcripts with and without speaker labels
- Speaker attribution flows through to synthesis
- Existing database transcripts still process correctly

## Success Metrics

1. **Cost reduction**: 58% reduction in transcription costs
2. **Speaker attribution**: 100% of multi-speaker videos have diarization
3. **Quote accuracy**: Reduced hallucination in key_quotes (measurable via Sonnet 4.5)
4. **Zero downtime**: Whisper fallback ensures no service interruption

## Definition of Done

### Dependencies
- [ ] `assemblyai>=0.30.0` added to requirements.txt

### Claude Model
- [ ] `BaseAgent` default model updated to `claude-sonnet-4-5-20250514`
- [ ] All agents inherit updated model

### AssemblyAI Integration
- [ ] AssemblyAI client initialized when API key present
- [ ] `_transcribe_assemblyai()` method implemented
- [ ] Speaker diarization enabled
- [ ] Segments include `speaker` field
- [ ] Timestamps converted from ms to seconds

### Fallback Logic
- [ ] Whisper used when `ASSEMBLYAI_API_KEY` not set
- [ ] Whisper used when AssemblyAI fails
- [ ] Existing `_transcribe_chunked()` preserved for Whisper

### Analysis Enhancement
- [ ] Analysis prompt includes speaker instructions when available
- [ ] `key_quotes` can include optional `speaker` field
- [ ] Backwards compatible with speaker-less transcripts

### Local Script
- [ ] `macro42_local.py` uses AssemblyAI when available

### Testing
- [ ] Unit tests for AssemblyAI transcription
- [ ] Unit tests for speaker diarization
- [ ] Unit tests for Claude model update
- [ ] Backwards compatibility tests pass
- [ ] Existing tests still pass

### Documentation
- [ ] Environment variable documented
- [ ] CLAUDE.md updated if needed
- [ ] PRD moved to archived on completion

## Rollout

1. **Phase 1**: Dependencies + Model Update
   - Add assemblyai to requirements.txt
   - Update Claude model to Sonnet 4.5
   - Deploy to verify no regressions

2. **Phase 2**: AssemblyAI Integration
   - Add AssemblyAI transcription method
   - Add fallback logic
   - Test with subset of videos

3. **Phase 3**: Analysis Enhancement
   - Update analysis prompts for speaker attribution
   - Verify quote accuracy improvement

4. **Phase 4**: Full Rollout
   - Set `ASSEMBLYAI_API_KEY` in production
   - Monitor costs and accuracy
   - Archive PRD

---

*Created: 2025-12-27*
