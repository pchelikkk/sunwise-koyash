from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.seed.seed_ingredient_aliases import seed_ingredient_aliases
from app.seed.seed_products import seed_products
from app.seed.seed_restrictions import seed_restrictions


async def seed_initial_data(
    database: AsyncDatabase[Any],
    *,
    include_sample_products: bool = True,
) -> None:
    await seed_ingredient_aliases(database)
    await seed_restrictions(database)

    if include_sample_products:
        await seed_products(database)
