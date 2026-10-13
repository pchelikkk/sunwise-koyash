from pathlib import Path

from openpyxl import Workbook

from app.importers.product_dataset import (
    load_products_from_dataset,
    normalize_product_row,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REAL_DATASET_PATH = REPOSITORY_ROOT / "data" / "products.xlsx"


def test_product_dataset_mapper_accepts_actual_products_columns() -> None:
    row = {
        "product_id": "product_001",
        "name": "Мягкая пенка",
        "brand": "Demo Brand",
        "price_rub": 743,
        "segment": "бюджет",
        "category": "Очищающий гель/пенка",
        "link": "https://example.com/product",
        "ingredients_raw": "Aqua, Glycerin, Fragrance",
        "main_actives": "Glycerin (увлажнитель)",
        "functional_category": "Мягкое очищение, гидратация",
        "allergens": "Fragrance",
        "vegan": "Да",
        "cruelty_free": "Да",
        "format": "Пенка",
        "volume_ml": 75,
        "price_per_ml": 9.9,
        "issues": "Есть отдушка",
        "status": False,
    }

    product = normalize_product_row(row, row_number=2)

    assert product["external_id"] == "product_001"
    assert product["name"] == "Мягкая пенка"
    assert product["brand"] == "Demo Brand"
    assert product["price_rub"] == 743
    assert product["budget_segment"] == "minimum"
    assert product["routine_step"] == "cleanser"
    assert product["product_url"] == "https://example.com/product"
    assert product["how_to_use"]
    assert "Glycerin" in product["ingredients"]
    assert "contains_fragrance" in product["risk_flags"]
    assert product["source"] == "dataset"
    assert product["is_active"] is True


def test_product_dataset_mapper_normalizes_browser_links_and_rejects_unsafe_urls() -> None:
    bare_link = normalize_product_row(
        {
            "name": "Toner",
            "brand": "Demo",
            "routine_step": "toner",
            "link": "example.com/product",
            "image": "javascript:alert(1)",
        },
        row_number=2,
    )

    assert bare_link["product_url"] == "https://example.com/product"
    assert bare_link["image_url"] == ""
    assert "после очищения" in bare_link["how_to_use"].lower()


def test_product_dataset_mapper_accepts_russian_columns() -> None:
    row = {
        "Название": "Мягкая пенка",
        "Бренд": "Demo Brand",
        "Цена": "750 ₽",
        "Шаг ухода": "Очищение",
        "Типы кожи": "комбинированная; жирная",
        "Запросы": "жирный блеск; высыпания",
        "Состав": "glycerin; parfum",
        "Активен": "да",
    }

    product = normalize_product_row(row, row_number=2)

    assert product["name"] == "Мягкая пенка"
    assert product["brand"] == "Demo Brand"
    assert product["price_rub"] == 750
    assert product["routine_step"] == "cleanser"
    assert product["skin_types"] == ["combination", "oily"]
    assert product["concerns"] == ["sebum", "acne"]
    assert "contains_fragrance" in product["risk_flags"]
    assert product["source"] == "dataset"
    assert product["is_active"] is True


def test_product_dataset_mapper_generates_budget_from_price() -> None:
    row = {
        "name": "Basic SPF",
        "brand": "Demo Brand",
        "price": "2600",
        "routine_step": "spf",
    }

    product = normalize_product_row(row, row_number=3)

    assert product["budget_segment"] == "premium"
    assert product["routine_step"] == "spf"


def test_product_dataset_mapper_deactivates_discontinued_products() -> None:
    product = normalize_product_row(
        {
            "product_id": "legacy_001",
            "name": "Legacy peeling",
            "brand": "Demo Brand",
            "price_rub": 900,
            "category": "Peeling",
            "status": "discontinued",
        },
        row_number=2,
    )

    assert product["product_status"] == "discontinued"
    assert product["is_active"] is False


def test_product_dataset_explicit_active_flag_overrides_catalog_status() -> None:
    product = normalize_product_row(
        {
            "product_id": "returned_001",
            "name": "Returned product",
            "brand": "Demo Brand",
            "price_rub": 900,
            "category": "Cleanser",
            "status": "discontinued",
            "is_active": "yes",
        },
        row_number=2,
    )

    assert product["is_active"] is True


def test_product_dataset_loader_reads_csv(tmp_path: Path) -> None:
    file_path = tmp_path / "products.csv"
    file_path.write_text(
        "Название;Бренд;Цена;Шаг ухода;Типы кожи;Запросы;Состав\n"
        "Пенка;Demo;700;Очищение;комбинированная;жирный блеск;glycerin\n",
        encoding="utf-8",
    )

    preview = load_products_from_dataset(file_path)

    assert len(preview.products) == 1
    assert preview.errors == []
    assert preview.products[0]["routine_step"] == "cleanser"


def test_product_dataset_loader_collects_invalid_rows(tmp_path: Path) -> None:
    file_path = tmp_path / "products.csv"
    file_path.write_text(
        "Название;Бренд;Цена;Шаг ухода\n"
        ";Demo;700;Очищение\n",
        encoding="utf-8",
    )

    preview = load_products_from_dataset(file_path)

    assert preview.products == []
    assert len(preview.errors) == 1
    assert preview.errors[0].reason == "Missing product name"


def test_product_dataset_loader_selects_products_sheet_not_consultations(tmp_path: Path) -> None:
    file_path = tmp_path / "products.xlsx"

    workbook = Workbook()
    consultation_sheet = workbook.active
    consultation_sheet.title = "Koyash"
    consultation_sheet.append(["consultation_id", "age", "skin_type", "concerns", "budget"])
    consultation_sheet.append(["cons_001", 22, "Жирная", "акне", "low"])

    products_sheet = workbook.create_sheet("Products")
    products_sheet.append(
        [
            "product_id",
            "name",
            "brand",
            "price_rub",
            "segment",
            "category",
            "link",
            "ingredients_raw",
            "main_actives",
            "functional_category",
        ]
    )
    products_sheet.append(
        [
            "product_001",
            "Мягкая пенка",
            "Demo",
            700,
            "бюджет",
            "Очищающий гель",
            "https://example.com",
            "Aqua, Glycerin",
            "Glycerin",
            "Мягкое очищение, гидратация",
        ]
    )

    workbook.save(file_path)

    preview = load_products_from_dataset(file_path)

    assert len(preview.products) == 1
    assert preview.errors == []
    assert preview.products[0]["external_id"] == "product_001"
    assert preview.products[0]["routine_step"] == "cleanser"


def test_real_dataset_keeps_reviewed_product_semantics_and_ruble_sources() -> None:
    preview = load_products_from_dataset(REAL_DATASET_PATH)
    products = {product["external_id"]: product for product in preview.products}

    corrected_toner = products["product_015"]
    aha_tonic = products["product_027"]
    some_by_mi = products["product_019"]
    mineral_89 = products["product_035"]

    assert corrected_toner["routine_step"] == "toner"
    assert "тоник" in corrected_toner["name"].lower()
    assert "krason.ru" in corrected_toner["product_url"]
    assert aha_tonic["routine_step"] == "toner"
    assert "aravia.ru" in aha_tonic["product_url"]
    assert some_by_mi["price_rub"] == 2030
    assert "maskshop.ru" in some_by_mi["product_url"]
    assert mineral_89["price_rub"] == 2694
    assert "2 капли" in mineral_89["how_to_use"]



def test_step_inference_keeps_toner_as_toner_when_it_says_moisturizing() -> None:
    row = {
        "product_id": "toner_001",
        "name": "Vinoclean Moisturizing Toning Lotion",
        "brand": "Demo Brand",
        "category": "Toning lotion",
        "functional_category": "Увлажнение, комфорт",
        "price_rub": 1200,
    }

    product = normalize_product_row(row, row_number=2)

    assert product["routine_step"] == "toner"


def test_step_inference_keeps_cleansing_tonic_in_toner_step() -> None:
    row = {
        "product_id": "toner_aha_001",
        "name": "AHA-Cleansing Tonic",
        "brand": "Demo Brand",
        "category": "Очищающий тоник с AHA-кислотами",
        "functional_category": "Отшелушивание и тонизирование",
        "price_rub": 900,
    }

    product = normalize_product_row(row, row_number=2)

    assert product["routine_step"] == "toner"


def test_step_inference_keeps_cleanser_as_cleanser_even_with_bha_function() -> None:
    row = {
        "product_id": "cleanser_bha_001",
        "name": "BHA Cleansing Gel",
        "brand": "Demo Brand",
        "category": "Очищающий гель для умывания",
        "functional_category": "BHA, мягкое обновление, увлажнение",
        "price_rub": 900,
    }

    product = normalize_product_row(row, row_number=2)

    assert product["routine_step"] == "cleanser"


def test_step_inference_keeps_serum_as_serum_when_function_is_hydration() -> None:
    row = {
        "product_id": "serum_001",
        "name": "Hydrating Serum",
        "brand": "Demo Brand",
        "category": "Сыворотка",
        "functional_category": "Гидратация, увлажнение",
        "price_rub": 1500,
    }

    product = normalize_product_row(row, row_number=2)

    assert product["routine_step"] == "serum"


def test_step_inference_keeps_explicit_peeling_as_exfoliation() -> None:
    row = {
        "product_id": "peeling_001",
        "name": "Enzyme Peeling",
        "brand": "Demo Brand",
        "category": "Пилинг",
        "functional_category": "Увлажнение, сияние",
        "price_rub": 1500,
    }

    product = normalize_product_row(row, row_number=2)

    assert product["routine_step"] == "exfoliation"
