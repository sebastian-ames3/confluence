"""Central configuration for AI agents."""
import os

# Model configuration - change here to update all agents
MODEL_SYNTHESIS = os.getenv("SYNTHESIS_MODEL", "claude-opus-4-5-20251101")
MODEL_ANALYSIS = os.getenv("ANALYSIS_MODEL", "claude-sonnet-4-20250514")
MODEL_EVALUATION = os.getenv("EVALUATION_MODEL", "claude-sonnet-4-20250514")

# Timeout configuration (seconds)
TIMEOUT_DEFAULT = int(os.getenv("AGENT_TIMEOUT", "120"))
TIMEOUT_SYNTHESIS = int(os.getenv("SYNTHESIS_TIMEOUT_PER_CALL", "300"))

# Token limits (characters)
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "100000"))  # ~25K tokens
MAX_TRANSCRIPT_CHARS = int(os.getenv("MAX_TRANSCRIPT_CHARS", "60000"))  # ~15K tokens
