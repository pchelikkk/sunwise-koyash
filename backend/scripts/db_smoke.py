import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database


async def main() -> None:
    await connect_to_mongo()

    database = get_database()

    ping = await database.command("ping")
    product_count = await database["products"].count_documents({})
    restriction_count = await database["restriction_suggestions"].count_documents({})
    user_count = await database["users"].count_documents({})
    profile_count = await database["user_profiles"].count_documents({})

    print("Mongo ping:", ping)
    print("Database name:", database.name)
    print("Products:", product_count)
    print("Restriction suggestions:", restriction_count)
    print("Users:", user_count)
    print("User profiles:", profile_count)
    print("DB SMOKE OK")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
