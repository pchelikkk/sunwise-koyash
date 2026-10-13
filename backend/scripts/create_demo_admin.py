import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import create_password_hash
from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository


async def main() -> None:
    settings = get_settings()
    if settings.is_production:
        raise RuntimeError("Demo administrator creation is disabled in production")

    email = os.getenv("KOYASH_DEMO_ADMIN_EMAIL", "admin@koyash-demo.ru").strip().lower()
    password = os.getenv("KOYASH_DEMO_ADMIN_PASSWORD", "")
    if len(password) < 12:
        raise RuntimeError("KOYASH_DEMO_ADMIN_PASSWORD must contain at least 12 characters")

    await connect_to_mongo()
    database = get_database()
    users = UserRepository(database)
    profiles = ProfileRepository(database)

    existing = await users.find_by_email(email)
    if existing is None:
        await users.create_user(
            email=email,
            password_hash=create_password_hash(password),
            full_name="Демо-администратор KOYASH",
        )
        action = "created"
    else:
        await users.update_password(existing["user_id"], create_password_hash(password))
        action = "updated"

    admin = await users.set_role_by_email(email, UserRole.ADMIN)
    if admin is None:
        raise RuntimeError("Could not assign administrator role")
    await profiles.ensure_profile(admin["user_id"])

    print(
        "DEMO ADMIN OK",
        {
            "action": action,
            "email": email,
            "role": admin["role"],
            "database": settings.mongo_db_name,
        },
    )
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
