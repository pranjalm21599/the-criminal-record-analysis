"""
Semantic search over free-text evidence (FIR narratives, witness statements,
chat notes) using ChromaDB + Sentence Transformers.

This is the piece that was listed in the Member 6 tech-stack table
(LangChain / ChromaDB / Sentence Transformers) but never actually appeared
in the original code — the rest of the pipeline is keyword-routed REST
calls, which is a fine RAG-lite pattern but isn't "semantic search." This
module makes that claim true, and gives you something concrete to point to
if a judge asks "where's the vector search."

Usage:
    store = VectorStore()
    store.add_documents([{"id": "fir_001", "text": "...", "meta": {...}}])
    hits = store.search("robbery near Andheri involving a white car", k=3)

If chromadb / sentence-transformers aren't installed or fail to load
(e.g. offline demo laptop with no model cached), this degrades to
returning an empty result set rather than crashing the service — semantic
search is a bonus signal, not something the whole chat should depend on.
"""
from app.config import settings

_backend_ready = False
_client = None
_collection = None
_embedder = None

try:
    import chromadb
    from sentence_transformers import SentenceTransformer

    _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    _collection = _client.get_or_create_collection("evidence")
    _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    _backend_ready = True
except Exception:
    # chromadb / sentence-transformers not installed, or model download
    # failed (no internet on demo day). Semantic search just no-ops.
    _backend_ready = False


class VectorStore:
    def __init__(self):
        self.ready = _backend_ready

    def add_documents(self, docs: list[dict]) -> int:
        """docs: [{"id": str, "text": str, "meta": dict}, ...]
        Returns the number of documents actually indexed."""
        if not self.ready or not docs:
            return 0

        embeddings = _embedder.encode([d["text"] for d in docs]).tolist()
        _collection.upsert(
            ids=[d["id"] for d in docs],
            embeddings=embeddings,
            documents=[d["text"] for d in docs],
            metadatas=[d.get("meta", {}) for d in docs],
        )
        return len(docs)

    def search(self, query: str, k: int = 3) -> str:
        """Returns a formatted string of the top-k semantically similar
        evidence snippets, or an empty string if the backend isn't ready
        or nothing relevant is indexed."""
        if not self.ready:
            return ""

        try:
            query_embedding = _embedder.encode([query]).tolist()
            results = _collection.query(query_embeddings=query_embedding, n_results=k)
        except Exception:
            return ""

        docs = results.get("documents", [[]])[0]
        if not docs:
            return ""

        lines = ["Semantically similar evidence:"]
        for doc in docs:
            snippet = doc[:300] + ("..." if len(doc) > 300 else "")
            lines.append(f"- {snippet}")
        return "\n".join(lines)
