# PRD-018: Discord Video Transcription

## Overview
Extend the Discord collector to automatically extract audio from Zoom/Webex recording links using yt-dlp, transcribe them using Whisper, save the transcript to the database, and delete temporary files afterward.

## Problem Statement
The Discord channels being monitored contain Zoom and Webex recording links with valuable spoken content. Currently, the collector only extracts and stores the URLs - it does not capture the actual content from these recordings.

**Why yt-dlp?**
Zoom/Webex share links return HTML landing pages, not direct video files. Simple HTTP downloads don't work. yt-dlp is purpose-built to handle these platforms - it navigates the landing pages internally and extracts the actual media stream.

## Goals
1. Automatically transcribe Zoom/Webex recordings found in Discord messages
2. Store transcripts in the database alongside the message metadata
3. Clean up temporary audio files after transcription to save disk space
4. Integrate seamlessly with the existing scheduled Task Scheduler job

## Non-Goals
- YouTube video transcription (separate collector exists for this)
- Real-time/live meeting transcription
- Speaker diarization (identifying who said what)
- Downloading full video files (audio-only extraction for efficiency)

## Requirements

### Dependencies

| Package | Purpose | Installation |
|---------|---------|--------------|
| ffmpeg | Audio extraction/conversion | `winget install ffmpeg` (already installed) |
| openai-whisper | Speech-to-text transcription | `pip install openai-whisper` (already installed) |
| yt-dlp | Extract audio from Zoom/Webex URLs | `pip install yt-dlp` |

### Configuration

**Whisper:**
- Model: `base` (good balance of speed/accuracy for 10-25 min recordings)
- Language: English (forced)
- Expected transcription time: 1-3 minutes per recording

**yt-dlp:**
- Extract audio only (`-x` flag) - no video download
- Output format: WAV or MP3 (Whisper-compatible)
- Temp directory: `downloads/discord/audio/`

## Implementation

### 1. Install yt-dlp
```bash
pip install yt-dlp
```

### 2. Update `collectors/discord_self.py`

Replace the current `_download_and_transcribe_video()` method with yt-dlp-based extraction:

```python
async def _download_and_transcribe_video(self, video_url: str, platform: str) -> Optional[Dict[str, Any]]:
    """
    Extract audio from Zoom/Webex recording using yt-dlp and transcribe with Whisper.
    """
    if platform == "youtube":
        return None  # Handled by separate collector

    audio_dir = self.download_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_path = audio_dir / f"{timestamp}_{platform}_audio.mp3"

    try:
        # Extract audio using yt-dlp
        result = subprocess.run([
            "yt-dlp",
            "-x",                          # Extract audio only
            "--audio-format", "mp3",       # Convert to MP3
            "-o", str(audio_path),         # Output path
            "--no-playlist",               # Single video only
            "--quiet",                     # Suppress output
            video_url
        ], capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            logger.warning(f"yt-dlp failed: {result.stderr}")
            return None

        # Transcribe with Whisper
        transcript_result = await self._transcribe_audio(audio_path)

        # Clean up audio file
        if audio_path.exists():
            audio_path.unlink()

        if transcript_result:
            transcript_result["platform"] = platform
            transcript_result["url"] = video_url
            transcript_result["transcribed_at"] = datetime.utcnow().isoformat()

        return transcript_result

    except subprocess.TimeoutExpired:
        logger.error(f"yt-dlp timed out for {video_url}")
        return None
    except Exception as e:
        logger.error(f"Failed to extract/transcribe: {e}")
        return None
```

### 3. Transcript Storage Format
```json
{
  "metadata": {
    "video_transcripts": [
      {
        "platform": "zoom",
        "url": "https://zoom.us/rec/share/...",
        "transcript": "Full transcribed text here...",
        "duration_seconds": 1234,
        "transcribed_at": "2025-12-02T18:00:00Z"
      }
    ]
  }
}
```

### 4. Error Handling

| Scenario | Action |
|----------|--------|
| yt-dlp fails (auth required, expired link) | Log warning, store URL without transcript, continue |
| yt-dlp times out (>5 min) | Log error, skip this recording, continue |
| Whisper fails | Log error, continue with other messages |
| Empty transcript | Log warning, store empty result |

### 5. Task Scheduler
- Timeout: **30 minutes** (already configured)
- Handles multiple recordings per run

## Data Flow
```
Discord Message with Zoom Link
    ↓
Extract URL via _extract_video_links()
    ↓
yt-dlp extracts audio to temp MP3 file
    ↓
Whisper transcribes audio (base model, English)
    ↓
Store transcript in message metadata
    ↓
Delete temp audio file
    ↓
Save to database (with transcript)
```

## Testing Plan
1. Install yt-dlp: `pip install yt-dlp`
2. Test yt-dlp manually with a Zoom link:
   ```bash
   yt-dlp -x --audio-format mp3 -o test_audio.mp3 "https://zoom.us/rec/share/..."
   ```
3. Run Discord collector manually
4. Verify transcript appears in database
5. Verify audio file is deleted after transcription
6. Test with expired/invalid link (should fail gracefully)

## Rollback Plan
- Remove yt-dlp calls from discord_self.py
- Uninstall: `pip uninstall yt-dlp`
- Transcription feature disabled, URLs still stored

## Implementation Checklist
1. [x] Install ffmpeg
2. [x] Install openai-whisper
3. [ ] Install yt-dlp
4. [ ] Update `_download_and_transcribe_video()` to use yt-dlp
5. [ ] Rename method to `_extract_and_transcribe_audio()` for clarity
6. [ ] Update `_transcribe_video()` to `_transcribe_audio()`
7. [ ] Test with real Zoom recording
8. [ ] Commit changes

## Estimated Complexity
Low-Medium - yt-dlp handles the hard part (navigating Zoom's pages). We just need to call it and pipe output to Whisper.
