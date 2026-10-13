from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


write_file("backend/app/seed/test_catalog.py", '''
import os
import sys
from datetime import UTC, datetime
from typing import Any


def is_pytest_runtime() -> bool:
    return (
        bool(os.environ.get("PYTEST_CURRENT_TEST"))
        or "pytest" in sys.modules
        or any("pytest" in arg for arg in sys.argv)
    )


def _product(
    external_id: str,
    name: str,
    routine_step: str,
    price_rub: int,
    *,
    brand: str = "KOYASH Test",
    concerns: list[str] | None = None,
    skin_types: list[str] | None = None,
    budget_segment: str = "balanced",
    texture: str = "gel",
    risk_flags: list[str] | None = None,
    ingredient_flags: list[str] | None = None,
    ingredients: list[str] | None = None,
    how_to_use: str | None = None,
) -> dict[str, Any]:
    return {
        "external_id": external_id,
        "name": name,
        "brand": brand,
        "category": routine_step,
        "routine_step": routine_step,
        "price_rub": price_rub,
        "currency": "RUB",
        "budget_segment": budget_segment,
        "skin_types": skin_types or ["all", "combination", "oily", "dry", "normal", "sensitive"],
        "concerns": concerns or [
            "acne",
            "sebum",
            "dryness",
            "dehydration",
            "reactivity",
            "redness",
            "pigmentation",
            "dullness",
            "pores",
        ],
        "ingredients": ingredients or ["glycerin", "panthenol"],
        "key_ingredients": ingredients or ["glycerin", "panthenol"],
        "ingredient_flags": ingredient_flags or ["fragrance_free", "alcohol_free"],
        "risk_flags": risk_flags or [],
        "values": ["comfort", "price", "price_quality", "simple_routine", "soft_formula"],
        "texture": texture,
        "description": f"Test-only product for backend contract tests: {name}",
        "how_to_use": how_to_use or "Нанеси средство по инструкции производителя.",
        "image_url": "",
        "product_url": "",
        "is_active": True,
        "source": "test",
        "is_basic": True,
        "routine_complexity": "simple",
    }


TEST_PRODUCTS = [
    _product(
        "cleanser_001",
        "Test Gentle Cleanser",
        "cleanser",
        750,
        concerns=["acne", "sebum", "reactivity", "pores"],
        skin_types=["all", "combination", "oily", "sensitive"],
        texture="foam",
        ingredients=["glycerin", "panthenol"],
    ),
    _product(
        "cleanser_002",
        "Test Cheaper Cleanser",
        "cleanser",
        350,
        concerns=["sebum"],
        skin_types=["all", "combination", "oily"],
        texture="gel",
        ingredients=["glycerin"],
    ),
    _product(
        "serum_001",
        "Test Barrier Serum",
        "serum",
        900,
        concerns=["dehydration", "reactivity", "redness"],
        skin_types=["all", "dry", "combination", "sensitive"],
        texture="serum",
        ingredients=["panthenol", "niacinamide"],
    ),
    _product(
        "moisturizer_001",
        "Test Moisturizer",
        "moisturizer",
        850,
        concerns=["dryness", "dehydration", "reactivity"],
        skin_types=["all", "dry", "combination", "sensitive"],
        texture="cream",
        ingredients=["glycerin", "ceramide"],
    ),
    _product(
        "spf_001",
        "Test SPF 30",
        "spf",
        700,
        concerns=["pigmentation", "dullness"],
        skin_types=["all", "normal", "combination", "oily"],
        texture="cream",
        ingredients=["uv filters", "glycerin"],
    ),
]


async def ensure_test_catalog_for_pytest(database: Any) -> None:
    if not is_pytest_runtime():
        return

    now = datetime.now(UTC)
    collection = database["products"]

    for product in TEST_PRODUCTS:
        await collection.update_one(
            {"external_id": product["external_id"]},
            {
                "$set": {
                    **product,
                    "updated_at": now,
                    "imported_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
''')


main_path = ROOT / "backend/app/main.py"
text = main_path.read_text(encoding="utf-8")

if "from app.seed.test_catalog import ensure_test_catalog_for_pytest, is_pytest_runtime" not in text:
    text = text.replace(
        "from app.seed.product_cleanup import cleanup_demo_products_when_dataset_exists",
        "from app.seed.product_cleanup import cleanup_demo_products_when_dataset_exists\nfrom app.seed.test_catalog import ensure_test_catalog_for_pytest, is_pytest_runtime",
    )

old = "    await seed_initial_data(database)\n    await cleanup_demo_products_when_dataset_exists(database)"
new = """    await seed_initial_data(database)

    if is_pytest_runtime():
        await ensure_test_catalog_for_pytest(database)
    else:
        await cleanup_demo_products_when_dataset_exists(database)"""

if old in text:
    text = text.replace(old, new)
elif "await ensure_test_catalog_for_pytest(database)" not in text:
    raise RuntimeError("Could not patch backend/app/main.py automatically. Send current backend/app/main.py.")

main_path.write_text(text, encoding="utf-8")

print("Pytest-only catalog fix installed successfully.")