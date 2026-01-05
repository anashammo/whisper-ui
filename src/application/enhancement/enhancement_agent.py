"""LangGraph-based enhancement agent

This module implements a simple LangGraph agent for enhancing transcriptions
using a local LLM.

Supports language-specific enhancement:
- Standard enhancement for most languages (grammar, punctuation, filler removal)
- Arabic-specific enhancement with full Tashkeel (diacritization) support
"""
from typing import Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
from ...infrastructure.llm.llm_client import LLMClient
from .prompts import get_system_prompt, get_user_prompt


class EnhancementState(TypedDict):
    """State for the enhancement agent"""
    transcription: str
    language: Optional[str]
    enable_tashkeel: bool  # Whether to add Arabic diacritics
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

        Selects appropriate prompt based on language and Tashkeel setting:
        - Arabic with Tashkeel enabled: Full diacritization + grammar enhancement
        - Other cases: Standard grammar/punctuation/filler removal

        Args:
            state: Current agent state

        Returns:
            Updated state with enhanced text or error
        """
        try:
            transcription = state["transcription"]
            language = state.get("language")
            enable_tashkeel = state.get("enable_tashkeel", False)

            # Get appropriate prompts based on language and Tashkeel setting
            # For Arabic with Tashkeel: includes full diacritization instructions
            # For others: standard grammar/punctuation/filler removal
            system_prompt = get_system_prompt(
                language=language,
                text=transcription,
                enable_tashkeel=enable_tashkeel
            )
            user_prompt = get_user_prompt(
                transcription=transcription,
                language=language,
                enable_tashkeel=enable_tashkeel
            )

            # Call LLM
            enhanced_text = await self.llm_client.complete(
                system_prompt=system_prompt,
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
        language: Optional[str] = None,
        enable_tashkeel: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance transcription text.

        Args:
            transcription: Original transcription text from Whisper
            language: Optional language code (e.g., 'en', 'es', 'ar')
            enable_tashkeel: Whether to add Arabic diacritics (only applies if text is Arabic)

        Returns:
            Dictionary with 'enhanced_text' and 'metadata'

        Raises:
            Exception: If enhancement fails
        """
        # Create initial state
        initial_state: EnhancementState = {
            "transcription": transcription,
            "language": language,
            "enable_tashkeel": enable_tashkeel,
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
                "enable_tashkeel": enable_tashkeel,
                "original_length": len(transcription),
                "enhanced_length": len(final_state["enhanced_text"])
            }
        }
