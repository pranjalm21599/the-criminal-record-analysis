from fastapi import APIRouter, Depends
from ..database import engine
from ..mongo import ping_mongo
import redis

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    # Check Postgres
    postgres_ok = False
    try:
        with engine.connect() as conn:
            postgres_ok = True
    except: pass

    # Check Mongo
    mongo_ok = await ping_mongo()

    return {
        "status": "active" if postgres_ok and mongo_ok else "degraded",
        "databases": {
            "postgres": "up" if postgres_ok else "down",
            "mongodb": "up" if mongo_ok else "down"
        }
    }