from pathlib import Path
import compileall
import re


ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> Path:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 1. Runtime startup:
#    - test catalog only when APP_ENV=test;
#    - do not seed sample products when dataset products already exist.
# ---------------------------------------------------------------------------

main_path = ROOT / "backend/app/main.py"
main_text = main_path.read_text(encoding="utf-8-sig")

main_text, import_count = re.subn(
    r"from app\.seed\.test_catalog import[^\n]+",
    "from app.seed.test_catalog import ensure_test_catalog_for_pytest",
    main_text,
    count=1,
)

if import_count != 1:
    raise RuntimeError(
        "Could not patch test_catalog import in backend/app/main.py"
    )

lifespan_pattern = re.compile(
    r"@asynccontextmanager\n"
    r"async def lifespan\(_: FastAPI\) -> AsyncIterator\[None\]:\n"
    r".*?"
    r"    try:\n",
    re.DOTALL,
)

lifespan_replacement = '''@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await connect_to_mongo()
    database = get_database()
    runtime_settings = get_settings()
    is_test_environment = runtime_settings.app_env.lower() == "test"
    dataset_count = await database["products"].count_documents(
        {"source": "dataset"}
    )

    await seed_initial_data(
        database,
        include_sample_products=is_test_environment or dataset_count == 0,
    )

    if is_test_environment:
        await ensure_test_catalog_for_pytest(database)
    else:
        await cleanup_demo_products_when_dataset_exists(database)
    try:
'''

main_text, lifespan_count = lifespan_pattern.subn(
    lifespan_replacement,
    main_text,
    count=1,
)

if lifespan_count != 1:
    raise RuntimeError(
        "Could not patch lifespan in backend/app/main.py"
    )

if "is_pytest_runtime" in main_text:
    raise RuntimeError(
        "backend/app/main.py still references is_pytest_runtime"
    )

main_path.write_text(main_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# 2. Sample seeding can now be disabled explicitly.
# ---------------------------------------------------------------------------

seed_init_path = write_file(
    "backend/app/seed/__init__.py",
    '''
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
''',
)


# ---------------------------------------------------------------------------
# 3. Remove heuristic pytest detection.
#    Main application now decides explicitly using APP_ENV=test.
# ---------------------------------------------------------------------------

test_catalog_path = ROOT / "backend/app/seed/test_catalog.py"
test_catalog_text = test_catalog_path.read_text(encoding="utf-8-sig")

test_catalog_text = test_catalog_text.replace(
    "import os\nimport sys\n",
    "",
)

test_catalog_text = re.sub(
    r"\ndef is_pytest_runtime\(\) -> bool:\n"
    r".*?"
    r"\n\ndef _product",
    "\n\ndef _product",
    test_catalog_text,
    count=1,
    flags=re.DOTALL,
)

test_catalog_text = test_catalog_text.replace(
    '''async def ensure_test_catalog_for_pytest(database: Any) -> None:
    if not is_pytest_runtime():
        return

    now = datetime.now(UTC)''',
    '''async def ensure_test_catalog_for_pytest(database: Any) -> None:
    now = datetime.now(UTC)''',
)

if "is_pytest_runtime" in test_catalog_text:
    raise RuntimeError(
        "backend/app/seed/test_catalog.py still contains is_pytest_runtime"
    )

test_catalog_path.write_text(test_catalog_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# 4. Pytest isolation:
#    all tests use koyash_test, never the runtime koyash database.
# ---------------------------------------------------------------------------

conftest_path = write_file(
    "backend/tests/conftest.py",
    '''
import os

import pytest
from pymongo import MongoClient


TEST_DATABASE_NAME = "koyash_test"

# conftest.py loads before test modules import app.main.
os.environ["APP_ENV"] = "test"
os.environ["MONGO_DB_NAME"] = TEST_DATABASE_NAME


def pytest_configure(config: pytest.Config) -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()


def _drop_test_database() -> None:
    from app.core.config import get_settings

    settings = get_settings()

    if settings.mongo_db_name != TEST_DATABASE_NAME:
        raise RuntimeError(
            f"Refusing to drop unexpected database: "
            f"{settings.mongo_db_name!r}"
        )

    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )

    try:
        client.admin.command("ping")
        client.drop_database(TEST_DATABASE_NAME)
    finally:
        client.close()


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    _drop_test_database()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    _drop_test_database()
''',
)


# ---------------------------------------------------------------------------
# 5. Regression tests for database isolation and sample-seed suppression.
# ---------------------------------------------------------------------------

isolation_test_path = write_file(
    "backend/tests/test_database_isolation.py",
    '''
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
''',
)


# ---------------------------------------------------------------------------
# 6. Read-only catalog checker.
#    It verifies the runtime DB without deleting or changing anything.
# ---------------------------------------------------------------------------

catalog_check_path = write_file(
    "backend/scripts/check_product_catalog_state.py",
    '''
import argparse
import asyncio
import json
import sys
from typing import Any

from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.seed.product_cleanup import SAMPLE_PRODUCTS_QUERY


async def async_main(strict_dataset: bool) -> None:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        products = client[settings.mongo_db_name]["products"]

        total = await products.count_documents({})
        dataset = await products.count_documents(
            {"source": "dataset"}
        )
        non_dataset = await products.count_documents(
            {"source": {"$ne": "dataset"}}
        )
        sample_like = await products.count_documents(
            SAMPLE_PRODUCTS_QUERY
        )

        strict_dataset_ok = (
            total > 0
            and total == dataset
            and non_dataset == 0
            and sample_like == 0
        )

        report = {
            "database": settings.mongo_db_name,
            "total": int(total),
            "dataset": int(dataset),
            "non_dataset": int(non_dataset),
            "sample_like": int(sample_like),
            "strict_dataset_ok": strict_dataset_ok,
        }

        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            )
        )

        if strict_dataset and not strict_dataset_ok:
            sys.exit(1)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict-dataset",
        action="store_true",
    )
    args = parser.parse_args()

    asyncio.run(
        async_main(args.strict_dataset)
    )


if __name__ == "__main__":
    main()
''',
)


modified_files = [
    main_path,
    seed_init_path,
    test_catalog_path,
    conftest_path,
    isolation_test_path,
    catalog_check_path,
]

for path in modified_files:
    compile_ok = compileall.compile_file(
        str(path),
        quiet=1,
    )

    if not compile_ok:
        raise RuntimeError(
            f"Python compilation failed: {path}"
        )

print(
    "ROOT FIX APPLIED: "
    "pytest uses koyash_test; "
    "runtime koyash remains dataset-only."
)