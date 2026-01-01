"""LLM infrastructure - HTTP clients for local LLM APIs

This package contains clients for communicating with local LLM services
that expose OpenAI-compatible APIs (Ollama, LM Studio, etc.).
"""
from .llm_client import LLMClient

__all__ = ["LLMClient"]
