from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph_loader import graph_loader
from app.routers import analysis

app = FastAPI(
    title="Network Analysis Service",
    description="Centrality, community detection, anomaly ML and risk scoring (Member 4)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Network Analysis",
        "neo4j_connected": graph_loader.is_connected(),
    }


@app.get("/")
def root():
    return {"service": "Network Analysis Service", "docs": "/docs", "health": "/health"}


@app.on_event("shutdown")
def on_shutdown() -> None:
    graph_loader.close()


# Run with: uvicorn app.main:app --reload --port 8003
