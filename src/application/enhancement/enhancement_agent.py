"""LangGraph-based enhancement agent

This module implements a simple LangGraph agent for enhancing transcriptions
using a local LLM.
"""
from typing import Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
from .llm_client import LLMClient
from .prompts import ENHANCEMENT_SYSTEM_PROMPT, ENHANCEMENT_USER_PROMPT_TEMPLATE


class EnhancementState(TypedDict):
    """State for the enhancement agent"""
    transcription: str
    language: Optional[str]
    enhanced_text: str
    error: Optional[str]


class EnhancementAgent:
    """
    LangGraph agent for enhancing transcriptions.

    This is a simple single-step agent that:
    1. Takes transcription text as input
    2. Formats prompt with enhancement instructions
    3. Calls LLM for enhancement
    4. Returns enhanced text or error
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize enhancement agent.

        Args:
            llm_client: LLM client instance for making API calls
        """
        self.llm_client = llm_client
        self.graph = self._build_graph()

    def _build_graph(self):
        """
        Build LangGraph workflow.

        Creates a simple single-node graph that performs the enhancement.

        Returns:
            Compiled LangGraph workflow
        """
        # Create graph with state
        workflow = StateGraph(EnhancementState)

        # Add enhancement node
        workflow.add_node("enhance", self._enhance_node)

        # Set entry point
        workflow.set_entry_point("enhance")

        # End after enhancement
        workflow.add_edge("enhance", END)

        # Compile and return
        return workflow.compile()

    async def _enhance_node(self, state: EnhancementState) -> EnhancementState:
        """
        Enhancement node - calls LLM with prompt.

        Args:
            state: Current agent state

        Returns:
            Updated state with enhanced text or error
        """
        try:
            # Format user prompt with transcription
            user_prompt = ENHANCEMENT_USER_PROMPT_TEMPLATE.format(
                transcription=state["transcription"]
            )

            # Call LLM
            enhanced_text = await self.llm_client.complete(
                system_prompt=ENHANCEMENT_SYSTEM_PROMPT,
                user_prompt=user_prompt
            )

            # Return updated state
            return {
                **state,
                "enhanced_text": enhanced_text,
                "error": None
            }

        except Exception as e:
            # Capture error in state
            return {
                **state,
                "enhanced_text": "",
                "error": str(e)
            }

    async def enhance(
        self,
        transcription: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance transcription text.

        Args:
            transcription: Original transcription text from Whisper
            language: Optional language code (e.g., 'en', 'es')

        Returns:
            Dictionary with 'enhanced_text' and 'metadata'

        Raises:
            Exception: If enhancement fails
        """
        # Create initial state
        initial_state: EnhancementState = {
            "transcription": transcription,
            "language": language,
            "enhanced_text": "",
            "error": None
        }

        # Run graph
        final_state = await self.graph.ainvoke(initial_state)

        # Check for errors
        if final_state.get("error"):
            raise Exception(final_state["error"])

        # Return results
        return {
            "enhanced_text": final_state["enhanced_text"],
            "metadata": {
                "language": language,
                "original_length": len(transcription),
                "enhanced_length": len(final_state["enhanced_text"])
            }
        }
