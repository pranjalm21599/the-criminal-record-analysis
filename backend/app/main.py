from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import cases, records, upload

app = FastAPI(
    title="Criminal Network Backend API",
    description="Evidence ingestion and structured storage (Member 1)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(upload.router)
app.include_router(records.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "Backend API"}


@app.get("/")
def root():
    return {"service": "Criminal Network Backend API", "docs": "/docs", "health": "/health"}


# Run with: uvicorn app.main:app --reload --port 8000
