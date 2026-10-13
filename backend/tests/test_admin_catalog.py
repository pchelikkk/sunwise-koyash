from uuid import uuid4

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.core.config import get_settings
from app.main import app


def _restore_catalog_state(state: dict | None, external_id: str) -> None:
    settings = get_settings()
    mongo_client = MongoClient(settings.mongo_uri)
    try:
        database = mongo_client[settings.mongo_db_name]
        database["products"].delete_one({"external_id": external_id})
        database["admin_audit_events"].delete_many(
            {
                "event_type": "catalog_dataset_imported",
                "external_ids": external_id,
            }
        )
        database["catalog_import_state"].delete_one(
            {"_id": "canonical-product-dataset"}
        )
        if state is not None:
            database["catalog_import_state"].insert_one(state)
    finally:
        mongo_client.close()


def _admin_headers(client: TestClient) -> dict[str, str]:
    email = f"catalog-admin-{uuid4().hex}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Catalog Admin",
        },
    )
    assert registered.status_code == 201

    settings = get_settings()
    mongo_client = MongoClient(settings.mongo_uri)
    try:
        result = mongo_client[settings.mongo_db_name]["users"].update_one(
            {"email": email},
            {"$set": {"role": "admin"}},
        )
        assert result.matched_count == 1
    finally:
        mongo_client.close()

    return {"Authorization": f"Bearer {registered.json()['access_token']}"}


def test_admin_catalog_quality_is_protected_and_documented() -> None:
    with TestClient(app) as client:
        unauthenticated = client.get("/api/v1/admin/catalog/quality")
        schema = client.get("/openapi.json").json()
        headers = _admin_headers(client)
        response = client.get("/api/v1/admin/catalog/quality", headers=headers)

    assert unauthenticated.status_code == 401
    assert "/api/v1/admin/catalog/quality" in schema["paths"]
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_products"] >= 8
    assert payload["active_products"] >= 8
    assert payload["step_counts"]["cleanser"] >= 1
    assert 0 <= payload["completeness_percent"] <= 100
    assert 0 <= payload["image_coverage_percent"] <= 100
    assert 0 <= payload["product_link_coverage_percent"] <= 100
    assert 0 <= payload["usage_coverage_percent"] <= 100
    assert all("email" not in key for key in payload)


def test_admin_can_review_catalog_issues_and_update_content() -> None:
    with TestClient(app) as client:
        headers = _admin_headers(client)
        issue_response = client.get(
            "/api/v1/admin/catalog/issues",
            params={"issue": "missing_image", "page_size": 5},
            headers=headers,
        )
        update_response = client.patch(
            "/api/v1/admin/catalog/products/cleanser_001",
            json={
                "image_url": "https://example.com/cleanser.png",
                "how_to_use": "Нанеси на влажную кожу и мягко смой водой.",
            },
            headers=headers,
        )

    assert issue_response.status_code == 200
    assert issue_response.json()["total"] >= 1
    assert all("missing_image" in item["issues"] for item in issue_response.json()["items"])
    assert update_response.status_code == 200
    assert update_response.json()["image_url"] == "https://example.com/cleanser.png"

    settings = get_settings()
    mongo_client = MongoClient(settings.mongo_uri)
    try:
        audit = mongo_client[settings.mongo_db_name]["admin_audit_events"].find_one(
            {"product_external_id": "cleanser_001"}
        )
    finally:
        mongo_client.close()

    assert audit is not None
    assert audit["event_type"] == "catalog_product_updated"


def test_admin_product_update_rejects_unsafe_url() -> None:
    with TestClient(app) as client:
        headers = _admin_headers(client)
        response = client.patch(
            "/api/v1/admin/catalog/products/cleanser_001",
            json={"product_url": "javascript:alert(1)"},
            headers=headers,
        )

    assert response.status_code == 422


def test_admin_can_validate_and_import_dataset_without_restart() -> None:
    external_id = f"admin_import_{uuid4().hex}"
    settings = get_settings()
    mongo_client = MongoClient(settings.mongo_uri)
    try:
        previous_state = mongo_client[settings.mongo_db_name][
            "catalog_import_state"
        ].find_one({"_id": "canonical-product-dataset"})
    finally:
        mongo_client.close()

    csv_content = (
        "external_id,name,brand,category,routine_step,price_rub,skin_types,"
        "concerns,ingredients,how_to_use,product_url,is_active\n"
        f"{external_id},Admin Import Cleanser,KOYASH QA,Очищение,cleanser,990,"
        "all,dryness,glycerin,Нанеси на влажную кожу и смой водой.,"
        "https://example.com/admin-import,true\n"
    )

    try:
        with TestClient(app) as client:
            headers = _admin_headers(client)
            response = client.post(
                "/api/v1/admin/catalog/import",
                headers=headers,
                files={
                    "file": (
                        "products.csv",
                        csv_content.encode("utf-8"),
                        "text/csv",
                    )
                },
                data={"synchronize_missing": "false"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["rows_valid"] == 1
        assert payload["inserted"] == 1
        assert payload["deactivated"] == 0
        assert payload["synchronize_missing"] is False

        mongo_client = MongoClient(settings.mongo_uri)
        try:
            database = mongo_client[settings.mongo_db_name]
            product = database["products"].find_one({"external_id": external_id})
            audit = database["admin_audit_events"].find_one(
                {
                    "event_type": "catalog_dataset_imported",
                    "fingerprint": payload["fingerprint"],
                }
            )
            state = database["catalog_import_state"].find_one(
                {"_id": "canonical-product-dataset"}
            )
        finally:
            mongo_client.close()

        assert product is not None
        assert product["source"] == "dataset"
        assert audit is not None
        assert state is not None
        assert state["source"] == "admin_upload"
    finally:
        _restore_catalog_state(previous_state, external_id)
