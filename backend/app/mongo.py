from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

# Collections
raw_docs_collection = db.get_collection("raw_documents")
audit_logs_collection = db.get_collection("audit_logs")

async def ping_mongo():
    try:
        await client.admin.command('ping')
        return True
    except Exception:
        return False