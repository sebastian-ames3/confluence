# PRD-018: Video Transcription for All Sources

## Overview
Automatically transcribe videos from all collection sources (Discord, 42 Macro, YouTube) using yt-dlp for audio extraction and Whisper for transcription. Store transcripts in the database for AI analysis.

## Problem Statement
Video content from multiple sources contains valuable spoken analysis that is currently not captured:
- **Discord**: Zoom/Webex recording links with market analysis
- **42 Macro**: Vimeo-hosted "Around The Horn" weekly videos
- **YouTube**: Long-form market commentary videos

The collectors store video URLs/IDs but don't extract the actual spoken content, leaving significant alpha on the table.

**Why yt-dlp?**
yt-dlp supports all major video platforms (Zoom, Webex, Vimeo, YouTube) and handles authentication, landing pages, and stream extraction automatically.

## Goals
1. Automatically transcribe videos when collected from any source
2. Use the existing `TranscriptHarvesterAgent` for transcription
3. Store transcripts in the database for synthesis
4. Clean up temporary audio files after transcription
5. Run transcription asynchronously to not block collection

## Non-Goals
- Real-time/live meeting transcription
- Speaker diarization (identifying who said what)
- Downloading full video files (audio-only extraction)
- Video content analysis (just transcription)

## Video Sources

| Source | Platform | Video Type | Priority |
|--------|----------|------------|----------|
| Discord | Zoom/Webex | Market analysis recordings | High |
| 42 Macro | Vimeo | Around The Horn weekly | High |
| YouTube | YouTube | Channel videos | Medium |

## Requirements

### Dependencies

| Package | Purpose | Installation |
|---------|---------|--------------|
| ffmpeg | Audio extraction/conversion | `winget install ffmpeg` |
| yt-dlp | Extract audio from video URLs | `pip install yt-dlp` |
| openai-whisper | Local transcription | `pip install openai-whisper` |
| openai | Whisper API (alternative) | `pip install openai` |

### Configuration

**Whisper (Local):**
- Model: `base` (good balance of speed/accuracy)
- Language: English (forced)
- Expected time: 1-3 minutes per 10-min recording

**Whisper API (Alternative):**
- Cost: $0.006/minute of audio
- Faster than local, requires OPENAI_API_KEY

**yt-dlp:**
- Extract audio only (`-x` flag)
- Output format: MP3
- Temp directory: `downloads/{source}/audio/`

## Implementation

### Phase 1: Wire TranscriptHarvesterAgent into Collection

#### 1. Update `/api/collect/discord` endpoint

After saving video content, trigger transcription:

```python
# In backend/routes/collect.py - ingest_discord_data()

from agents.transcript_harvester import TranscriptHarvesterAgent

# After saving each message with video content
if message_data.get("content_type") == "video":
    url = message_data.get("url")
    if url:
        # Run transcription in background thread to not block
        asyncio.create_task(_transcribe_video(db, raw_content.id, url, "discord"))
```

#### 2. Update `/api/collect/42macro` endpoint

```python
# In backend/routes/collect.py - ingest_42macro_data()

# After saving each video item
if item_data.get("content_type") == "video":
    url = item_data.get("url")
    if url:
        asyncio.create_task(_transcribe_video(db, raw_content.id, url, "42macro"))
```

#### 3. Create shared transcription function

```python
# In backend/routes/collect.py

async def _transcribe_video(db: Session, raw_content_id: int, video_url: str, source: str):
    """
    Transcribe a video and update the database record.
    Runs in background to not block collection.
    """
    try:
        harvester = TranscriptHarvesterAgent()

        # Determine priority tier based on source
        if source == "discord":
            tier = 1  # High priority - Imran's videos
        elif source == "42macro":
            tier = 1  # High priority - Darius Dale
        else:
            tier = 3  # Standard - YouTube

        # Run transcription
        result = await harvester.process_video(video_url, tier=tier)

        if result and result.get("transcript"):
            # Update raw_content with transcript
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if raw_content:
                metadata = json.loads(raw_content.json_metadata or "{}")
                metadata["transcript"] = result["transcript"]
                metadata["transcription_duration"] = result.get("duration_seconds")
                metadata["transcribed_at"] = datetime.utcnow().isoformat()
                raw_content.json_metadata = json.dumps(metadata)
                raw_content.content_text = result["transcript"]  # Also store as content_text
                db.commit()
                logger.info(f"Transcribed video {raw_content_id}: {len(result['transcript'])} chars")

    except Exception as e:
        logger.error(f"Transcription failed for {raw_content_id}: {e}")
```

### Phase 2: Update TranscriptHarvesterAgent

#### 1. Add yt-dlp support for all platforms

```python
# In agents/transcript_harvester.py

SUPPORTED_PLATFORMS = {
    "zoom": ["zoom.us/rec/", "zoom.us/j/"],
    "webex": ["webex.com/meet/", "webex.com/rec/"],
    "vimeo": ["vimeo.com/", "player.vimeo.com/"],
    "youtube": ["youtube.com/watch", "youtu.be/"],
}

def _extract_audio(self, video_url: str) -> Optional[Path]:
    """Extract audio from video URL using yt-dlp."""
    audio_dir = self.downloads_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_path = audio_dir / f"{timestamp}_audio.mp3"

    try:
        result = subprocess.run([
            "yt-dlp",
            "-x",                          # Extract audio only
            "--audio-format", "mp3",       # Convert to MP3
            "-o", str(audio_path),         # Output path
            "--no-playlist",               # Single video only
            "--quiet",                     # Suppress output
            video_url
        ], capture_output=True, text=True, timeout=600)  # 10 min timeout

        if result.returncode == 0 and audio_path.exists():
            return audio_path
        else:
            logger.warning(f"yt-dlp failed: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"yt-dlp timed out for {video_url}")
        return None
```

#### 2. Add Whisper transcription (local or API)

```python
def _transcribe_audio(self, audio_path: Path, use_api: bool = False) -> Optional[str]:
    """Transcribe audio file using Whisper."""
    try:
        if use_api and self.openai_api_key:
            # Use Whisper API
            with open(audio_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
                return transcript.text
        else:
            # Use local Whisper
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path), language="en")
            return result["text"]

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return None
```

### Phase 3: Handle Async Transcription

Since transcription can take several minutes, run it in a thread pool:

```python
# In backend/routes/collect.py

from concurrent.futures import ThreadPoolExecutor
import asyncio

# Create thread pool for transcription
transcription_executor = ThreadPoolExecutor(max_workers=2)

async def _transcribe_video_async(db_session_factory, raw_content_id: int, video_url: str, source: str):
    """Run transcription in thread pool to not block event loop."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        transcription_executor,
        _transcribe_video_sync,
        db_session_factory,
        raw_content_id,
        video_url,
        source
    )
```

## Data Flow

```
Video Collected (Discord/42macro/YouTube)
    ↓
Save to database (URL, metadata)
    ↓
Trigger async transcription task
    ↓
yt-dlp extracts audio to temp MP3
    ↓
Whisper transcribes audio
    ↓
Update database with transcript
    ↓
Delete temp audio file
    ↓
Content ready for AI analysis
```

## Transcript Storage Format

```json
{
  "content_type": "video",
  "content_text": "Full transcript text here...",
  "url": "https://vimeo.com/1234567",
  "metadata": {
    "video_id": "1234567",
    "platform": "vimeo",
    "title": "Around The Horn - November 29, 2025",
    "transcript": "Full transcript text here...",
    "transcription_duration": 1847,
    "transcribed_at": "2025-12-03T19:00:00Z"
  }
}
```

## Error Handling

| Scenario | Action |
|----------|--------|
| yt-dlp fails (auth required, expired) | Log warning, keep URL without transcript |
| yt-dlp times out (>10 min) | Log error, skip transcription |
| Whisper fails | Log error, keep URL without transcript |
| Empty transcript | Log warning, store empty result |
| Duplicate video | Skip (handled by PRD-019 dedup) |

## Cost Estimate

**Per video (Whisper API):**
- Average video: 20 minutes
- Cost: $0.006/min × 20 = $0.12 per video

**Current collection:**
- Discord videos: ~5 per week
- 42 Macro videos: ~4 per week
- YouTube videos: ~10 per week
- **Weekly cost: ~$2.30**

**Alternative (Local Whisper):**
- Free but slower
- Requires GPU for reasonable speed
- ~5 min processing per 20-min video on CPU

## Testing Plan

1. Install dependencies:
   ```bash
   pip install yt-dlp openai-whisper
   ```

2. Test yt-dlp manually:
   ```bash
   yt-dlp -x --audio-format mp3 -o test.mp3 "https://vimeo.com/1141678913"
   ```

3. Test local Whisper:
   ```python
   import whisper
   model = whisper.load_model("base")
   result = model.transcribe("test.mp3")
   print(result["text"])
   ```

4. Run collection and verify transcripts saved

5. Check synthesis includes video content

## Implementation Checklist

- [ ] Install yt-dlp: `pip install yt-dlp`
- [ ] Verify ffmpeg installed
- [ ] Update `TranscriptHarvesterAgent` with yt-dlp extraction
- [ ] Add `_transcribe_video()` to collect.py
- [ ] Wire into `/api/collect/discord` endpoint
- [ ] Wire into `/api/collect/42macro` endpoint
- [ ] Add thread pool for async transcription
- [ ] Test with Discord Zoom link
- [ ] Test with 42 Macro Vimeo video
- [ ] Test with YouTube video
- [ ] Verify transcripts appear in synthesis
- [ ] Update CHANGELOG

## Success Criteria

- [ ] Videos from all 3 sources are automatically transcribed
- [ ] Transcripts stored in database within 5 minutes of collection
- [ ] Temp audio files cleaned up after transcription
- [ ] Synthesis agent can access and summarize video content
- [ ] No blocking of collection process

## Estimated Effort

| Task | Estimate |
|------|----------|
| Update TranscriptHarvesterAgent | 1 hour |
| Wire into collection endpoints | 30 min |
| Async thread pool handling | 30 min |
| Testing all platforms | 1 hour |
| **Total** | ~3 hours |
