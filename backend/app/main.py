from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .routers import cases, upload, health, fir, call_records

# Create Database Tables (Development)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for AI Criminal Network Analysis",
    version="1.0.0"
)

# CORS Configuration
origins = settings.ALLOWED_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(cases.router)
app.include_router(upload.router)
# app.include_router(fir.router)
# app.include_router(call_records.router)

@app.get("/")
def read_root():
    return {"message": "Criminal Network API v1.0", "docs": "/docs"}