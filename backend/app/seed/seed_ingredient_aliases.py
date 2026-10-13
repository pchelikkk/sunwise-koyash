from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

ALIASES = [
    {
        "canonical_key": "fragrance",
        "display_name": "Отдушки",
        "aliases": [
            "отдушка",
            "отдушки",
            "ароматизатор",
            "ароматизаторы",
            "fragrance",
            "parfum",
            "perfume",
        ],
        "kind": "restriction",
        "is_active": True,
    },
    {
        "canonical_key": "alcohol",
        "display_name": "Спирт",
        "aliases": ["спирт", "алкоголь", "alcohol", "ethanol", "этанол", "ethyl alcohol"],
        "kind": "restriction",
        "is_active": True,
    },
    {
        "canonical_key": "essential_oils",
        "display_name": "Эфирные масла",
        "aliases": ["эфирные масла", "эфирное масло", "essential oils", "essential oil"],
        "kind": "restriction",
        "is_active": True,
    },
    {
        "canonical_key": "none",
        "display_name": "Нет ограничений",
        "aliases": ["нет ограничений", "ничего", "no restrictions", "none"],
        "kind": "restriction",
        "is_active": True,
    },
]


async def seed_ingredient_aliases(database: AsyncDatabase[Any]) -> None:
    collection = database["ingredient_aliases"]

    for alias in ALIASES:
        await collection.update_one(
            {"canonical_key": alias["canonical_key"]},
            {"$set": alias},
            upsert=True,
        )
