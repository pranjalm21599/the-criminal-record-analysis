"""
RAG (Retrieval-Augmented Generation) orchestration.

How it works:
1. An investigator asks a question.
2. detect_query_intent() figures out WHAT they're asking about
   (risk scores? connections? financial anomalies? a specific person/case?).
3. gather_context() fetches only the RELEVANT data from the graph, the
   analysis service, and (optionally) semantic search over free-text
   evidence — run concurrently, not one-by-one.
4. GeminiClient turns that evidence + the question into a grounded answer.
5. Conversation history is kept per conversation_id so multi-turn chat
   actually has memory (the original design created one shared
   GeminiClient.chat_history for every user, which meant two investigators
   chatting at once would corrupt each other's conversation).
"""
import asyncio
import re
from typing import Dict, List, Optional

from app.llm.gemini_client import GeminiClient
from app.llm.prompt_builder import combine_context
from app.retrieval.graph_retriever import GraphRetriever
from app.retrieval.db_retriever import DBRetriever
from app.retrieval.vector_store import VectorStore

# Common English words that happen to be capitalized at the start of a
# sentence — filtered out of the naive name-extraction regex so "What",
# "How", "Show" etc. don't get treated as suspect names.
_STOPWORDS = {
    "What", "How", "Who", "Where", "When", "Why", "Show", "Tell", "Is",
    "Are", "Does", "Do", "Can", "Which", "The", "This", "That",
}


class QAService:
    def __init__(self):
        self.llm = GeminiClient()
        self.graph = GraphRetriever()
        self.db = DBRetriever()
        self.vectors = VectorStore()
        # Per-conversation Gemini chat sessions, keyed by conversation_id,
        # so concurrent investigators don't share state.
        self._sessions: Dict[str, object] = {}

    # ---------- intent + entity extraction ----------

    def detect_query_intent(self, question: str) -> Dict:
        q = question.lower()
        intents: List[str] = []

        if any(w in q for w in ["suspect", "accused", "top", "important", "risk"]):
            intents.append("risk_scores")
        if any(w in q for w in ["connect", "link", "know", "relation", "associate"]):
            intents.append("connections")
        if any(w in q for w in ["transaction", "money", "financial", "transfer", "bank"]):
            intents.append("financial_anomalies")
        if any(w in q for w in ["call", "phone", "contact", "communication"]):
            intents.append("communication_anomalies")
        if any(w in q for w in ["group", "gang", "network", "cluster", "community"]):
            intents.append("communities")
        if not intents:
            intents.append("general")

        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", question)
        persons = [p for p in capitalized if p.split()[0] not in _STOPWORDS and len(p) > 3]

        case_ids = [int(c) for c in re.findall(r"(?:case|case id|case number)[:\s#]*(\d+)", q)]
        phone_numbers = re.findall(r"\b[6-9]\d{9}\b", question)

        return {
            "intents": intents,
            "entities": {"persons": persons, "case_ids": case_ids, "phone_numbers": phone_numbers},
        }

    # ---------- context gathering ----------

    async def gather_context(self, question: str, case_id: Optional[int] = None) -> str:
        intent_data = self.detect_query_intent(question)
        intents = intent_data["intents"]
        entities = intent_data["entities"]

        # Fire off every relevant retrieval call concurrently instead of
        # awaiting them one at a time — this is the main latency win over
        # the original sequential version.
        tasks = []

        if "risk_scores" in intents:
            tasks.append(self.db.get_top_suspects())
        if "financial_anomalies" in intents or "communication_anomalies" in intents:
            tasks.append(self.db.get_anomalies())
        if "communities" in intents:
            tasks.append(self.db.get_communities())

        for person in entities["persons"][:3]:
            tasks.append(self.graph.get_person_facts(person))

        for cid in entities["case_ids"][:2]:
            tasks.append(self.db.get_case_info(cid))
        if case_id is not None and case_id not in entities["case_ids"]:
            tasks.append(self.db.get_case_info(case_id))

        if "connections" in intents and len(entities["persons"]) >= 2:
            tasks.append(self.graph.find_path_between(entities["persons"][0], entities["persons"][1]))

        # Semantic search always runs in parallel too — cheap, and catches
        # evidence the keyword router missed.
        semantic_task = asyncio.to_thread(self.vectors.search, question)

        results = await asyncio.gather(*tasks, semantic_task, return_exceptions=True)
        parts = [r for r in results if isinstance(r, str) and r]

        if not parts:
            fallback = await self.graph.search_entities(question[:50])
            if fallback:
                parts.append(fallback)

        return combine_context(*parts)

    # ---------- public API ----------

    async def answer_question(self, question: str, case_id: Optional[int] = None) -> Dict:
        context = await self.gather_context(question, case_id)
        answer = self.llm.generate_response(question, context)
        intent_data = self.detect_query_intent(question)

        return {
            "question": question,
            "answer": answer,
            "data_sources_used": intent_data["intents"],
            "entities_found": intent_data["entities"],
            "context_length": len(context),
            "note": "Answer is based on available evidence in the system.",
        }

    async def chat(self, message: str, conversation_id: str = "default",
                    case_id: Optional[int] = None) -> Dict:
        context = await self.gather_context(message, case_id)

        session = self._sessions.get(conversation_id)
        if session is None:
            session = self.llm.create_chat()
            self._sessions[conversation_id] = session

        try:
            response = session.send_message(
                f"Context for this turn:\n{context}\n\nQuestion: {message}"
            )
            answer = response.text or "I wasn't able to generate a response."
        except Exception as e:
            answer = f"Error: {e}"

        return {"message": answer, "conversation_id": conversation_id}

    def reset_conversation(self, conversation_id: str = "default") -> None:
        self._sessions.pop(conversation_id, None)
