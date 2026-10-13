from fastapi import APIRouter

from app.core.config import get_settings
from app.db.mongodb import get_database

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, object]:
    settings = get_settings()
    database = get_database()
    ping = await database.command("ping")

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "database": {
            "status": "ok" if ping.get("ok") == 1 else "unknown",
            "name": settings.mongo_db_name,
        },
    }
