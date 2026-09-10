# AI Assistant Service (Member 6)

Gemini-powered RAG chat assistant for the Criminal Network Analysis System,
plus the docker-compose / health-check / pipeline-test integration files
for the whole 6-service system.

## What changed from the original spec, and why

1. **`google-generativeai` -> `google-genai`.** The old package is fully
   deprecated (Google's own repo says support ended Nov 30, 2025). This
   codebase uses the current unified SDK (`from google import genai`).
2. **`gemini-1.5-flash` -> `gemini-2.5-flash`.** Both `gemini-1.5-flash`
   and `gemini-2.0-flash` have been shut down. `GEMINI_MODEL` is read from
   `.env`, so if `gemini-2.5-flash` itself gets retired before your demo,
   change one line — no code edit needed. `gemini-flash-latest` is a
   rolling alias you can fall back to.
3. **`requests` -> `httpx.AsyncClient`.** The retrievers were synchronous,
   which blocks FastAPI's event loop under concurrent requests. Now async,
   and `qa_service.gather_context()` fires all retrieval calls
   concurrently with `asyncio.gather` instead of sequentially.
4. **Chat sessions are per-`conversation_id`.** The original `GeminiClient`
   kept one shared `chat_history` list for every caller — two
   investigators chatting at once would have corrupted each other's
   conversation. Sessions are now stored per conversation ID in
   `QAService._sessions`.
5. **`vector_store.py` is now real.** ChromaDB + Sentence Transformers were
   in the tech-stack table but nothing in the original code used them.
   `VectorStore` now does actual semantic search over free-text evidence,
   and degrades gracefully to a no-op if the packages/model aren't
   available (e.g. no internet on demo day).
6. **Added the missing `Dockerfile`.** `docker-compose.yml` referenced
   `build: ..` for `ai_service` but no `Dockerfile` existed anywhere in the
   original spec — the compose file would have failed on `docker compose up`.
7. **Frontend port fixed to `5173` everywhere** — the original
   `docker-compose.yml` mapped the frontend to `3000:80`, but the master
   doc and `health_check.py` both expected `5173`. Now consistent.

## Setup

```bash
cd ai_service
pip install -r requirements.txt
cp .env.example .env
# then edit .env: paste your key from https://aistudio.google.com/
uvicorn app.main:app --reload --port 8004
```

## Try it

```bash
curl http://localhost:8004/health

curl -X POST http://localhost:8004/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the top suspects in this network?"}'

curl -X POST http://localhost:8004/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Ravi Kumar", "conversation_id": "investigator1"}'

curl http://localhost:8004/chat/sample-questions
```

## Running the whole system

```bash
cd integration
GEMINI_API_KEY=your-key docker compose up --build
python health_check.py
python data_pipeline.py
```

## What you hand off to the team

| Member | What they get from you |
|--------|------------------------|
| Member 5 (Frontend) | `POST /chat/` and `POST /chat/ask` — response shapes are in `app/routers/chat.py` |
| Everyone | `integration/docker-compose.yml` — one command starts the full system |
| Team | `integration/health_check.py` to verify demo readiness before you go on stage |
