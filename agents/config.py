"""Central configuration for AI agents."""
import os

# Model configuration - change here to update all agents
MODEL_SYNTHESIS = os.getenv("SYNTHESIS_MODEL", "claude-opus-4-6")
MODEL_ANALYSIS = os.getenv("ANALYSIS_MODEL", "claude-sonnet-4-20250514")
MODEL_EVALUATION = os.getenv("EVALUATION_MODEL", "claude-sonnet-4-20250514")

# Timeout configuration (seconds)
TIMEOUT_DEFAULT = int(os.getenv("AGENT_TIMEOUT", "120"))
TIMEOUT_SYNTHESIS = int(os.getenv("SYNTHESIS_TIMEOUT_PER_CALL", "300"))

# Token limits (characters)
MAX_SOURCE_TOKENS = int(os.getenv("MAX_SOURCE_TOKENS", "8000"))
MAX_TRANSCRIPT_CHARS = int(os.getenv("MAX_TRANSCRIPT_CHARS", "60000"))  # ~15K tokens
MAX_SOURCE_PROMPT_CHARS = int(os.getenv("MAX_SOURCE_PROMPT_CHARS", "150000"))  # ~37K tokens
