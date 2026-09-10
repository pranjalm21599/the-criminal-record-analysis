from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat

app = FastAPI(
    title="AI Assistant Service",
    description="Gemini-powered Q&A for the Criminal Network Analysis System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Assistant",
        "llm_model": settings.GEMINI_MODEL,
    }


# Run with: uvicorn app.main:app --reload --port 8004
