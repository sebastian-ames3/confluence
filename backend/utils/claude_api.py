"""
Claude API Utilities

Helper functions for interacting with the Anthropic Claude API.
To be implemented in Phase 1 (PRD-003).
"""

import os
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# TODO: Implement Claude API helpers
# - Initialize Anthropic client
# - Standard prompt templates
# - Response parsing
# - Error handling and retries
