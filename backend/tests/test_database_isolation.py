import pytest

from app.core.config import get_settings
from app.seed import seed_initial_data


def test_pytest_uses_isolated_database() -> None:
    settings = get_settings()

    assert settings.app_env == "test"
    assert settings.mongo_db_name == "koyash_test"
    assert settings.mongo_db_name != "koyash"


@pytest.mark.asyncio
async def test_seed_initial_data_can_skip_sample_products(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def mark_aliases(database: object) -> None:
        calls.append("aliases")

    async def mark_restrictions(database: object) -> None:
        calls.append("restrictions")

    async def mark_products(database: object) -> None:
        calls.append("products")

    monkeypatch.setattr(
        "app.seed.seed_ingredient_aliases",
        mark_aliases,
    )
    monkeypatch.setattr(
        "app.seed.seed_restrictions",
        mark_restrictions,
    )
    monkeypatch.setattr(
        "app.seed.seed_products",
        mark_products,
    )

    await seed_initial_data(
        object(),
        include_sample_products=False,
    )

    assert calls == ["aliases", "restrictions"]
