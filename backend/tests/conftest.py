import os

import pytest
from pymongo import MongoClient

TEST_DATABASE_NAME = "koyash_test"

# conftest.py loads before test modules import app.main.
os.environ["APP_ENV"] = "test"
os.environ["MONGO_DB_NAME"] = TEST_DATABASE_NAME
os.environ["JWT_SECRET_KEY"] = "koyash-test-secret-key-at-least-32-bytes"


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
