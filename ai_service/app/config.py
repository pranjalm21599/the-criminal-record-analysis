"""
Central configuration. Everything is read from environment variables
(loaded from .env in local dev, or injected directly by Docker Compose).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Current as of Sept 2026. gemini-1.5-flash and gemini-2.0-flash are
    # both SHUT DOWN — do not use them. If this exact model string ever
    # stops working, try "gemini-flash-latest" (Google's rolling alias)
    # or check https://ai.google.dev/gemini-api/docs/models
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Other services (Member 1, 3, 4) ---
    BACKEND_API: str = os.getenv("BACKEND_API", "http://localhost:8000")
    GRAPH_API: str = os.getenv("GRAPH_API", "http://localhost:8002")
    ANALYSIS_API: str = os.getenv("ANALYSIS_API", "http://localhost:8003")

    # --- Databases ---
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "criminal123")
    BACKEND_DB_URL: str = os.getenv("BACKEND_DB_URL", "")

    # --- Vector store ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # --- HTTP ---
    REQUEST_TIMEOUT: float = 10.0


settings = Settings()
