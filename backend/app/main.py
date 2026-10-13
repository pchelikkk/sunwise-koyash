from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database
from app.importers.product_dataset_sync import sync_product_dataset
from app.seed import seed_initial_data
from app.seed.product_cleanup import cleanup_demo_products_when_dataset_exists
from app.seed.test_catalog import ensure_test_catalog_for_pytest


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await connect_to_mongo()
    database = get_database()
    runtime_settings = get_settings()
    is_test_environment = runtime_settings.app_env.lower() == "test"

    if (
        not is_test_environment
        and runtime_settings.import_dataset_on_startup
        and runtime_settings.product_dataset_file.is_file()
    ):
        await sync_product_dataset(database, runtime_settings.product_dataset_file)

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
        yield
    finally:
        await close_mongo_connection()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.1",
    description=(
        "KOYASH API for deterministic, explainable skincare routines, "
        "product discovery, feedback, and account history."
    ),
    lifespan=lifespan,
)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def root_health_check() -> dict[str, object]:
    database = get_database()
    ping = await database.command("ping")

    return {
        "status": "ok",
        "service": settings.app_name,
        "database": "ok" if ping.get("ok") == 1 else "unknown",
    }

