"""
Tests for PRD-042: Transcription LLM Update

Tests for:
- AssemblyAI transcription integration with speaker diarization
- Claude model update to Sonnet 4.5
- Whisper fallback logic
- Speaker attribution in analysis
- Backwards compatibility
"""
import pytest
from pathlib import Path


class TestClaudeModelUpdate:
    """Test Claude model has been updated to Sonnet 4.5 across all agents."""

    def test_base_agent_default_model_uses_config(self):
        """BaseAgent should use MODEL_ANALYSIS from agents/config.py."""
        base_agent_path = Path(__file__).parent.parent / "agents" / "base_agent.py"
        content = base_agent_path.read_text()

        assert "MODEL_ANALYSIS" in content, \
            "BaseAgent should import MODEL_ANALYSIS from agents.config"

        config_path = Path(__file__).parent.parent / "agents" / "config.py"
        config_content = config_path.read_text()
        assert "claude-sonnet-4-20250514" in config_content, \
            "agents/config.py should define the default Sonnet model"

    def test_transcript_harvester_uses_sonnet_4(self):
        """TranscriptHarvesterAgent should use claude-sonnet-4-20250514."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'model: str = "claude-sonnet-4-20250514"' in content, \
            "TranscriptHarvesterAgent should use claude-sonnet-4-20250514"

    def test_no_invalid_model_references_in_agents(self):
        """No agent files should reference the invalid claude-sonnet-4-5-20250514 model."""
        agents_dir = Path(__file__).parent.parent / "agents"

        for agent_file in agents_dir.glob("*.py"):
            content = agent_file.read_text(encoding='utf-8')
            assert "claude-sonnet-4-5-20250514" not in content, \
                f"{agent_file.name} references invalid model claude-sonnet-4-5-20250514"

    def test_all_agents_updated_to_sonnet_4(self):
        """All agent files with model parameters should use Sonnet 4 (except synthesis which uses Opus)."""
        agents_dir = Path(__file__).parent.parent / "agents"
        # Agents that should use Sonnet 4 for cost efficiency
        agents_with_sonnet = [
            "base_agent.py",
            "transcript_harvester.py",
            "confluence_scorer.py",
            "cross_reference.py",
            "pdf_analyzer.py",
            "image_intelligence.py",
            "symbol_level_extractor.py",
            "visual_content_classifier.py",
        ]

        for agent_name in agents_with_sonnet:
            agent_path = agents_dir / agent_name
            if agent_path.exists():
                content = agent_path.read_text()
                if "model: str =" in content:
                    assert "claude-sonnet-4-20250514" in content, \
                        f"{agent_name} should use claude-sonnet-4-20250514"

    def test_synthesis_agent_uses_opus_via_config(self):
        """Synthesis agent should use MODEL_SYNTHESIS from agents/config.py (Opus)."""
        agents_dir = Path(__file__).parent.parent / "agents"
        synthesis_path = agents_dir / "synthesis_agent.py"
        content = synthesis_path.read_text(encoding='utf-8')
        assert "MODEL_SYNTHESIS" in content, \
            "synthesis_agent.py should import MODEL_SYNTHESIS from agents.config"

        config_path = agents_dir / "config.py"
        config_content = config_path.read_text()
        assert "claude-opus-4-6" in config_content, \
            "agents/config.py should define the default Opus model for synthesis"


class TestAssemblyAIDependency:
    """Test AssemblyAI dependency is properly configured."""

    def test_assemblyai_in_requirements(self):
        """AssemblyAI package should be in requirements.txt."""
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        content = requirements_path.read_text()

        assert "assemblyai" in content, \
            "assemblyai should be in requirements.txt"
        assert "assemblyai>=0.30.0" in content, \
            "assemblyai should have version constraint >=0.30.0"


class TestAssemblyAIClientInitialization:
    """Test AssemblyAI client is properly initialized."""

    def test_assemblyai_api_key_checked(self):
        """Transcript harvester should check for ASSEMBLYAI_API_KEY env var."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'os.getenv("ASSEMBLYAI_API_KEY")' in content, \
            "Should check for ASSEMBLYAI_API_KEY environment variable"

    def test_assemblyai_client_attribute_exists(self):
        """Transcript harvester should have assemblyai_client attribute."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "self.assemblyai_client" in content, \
            "Should have assemblyai_client attribute"

    def test_assemblyai_transcriber_created(self):
        """AssemblyAI Transcriber should be created when key is available."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "aai.Transcriber()" in content, \
            "Should create AssemblyAI Transcriber"

    def test_fallback_message_when_no_key(self):
        """Should log message when ASSEMBLYAI_API_KEY is not set."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "ASSEMBLYAI_API_KEY not found" in content or "using Whisper as primary" in content, \
            "Should log fallback message when key not found"


class TestAssemblyAITranscription:
    """Test AssemblyAI transcription method implementation."""

    def test_transcribe_assemblyai_method_exists(self):
        """_transcribe_assemblyai method should exist."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "async def _transcribe_assemblyai(" in content, \
            "_transcribe_assemblyai method should exist"

    def test_speaker_diarization_enabled(self):
        """Speaker diarization should be enabled in AssemblyAI config."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "speaker_labels=True" in content, \
            "Speaker diarization should be enabled"

    def test_transcription_config_created(self):
        """TranscriptionConfig should be created with speaker labels."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "aai.TranscriptionConfig(" in content, \
            "Should create TranscriptionConfig"

    def test_utterances_converted_to_segments(self):
        """AssemblyAI utterances should be converted to segment format."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "transcript.utterances" in content, \
            "Should access transcript.utterances"
        assert '"speaker": utterance.speaker' in content, \
            "Should include speaker in segment"

    def test_timestamps_converted_from_ms(self):
        """Timestamps should be converted from milliseconds to seconds."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "utterance.start / 1000" in content, \
            "Should convert start from ms to seconds"
        assert "utterance.end / 1000" in content, \
            "Should convert end from ms to seconds"

    def test_speaker_count_included(self):
        """Response should include speaker_count metadata."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"speaker_count":' in content, \
            "Should include speaker_count in response"

    def test_transcription_provider_included(self):
        """Response should include transcription_provider metadata."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"transcription_provider": "assemblyai"' in content, \
            "AssemblyAI response should include provider metadata"


class TestWhisperFallback:
    """Test Whisper fallback logic."""

    def test_transcribe_whisper_method_exists(self):
        """_transcribe_whisper method should exist."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "async def _transcribe_whisper(" in content, \
            "_transcribe_whisper method should exist"

    def test_whisper_used_when_no_assemblyai_client(self):
        """Whisper should be used when AssemblyAI client is not available."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "if self.assemblyai_client:" in content, \
            "Should check if AssemblyAI client is available"
        assert "return await self._transcribe_whisper(audio_file)" in content, \
            "Should fall back to Whisper"

    def test_whisper_fallback_on_assemblyai_failure(self):
        """Whisper should be used when AssemblyAI fails."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "AssemblyAI transcription failed, falling back to Whisper" in content, \
            "Should log fallback message on AssemblyAI failure"

    def test_whisper_provider_metadata(self):
        """Whisper response should include provider metadata."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"transcription_provider": "whisper"' in content, \
            "Whisper response should include provider metadata"

    def test_chunked_transcription_preserved(self):
        """_transcribe_chunked method should still exist for large files."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "async def _transcribe_chunked(" in content, \
            "_transcribe_chunked should still exist for Whisper large files"


class TestSpeakerDiarizationInAnalysis:
    """Test speaker diarization is handled in transcript analysis."""

    def test_speaker_detection_check(self):
        """Analysis should check for speaker presence in segments."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'any(seg.get("speaker") for seg in segments)' in content or \
               'any(seg.get("speaker")' in content, \
            "Should check for speaker presence in segments"

    def test_speaker_instruction_added_when_speakers_present(self):
        """Speaker-specific instructions should be added when speakers detected."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert "speaker diarization" in content.lower(), \
            "Should mention speaker diarization in instructions"
        assert "Speaker A" in content or "speaker label" in content.lower(), \
            "Should instruct about speaker labels"

    def test_key_quotes_schema_includes_speaker(self):
        """key_quotes schema should support optional speaker field."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"speaker"' in content and '"timestamp"' in content and '"text"' in content, \
            "key_quotes schema should include speaker field"

    def test_speaker_count_added_to_analysis(self):
        """Analysis response should include speaker_count when available."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert 'analysis["speaker_count"]' in content, \
            "Analysis should add speaker_count to response"


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing transcripts."""

    def test_analysis_works_without_speakers(self):
        """Analysis should work with transcripts that don't have speaker labels."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        # Check that speaker instruction is conditionally added
        assert "if has_speakers:" in content, \
            "Speaker instruction should be conditional"

    def test_whisper_output_format_unchanged(self):
        """Whisper output should maintain compatibility with existing format."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        # Whisper output should have text, segments, duration
        assert '"text":' in content, "Should include text field"
        assert '"segments":' in content, "Should include segments field"
        assert '"duration":' in content, "Should include duration field"

    def test_existing_harvest_interface_unchanged(self):
        """harvest() method signature should remain unchanged."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        # harvest should still accept video_url, source, metadata, priority
        assert "async def harvest(" in content, "harvest method should exist"
        assert "video_url: str" in content, "harvest should accept video_url"
        assert "source: str" in content, "harvest should accept source"
        assert "metadata: Optional[Dict[str, Any]]" in content, "harvest should accept metadata"
        assert "priority: str" in content, "harvest should accept priority"


class TestSegmentFormat:
    """Test segment format consistency between providers."""

    def test_assemblyai_segments_have_id(self):
        """AssemblyAI segments should include id field."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        # Check _transcribe_assemblyai creates segments with id
        assert '"id": i' in content, \
            "AssemblyAI segments should include id field"

    def test_assemblyai_segments_have_start_end(self):
        """AssemblyAI segments should include start and end fields."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"start": utterance.start / 1000' in content, \
            "AssemblyAI segments should include start field"
        assert '"end": utterance.end / 1000' in content, \
            "AssemblyAI segments should include end field"

    def test_assemblyai_segments_have_text(self):
        """AssemblyAI segments should include text field."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"text": utterance.text' in content, \
            "AssemblyAI segments should include text field"

    def test_assemblyai_segments_have_speaker(self):
        """AssemblyAI segments should include speaker field."""
        harvester_path = Path(__file__).parent.parent / "agents" / "transcript_harvester.py"
        content = harvester_path.read_text()

        assert '"speaker": utterance.speaker' in content, \
            "AssemblyAI segments should include speaker field"


class TestLocalScriptCompatibility:
    """Test local script remains compatible with new implementation."""

    def test_local_script_uses_transcript_harvester(self):
        """Local script should use TranscriptHarvesterAgent."""
        local_script = Path(__file__).parent.parent / "dev" / "scripts" / "macro42_local.py"
        if local_script.exists():
            content = local_script.read_text()

            assert "TranscriptHarvesterAgent" in content, \
                "Local script should use TranscriptHarvesterAgent"


class TestPRD042Documentation:
    """Test PRD-042 is properly documented."""

    def test_prd042_file_exists(self):
        """PRD-042 document should exist."""
        prd_path = Path(__file__).parent.parent / "docs" / "PRD-042_Transcription_LLM_Update.md"

        assert prd_path.exists(), \
            "PRD-042_Transcription_LLM_Update.md should exist"

    def test_prd042_mentions_assemblyai(self):
        """PRD-042 should document AssemblyAI integration."""
        prd_path = Path(__file__).parent.parent / "docs" / "PRD-042_Transcription_LLM_Update.md"
        content = prd_path.read_text()

        assert "AssemblyAI" in content, \
            "PRD-042 should mention AssemblyAI"

    def test_prd042_mentions_speaker_diarization(self):
        """PRD-042 should document speaker diarization."""
        prd_path = Path(__file__).parent.parent / "docs" / "PRD-042_Transcription_LLM_Update.md"
        content = prd_path.read_text()

        assert "speaker" in content.lower() and "diarization" in content.lower(), \
            "PRD-042 should mention speaker diarization"

    def test_prd042_documents_env_var(self):
        """PRD-042 should document ASSEMBLYAI_API_KEY."""
        prd_path = Path(__file__).parent.parent / "docs" / "PRD-042_Transcription_LLM_Update.md"
        content = prd_path.read_text()

        assert "ASSEMBLYAI_API_KEY" in content, \
            "PRD-042 should document ASSEMBLYAI_API_KEY environment variable"
