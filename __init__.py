"""
Web Operator Agent - LangGraph + FastAPI Implementation

A sophisticated web automation agent inspired by OpenAI's Operator,
built with LangGraph for agent orchestration and FastAPI for the API layer.

Features:
- Browser automation with Playwright
- Computer vision for web element detection
- Multi-step task execution
- Safety guardrails and user confirmation
- Real-time task monitoring
- Secure credential handling

Author: AI Assistant
Created: June 2025
"""

from .core.config import settings
from .api.main import app

__version__ = "1.0.0"
__author__ = "AI Assistant"

# Export main components
__all__ = ["app", "settings"]
