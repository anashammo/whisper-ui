"""LLM client using OpenAI-compatible API

This module provides a client for communicating with local LLMs
that expose an OpenAI-compatible API (like Ollama, LM Studio).
"""
from typing import Dict, Any, Optional
import httpx
from openai import AsyncOpenAI


class LLMClient:
    """
    Client for communicating with local LLM via OpenAI-compatible API.

    Supports any local LLM server that implements the OpenAI chat completions
    API format (Ollama with openai-compatible endpoint, LM Studio, etc.)
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 60,
        temperature: float = 0.3
    ):
        """
        Initialize LLM client.

        Args:
            base_url: Base URL for LLM API (e.g., http://localhost:11434/v1)
            model: Model name (e.g., llama3, mistral)
            timeout: Request timeout in seconds
            temperature: Sampling temperature (0.0-1.0, lower = more focused)
        """
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key="not-needed",  # Local LLMs don't require API key
            timeout=httpx.Timeout(timeout, connect=10.0)
        )
        self.model = model
        self.temperature = temperature

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048
    ) -> str:
        """
        Get completion from LLM.

        Args:
            system_prompt: System message defining role and behavior
            user_prompt: User message with the actual request
            max_tokens: Maximum tokens in response

        Returns:
            LLM response text

        Raises:
            Exception: If API call fails (connection error, timeout, etc.)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
                # Additional parameters to reduce token waste
                frequency_penalty=0.5,  # Reduce repetition
                presence_penalty=0.3,   # Encourage conciseness
                top_p=0.9              # Focus on high-probability tokens
            )

            # Extract only the content, ignoring any reasoning field
            return response.choices[0].message.content.strip()

        except httpx.ConnectError as e:
            raise Exception(
                f"Failed to connect to LLM server at {self.client.base_url}. "
                f"Is the LLM server running? Error: {str(e)}"
            )
        except httpx.TimeoutException as e:
            raise Exception(
                f"LLM request timed out after {self.client.timeout.read}s. "
                f"The model may be too slow or the text too long. Error: {str(e)}"
            )
        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
