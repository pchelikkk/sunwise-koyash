import argparse
import asyncio
import json
import sys
from typing import Any

from pydantic import EmailStr, TypeAdapter, ValidationError
from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.time import utc_now


async def set_role(email: str, role: UserRole, apply_change: bool) -> dict[str, Any]:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        users = client[settings.mongo_db_name]["users"]
        user = await users.find_one({"email": email})

        if user is None:
            return {
                "ok": False,
                "database": settings.mongo_db_name,
                "email": email,
                "error": "user_not_found",
            }

        previous_role = str(user.get("role") or UserRole.USER.value)

        if apply_change:
            await users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "role": role.value,
                        "updated_at": utc_now(),
                    }
                },
            )

        return {
            "ok": True,
            "applied": apply_change,
            "database": settings.mongo_db_name,
            "user_id": str(user["_id"]),
            "email": email,
            "previous_role": previous_role,
            "requested_role": role.value,
        }
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely set role for an existing KOYASH user.",
    )
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in UserRole],
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the change. Without this flag the command is a dry run.",
    )
    args = parser.parse_args()

    try:
        email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": "invalid_email"}, indent=2))
        raise SystemExit(2) from exc

    report = asyncio.run(
        set_role(
            email=email,
            role=UserRole(args.role),
            apply_change=args.apply,
        )
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
