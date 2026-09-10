from fastapi import FastAPI

from app.routers import extract


app = FastAPI(
    title="NLP Extraction Service",
    description="NLP Entity and Pattern Extraction for Criminal Network Analysis",
    version="1.0.0"
)


app.include_router(extract.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "NLP Extraction"
    }