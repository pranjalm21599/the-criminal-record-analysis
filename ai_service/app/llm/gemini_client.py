"""
Wrapper around Google's Gemini API.

IMPORTANT: this uses the `google-genai` package (`from google import genai`),
NOT the old `google-generativeai` package. The old package is fully
deprecated (its GitHub repo says "EOL Nov 30, 2025") and `gemini-1.5-flash` /
`gemini-2.0-flash`, the models it typically pointed to, have both been shut
down. Installing the old package or using those model names will simply
fail on the day of your demo.

If GEMINI_MODEL in your .env ever starts failing with a 404 "model not
found", swap it for "gemini-flash-latest" (Google's rolling alias to
whatever their current default Flash model is) or check
https://ai.google.dev/gemini-api/docs/models for the current list.
"""
from google import genai
from google.genai import types

from app.config import settings

SYSTEM_INSTRUCTION = """You are CrimeNet AI, an expert criminal network analysis assistant \
for law enforcement investigators.

RULES YOU MUST FOLLOW:
1. Only answer based on the EVIDENCE provided in the context. Never invent facts.
2. If the evidence does not contain the answer, say so plainly: \
"I don't have enough data on this."
3. Always indicate which data source (graph, risk analysis, case records, etc.) \
each part of your answer comes from.
4. Be concise but thorough — investigators are busy.
5. Clearly flag any high-risk finding with an explicit warning."""


class GeminiClient:
    """Thin, testable wrapper. One instance per process is fine — the
    genai.Client is stateless/threadsafe; conversation state for multi-turn
    chat lives in the caller (QAService), not here."""

    MISSING_KEY_MESSAGE = (
        "The AI assistant is not configured: GEMINI_API_KEY is not set. "
        "Get a free key at https://aistudio.google.com/ and add it to your "
        ".env, then restart the AI service."
    )

    def __init__(self):
        # A missing key must not stop the service from starting — the router
        # builds a QAService at import time, so raising here would take the
        # whole process down and make /health unreachable too. Instead the
        # service starts, reports itself unconfigured, and says so on every
        # question.
        self.model = settings.GEMINI_MODEL
        self.configured = bool(settings.GEMINI_API_KEY)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if self.configured else None

    def generate_response(self, question: str, context: str = "") -> str:
        """Single-turn, evidence-grounded answer. Used by /chat/ask."""
        if not self.configured:
            return self.MISSING_KEY_MESSAGE

        prompt = f"""=== AVAILABLE EVIDENCE ===
{context or "No evidence was retrieved for this question."}
=========================

INVESTIGATOR'S QUESTION: {question}

Provide a clear, evidence-based answer:"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                ),
            )
            return response.text or "I wasn't able to generate a response."
        except Exception as e:
            return (
                f"Error generating response: {e}. "
                f"Check that GEMINI_API_KEY is valid and {self.model} is "
                f"still a live model name."
            )

    def create_chat(self, history: list | None = None):
        """Returns a stateful Gemini chat session for multi-turn conversation.
        `history` is a list of {"role": "user"|"model", "parts": [text]} dicts.
        Returns None when no API key is configured; callers fall back to
        MISSING_KEY_MESSAGE."""
        if not self.configured:
            return None

        return self.client.chats.create(
            model=self.model,
            history=history or [],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
            ),
        )
