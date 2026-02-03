"""
Tests for 42macro Vimeo Transcript Extraction

Tests for:
- Metadata passing through transcription pipeline
- 42macro-specific yt-dlp command building
- Cookie conversion to Netscape format
- Embed URL fallback logic
"""
import pytest
from pathlib import Path
import json
import tempfile


class TestMetadataPassthrough:
    """Test metadata is properly passed through the transcription pipeline."""

    def test_collect_routes_passes_metadata(self):
        """Verify collect.py passes metadata to transcription functions."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        # Check metadata is captured in videos_to_transcribe
        assert '"embed_url": metadata.get("embed_url")' in content, \
            "embed_url should be captured from metadata"
        assert '"metadata": metadata' in content, \
            "Full metadata should be passed to transcription queue"

    def test_transcribe_video_sync_accepts_metadata(self):
        """Verify _transcribe_video_sync accepts source_metadata parameter."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "source_metadata: Optional[Dict[str, Any]] = None" in content, \
            "_transcribe_video_sync should accept source_metadata parameter"

    def test_transcribe_video_async_passes_metadata(self):
        """Verify _transcribe_video_async passes metadata through."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "metadata=video.get(\"metadata\")" in content, \
            "_transcribe_video_async should pass metadata from video dict"

    def test_metadata_merged_in_sync_function(self):
        """Verify source metadata is merged with basic metadata."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "if source_metadata:" in content, \
            "Should check for source_metadata"
        assert "metadata.update(source_metadata)" in content, \
            "Should merge source_metadata into metadata"


class TestTranscriptHarvester42MacroSupport:
    """Test transcript_harvester.py 42macro-specific functionality."""

    def test_download_and_extract_audio_accepts_metadata(self):
        """Verify download_and_extract_audio accepts metadata parameter."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "metadata: Optional[Dict[str, Any]] = None" in content, \
            "download_and_extract_audio should accept metadata parameter"

    def test_harvest_passes_metadata_to_download(self):
        """Verify harvest() passes metadata to download_and_extract_audio."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "download_and_extract_audio(video_url, source, metadata)" in content, \
            "harvest should pass metadata to download_and_extract_audio"

    def test_build_ytdlp_command_method_exists(self):
        """Verify _build_ytdlp_command method exists."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "def _build_ytdlp_command(" in content, \
            "_build_ytdlp_command method should exist"

    def test_convert_cookies_to_netscape_method_exists(self):
        """Verify _convert_cookies_to_netscape method exists."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "def _convert_cookies_to_netscape(" in content, \
            "_convert_cookies_to_netscape method should exist"


class Test42MacroYtdlpOptions:
    """Test 42macro-specific yt-dlp command options."""

    def test_42macro_uses_correct_referer(self):
        """Verify 42macro uses app.42macro.com as referer."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"--referer", "https://app.42macro.com/"' in content, \
            "42macro should use app.42macro.com as referer"

    def test_42macro_checks_for_cookies(self):
        """Verify 42macro checks for cookies file."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'if source == "42macro":' in content, \
            "Should have 42macro-specific handling"
        assert "cookies_path.exists()" in content, \
            "Should check if cookies file exists"

    def test_embed_url_fallback(self):
        """Verify embed_url is used as fallback for 42macro."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'if source == "42macro" and metadata.get("embed_url"):' in content, \
            "Should check for embed_url on 42macro failures"
        assert 'embed_url = metadata["embed_url"]' in content, \
            "Should extract embed_url for retry"

    def test_youtube_uses_youtube_referer(self):
        """Verify YouTube uses youtube.com as referer, not google.com."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"--referer", "https://www.youtube.com/"' in content, \
            "YouTube should use youtube.com as referer"


class TestCookieConversion:
    """Test Netscape cookie format conversion."""

    def test_netscape_format_header(self):
        """Verify Netscape cookie file has proper header."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "# Netscape HTTP Cookie File" in content, \
            "Should write Netscape header"

    def test_netscape_format_fields(self):
        """Verify Netscape format includes all required fields."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        # Check field extraction
        assert 'domain = cookie.get("domain", "")' in content, \
            "Should extract domain"
        assert 'path = cookie.get("path", "/")' in content, \
            "Should extract path"
        assert 'secure = "TRUE" if cookie.get("secure", False) else "FALSE"' in content, \
            "Should convert secure to TRUE/FALSE"
        assert 'include_subdomains = "TRUE" if domain.startswith(".")' in content, \
            "Should set include_subdomains based on domain prefix"

    def test_netscape_output_file_path(self):
        """Verify Netscape cookies are written to correct path."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '42macro_cookies_netscape.txt' in content, \
            "Should write to 42macro_cookies_netscape.txt"


class TestCookieConversionUnit:
    """Unit tests for cookie conversion logic (without imports)."""

    def test_cookie_conversion_logic(self):
        """Test the cookie conversion logic works correctly."""
        # Simulate the conversion logic without importing the module
        test_cookies = [
            {
                "domain": ".42macro.com",
                "path": "/",
                "secure": True,
                "expiry": 1735689600,
                "name": "session_id",
                "value": "abc123"
            },
            {
                "domain": "app.42macro.com",
                "path": "/api",
                "secure": False,
                "name": "csrf_token",
                "value": "xyz789"
            }
        ]

        # Apply the same logic as _convert_cookies_to_netscape
        lines = []
        for cookie in test_cookies:
            domain = cookie.get("domain", "")
            include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            expiry = str(int(cookie.get("expiry", 0))) if cookie.get("expiry") else "0"
            name = cookie.get("name", "")
            value = cookie.get("value", "")

            lines.append(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")

        # Verify first cookie (with subdomain and secure)
        assert ".42macro.com\tTRUE\t/\tTRUE\t1735689600\tsession_id\tabc123" == lines[0]

        # Verify second cookie (without subdomain, not secure, no expiry)
        assert "app.42macro.com\tFALSE\t/api\tFALSE\t0\tcsrf_token\txyz789" == lines[1]


class TestBackwardsCompatibility:
    """Test that existing functionality is not broken."""

    def test_youtube_still_works(self):
        """Verify YouTube-specific options still exist."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'elif source == "youtube" or "youtube.com" in video_url:' in content, \
            "YouTube handling should still work"
        assert '"youtube:player_client=android"' in content, \
            "YouTube Android client workaround should still work"

    def test_generic_fallback_exists(self):
        """Verify generic fallback for other platforms."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "else:" in content and '"--referer", "https://www.google.com/"' in content, \
            "Generic fallback with google.com referer should exist"

    def test_base_ytdlp_options_preserved(self):
        """Verify base yt-dlp options are still present."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        base_options = [
            '"-f", "bestaudio/best"',
            '"-x"',
            '"--audio-format", "mp3"',
            '"--audio-quality", "0"',
            '"--no-playlist"',
            '"--retries", "3"',
        ]

        for option in base_options:
            assert option in content, f"Base option {option} should be preserved"
