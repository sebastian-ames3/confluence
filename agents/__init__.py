"""
Macro Confluence Hub - AI Sub-Agents Package

This package contains specialized AI agents for content analysis and confluence scoring.
Each agent is a focused module that uses the Claude API for specific analysis tasks.
"""

__version__ = "0.2.0"

from agents.base_agent import BaseAgent
from agents.synthesis_agent import SynthesisAgent, generate_synthesis

__all__ = [
    "BaseAgent",
    "SynthesisAgent",
    "generate_synthesis",
]
