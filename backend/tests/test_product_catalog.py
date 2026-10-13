from fastapi.testclient import TestClient

from app.main import app


def test_catalog_returns_paginated_products_and_facets() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/products/catalog",
            params={"page": 1, "page_size": 3, "sort": "price_asc"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 8
    assert len(payload["items"]) == 3
    assert payload["total_pages"] >= 3
    assert payload["facets"]["routine_steps"]
    assert payload["facets"]["max_price_rub"] >= payload["facets"]["min_price_rub"]
    prices = [product["price_rub"] for product in payload["items"]]
    assert prices == sorted(prices)


def test_default_catalog_interleaves_routine_steps() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/products/catalog",
            params={"page": 1, "page_size": 6},
        )

    assert response.status_code == 200
    steps = [product["routine_step"] for product in response.json()["items"]]
    assert len(set(steps)) >= 4


def test_catalog_combines_filters_without_leaking_inactive_products() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/products/catalog",
            params=[
                ("routine_step", "cleanser"),
                ("skin_type", "combination"),
                ("no_known_irritants", "true"),
                ("page_size", "48"),
            ],
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    for product in payload["items"]:
        assert product["routine_step"] == "cleanser"
        assert product["is_active"] is True
        assert not {
            "contains_alcohol",
            "contains_essential_oils",
            "contains_fragrance",
        }.intersection(product["risk_flags"])
        assert "combination" in product["skin_types"] or "all" in product["skin_types"]


def test_catalog_search_is_case_insensitive() -> None:
    with TestClient(app) as client:
        first = client.get(
            "/api/v1/products/catalog",
            params={"page_size": 1},
        ).json()["items"][0]
        response = client.get(
            "/api/v1/products/catalog",
            params={"search": first["brand"].upper(), "page_size": 48},
        )

    assert response.status_code == 200
    assert response.json()["items"]
    assert all(
        first["brand"].casefold() in (item["brand"] + " " + item["name"]).casefold()
        for item in response.json()["items"]
    )


def test_catalog_rejects_inverted_price_range() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/products/catalog",
            params={"min_price_rub": 2000, "max_price_rub": 1000},
        )

    assert response.status_code == 422
