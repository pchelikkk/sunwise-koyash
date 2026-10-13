from fastapi.testclient import TestClient

from app.main import app


def test_products_are_seeded_and_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) >= 8
    assert all(product["external_id"] for product in payload)
    assert all(product["is_active"] is True for product in payload)


def test_product_can_be_loaded_by_external_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products/cleanser_001")

    assert response.status_code == 200
    payload = response.json()

    assert payload["external_id"] == "cleanser_001"
    assert payload["routine_step"] == "cleanser"


def test_unknown_product_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products/unknown_product")

    assert response.status_code == 404
