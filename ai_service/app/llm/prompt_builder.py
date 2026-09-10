"""
Small helpers for shaping context text before it goes to Gemini.
Kept separate from gemini_client.py so retrieval-side formatting logic
doesn't get tangled up with the API wrapper itself.
"""


def combine_context(*sections: str, max_chars: int = 8000) -> str:
    """Join non-empty context sections and hard-cap the total length so a
    chatty retriever can't blow out the prompt (and your Gemini quota)."""
    parts = [s.strip() for s in sections if s and s.strip()]
    combined = "\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n...[context truncated]"
    return combined or "No relevant data was found in the system."


def format_sample_questions() -> list[str]:
    return [
        "Who are the top 5 suspects in the network?",
        "How is Ravi Kumar connected to the Mumbai gang?",
        "What suspicious transactions have been flagged?",
        "Show me the criminal groups detected in the network.",
        "What is the risk score for Mohammad Ali?",
        "Are there any communication anomalies in case 1?",
        "What crimes are associated with suspect Suresh Sharma?",
    ]
