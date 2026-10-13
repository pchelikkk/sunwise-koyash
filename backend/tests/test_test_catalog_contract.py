from app.seed.test_catalog import TEST_PRODUCTS


def test_test_catalog_has_cross_brand_cleanser_alternative() -> None:
    cleansers = [
        product
        for product in TEST_PRODUCTS
        if product.get("routine_step") == "cleanser"
    ]

    brands = {
        str(product.get("brand") or "").strip().casefold()
        for product in cleansers
        if str(product.get("brand") or "").strip()
    }

    assert len(cleansers) >= 2
    assert len(brands) >= 2


def test_cleanser_002_is_a_different_brand_alternative() -> None:
    products = {
        product["external_id"]: product
        for product in TEST_PRODUCTS
    }

    original = products["cleanser_001"]
    alternative = products["cleanser_002"]

    assert original["routine_step"] == alternative["routine_step"]
    assert original["brand"].casefold() != alternative["brand"].casefold()
    assert alternative["price_rub"] < original["price_rub"]
