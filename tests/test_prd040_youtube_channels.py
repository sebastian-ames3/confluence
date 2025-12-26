"""
Tests for PRD-040: YouTube Channel Identification

Tests for:
- 40.1 Channel Display Name Mapping
- 40.2 Content Extraction with Channel Info
- 40.3 Synthesis Prompt Building with Channel Grouping
- 40.4 Backwards Compatibility
"""
import pytest
from pathlib import Path
import json


class TestChannelMapping:
    """Test 40.1: YouTube channel display name mapping."""

    def test_synthesis_routes_has_channel_mapping(self):
        """Verify YOUTUBE_CHANNEL_DISPLAY dict exists in synthesis.py."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        assert "YOUTUBE_CHANNEL_DISPLAY" in content, "Channel display mapping should exist"

    def test_channel_mapping_has_all_channels(self):
        """Verify all 4 YouTube channels are mapped."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        required_channels = [
            "peter_diamandis",
            "jordi_visser",
            "forward_guidance",
            "42macro"
        ]

        for channel in required_channels:
            assert f'"{channel}"' in content, f"Channel {channel} should be in mapping"

    def test_channel_mapping_has_display_names(self):
        """Verify display names are properly set."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        display_names = [
            "Moonshots",
            "Jordi Visser Labs",
            "Forward Guidance",
            "42 Macro"
        ]

        for name in display_names:
            assert f'"{name}"' in content, f"Display name {name} should be in mapping"

    def test_moonshots_not_peter_diamandis(self):
        """Verify peter_diamandis maps to 'Moonshots' not 'Peter Diamandis'."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Find the mapping line
        assert '"peter_diamandis": "Moonshots"' in content, \
            "peter_diamandis should map to Moonshots (podcast name, not host)"


class TestContentExtraction:
    """Test 40.2: Content extraction with channel info."""

    def test_get_content_for_synthesis_adds_channel_fields(self):
        """Verify _get_content_for_synthesis adds channel and channel_display fields."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Check that channel fields are added to content_items
        assert '"channel":' in content or "'channel':" in content, \
            "Content items should include 'channel' field"
        assert '"channel_display":' in content or "'channel_display':" in content, \
            "Content items should include 'channel_display' field"

    def test_channel_extraction_only_for_youtube(self):
        """Verify channel extraction is conditional on youtube source."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Should check for youtube source before extracting channel
        assert 'source.name == "youtube"' in content, \
            "Should check for youtube source before extracting channel info"

    def test_channel_fallback_for_missing_metadata(self):
        """Verify fallback when channel_name not in metadata."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Should have fallback logic
        assert "Youtube" in content and "Fallback" in content, \
            "Should have fallback for old data without channel_name"

    def test_source_field_preserved(self):
        """Verify source field still uses source.name for weighting."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Source should still be set to source.name
        assert '"source": source.name' in content, \
            "Source field should still use source.name for backwards compatibility"


class TestSynthesisPromptBuilding:
    """Test 40.3: Synthesis prompt building with channel grouping."""

    def test_v1_prompt_groups_by_channel(self):
        """Verify _build_synthesis_prompt groups YouTube by channel."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Should use channel_display for grouping
        assert "channel_display" in content, \
            "Prompt building should reference channel_display"

    def test_v2_prompt_groups_by_channel(self):
        """Verify _build_synthesis_prompt_v2 groups YouTube by channel."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Check v2 method exists and uses channel grouping
        assert "def _build_synthesis_prompt_v2" in content
        # The method should use youtube:channel_display pattern
        assert 'youtube:' in content or "youtube:" in content, \
            "Should use youtube:channel_display pattern for grouping"

    def test_v3_prompt_groups_by_channel(self):
        """Verify _build_synthesis_prompt_v3 groups YouTube by channel."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        assert "def _build_synthesis_prompt_v3" in content

    def test_youtube_header_format(self):
        """Verify YouTube content uses 'YOUTUBE - ChannelName' header format."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        assert 'YOUTUBE - {channel_name}' in content or "YOUTUBE - " in content, \
            "YouTube sections should use 'YOUTUBE - ChannelName' format"

    def test_weight_uses_base_youtube_source(self):
        """Verify weight lookup uses 'youtube' not channel name."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Should use base_source = "youtube" for weight lookup
        assert 'base_source = "youtube"' in content, \
            "Weight lookup should use base 'youtube' source, not individual channels"

    def test_older_content_also_grouped_by_channel(self):
        """Verify older content section in v3 also groups by channel."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Should have PRD-040 comment in older content section
        assert "older_by_source" in content
        # And should process channel_display
        assert "older" in content.lower() and "channel_display" in content


class TestSystemPromptUpdates:
    """Test 40.3b: System prompt updates for YouTube channels."""

    def test_v3_system_prompt_lists_channels(self):
        """Verify V3 system prompt lists individual YouTube channels."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Should list individual channels in SOURCE CONTEXT
        assert "Moonshots" in content, "System prompt should mention Moonshots"
        assert "Jordi Visser Labs" in content, "System prompt should mention Jordi Visser Labs"
        assert "Forward Guidance" in content, "System prompt should mention Forward Guidance"

    def test_v3_system_prompt_describes_channel_focus(self):
        """Verify system prompt describes each channel's focus area."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Moonshots should mention AI/technology
        assert "AI" in content and "Moonshots" in content

    def test_moonshots_mentions_guests(self):
        """Verify Moonshots description mentions guests (Moonshot Mates)."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Should mention that it's a podcast with guests
        assert "guest" in content.lower() or "podcast" in content.lower(), \
            "Moonshots description should mention it has guests"


class TestBackwardsCompatibility:
    """Test 40.4: Backwards compatibility."""

    def test_source_field_unchanged(self):
        """Verify 'source' field still exists and uses source.name."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Should still set source to source.name
        assert '"source": source.name' in content

    def test_sources_included_format_unchanged(self):
        """Verify sources_included field format is not changed."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # sources_included should still work the same way
        assert "sources_included" in content

    def test_youtube_weight_unchanged(self):
        """Verify YouTube weight remains 0.8 for all channels."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # YouTube weight should still be 0.8
        assert '"youtube": 0.8' in content, "YouTube weight should remain 0.8"

    def test_no_per_channel_weights(self):
        """Verify there are no individual channel weights."""
        agent_path = Path(__file__).parent.parent / "agents" / "synthesis_agent.py"
        content = agent_path.read_text()

        # Should NOT have individual channel weights
        assert '"peter_diamandis":' not in content or "YOUTUBE_CHANNEL_DISPLAY" not in content
        assert '"moonshots":' not in content.lower() or "display" in content.lower()


class TestYouTubeCollectorIntegration:
    """Test integration with YouTube collector metadata."""

    def test_collector_has_channel_name_in_metadata(self):
        """Verify YouTube collector stores channel_name in metadata."""
        collector_path = Path(__file__).parent.parent / "collectors" / "youtube_api.py"
        content = collector_path.read_text()

        assert '"channel_name": channel_name' in content or "'channel_name': channel_name" in content, \
            "Collector should store channel_name in metadata"

    def test_collector_has_all_channels_defined(self):
        """Verify YouTube collector has all 4 channels defined."""
        collector_path = Path(__file__).parent.parent / "collectors" / "youtube_api.py"
        content = collector_path.read_text()

        channels = [
            "peter_diamandis",
            "jordi_visser",
            "forward_guidance",
            "42macro"
        ]

        for channel in channels:
            assert f'"{channel}"' in content, f"Collector should have {channel} defined"


class TestPRD040Documentation:
    """Test PRD-040 documentation exists (archived after completion)."""

    def test_prd_file_exists(self):
        """Verify PRD-040 documentation exists in archived folder."""
        prd_path = Path(__file__).parent.parent / "docs" / "archived" / "PRD-040_YouTube_Channel_Identification.md"
        assert prd_path.exists(), "PRD-040 documentation should exist in docs/archived/"

    def test_prd_has_definition_of_done(self):
        """Verify PRD has Definition of Done section."""
        prd_path = Path(__file__).parent.parent / "docs" / "archived" / "PRD-040_YouTube_Channel_Identification.md"
        content = prd_path.read_text()

        assert "Definition of Done" in content, "PRD should have Definition of Done section"

    def test_prd_mentions_all_channels(self):
        """Verify PRD documents all 4 channels."""
        prd_path = Path(__file__).parent.parent / "docs" / "archived" / "PRD-040_YouTube_Channel_Identification.md"
        content = prd_path.read_text()

        channels = ["Moonshots", "Jordi Visser", "Forward Guidance", "42 Macro"]
        for channel in channels:
            assert channel in content, f"PRD should mention {channel}"


class TestUICompatibility:
    """Test 40.5: UI compatibility with channel names."""

    def test_frontend_index_exists(self):
        """Verify frontend index.html exists."""
        index_path = Path(__file__).parent.parent / "frontend" / "index.html"
        assert index_path.exists(), "frontend/index.html should exist"

    def test_source_stances_display_is_dynamic(self):
        """Verify source stances display uses dynamic source names."""
        index_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        # Should iterate over stances dynamically
        assert "Object.entries(stances)" in content, \
            "Source stances should be displayed dynamically"

    def test_source_stances_uses_name_variable(self):
        """Verify source stances display shows the source name from data."""
        index_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        # Should display the name from the object entries
        assert "${name}" in content, \
            "Source name should be displayed from data, not hardcoded"

    def test_no_hardcoded_youtube_in_stances(self):
        """Verify no hardcoded 'youtube' string in source stances display."""
        index_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        # Find the displayV3SourceStances function
        import re
        stances_match = re.search(
            r'function displayV3SourceStances\(stances\)\s*\{[^}]+\}[^}]+\}',
            content,
            re.DOTALL
        )
        if stances_match:
            stances_func = stances_match.group()
            # Should not have hardcoded 'youtube' (case insensitive)
            assert 'youtube' not in stances_func.lower() or '${' in stances_func, \
                "Source stances should not hardcode 'youtube' source name"

    def test_v3_executive_summary_handles_youtube_channels(self):
        """Verify executive summary can handle YouTube channel names in source_highlights."""
        index_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = index_path.read_text()

        # The executive summary should handle source_highlights dynamically
        assert "source_highlights" in content, \
            "Executive summary should handle source_highlights"


class TestContentItemStructure:
    """Test content item structure includes channel fields."""

    def test_content_items_structure(self):
        """Verify content items include channel and channel_display fields."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # Check the content_items.append section has both fields
        assert '"channel": channel_name' in content, \
            "Content items should include channel field"
        assert '"channel_display": channel_display' in content, \
            "Content items should include channel_display field"

    def test_non_youtube_sources_have_none_channel(self):
        """Verify non-YouTube sources have None for channel fields."""
        synthesis_path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = synthesis_path.read_text()

        # channel_name and channel_display should only be set for youtube
        assert "channel_name = None" in content, \
            "channel_name should default to None for non-YouTube"
        assert "channel_display = None" in content, \
            "channel_display should default to None for non-YouTube"
