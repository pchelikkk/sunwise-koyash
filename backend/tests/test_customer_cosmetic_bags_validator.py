import json

from scripts.validate_customer_cosmetic_bags import validate_export


def _product(
    product_id: str,
    *,
    step: str = "cleanser",
    source: str | None = "dataset",
    verified: bool = True,
) -> dict:
    return {
        "external_id": product_id,
        "name": product_id,
        "brand": "Dataset Brand",
        "routine_step": step,
        "source": source,
        "dataset_verified": verified,
        "dataset_external_id": product_id,
    }


def _item(product_id: str, *, step: str = "cleanser", part: str = "morning") -> dict:
    return {
        "part": part,
        "step": step,
        "product": _product(product_id, step=step),
        "llm_user_prompt_context": {
            "name": product_id,
            "step": step,
        },
    }


def _sample(index: int, product_id: str) -> dict:
    return {
        "scenario_id": f"scenario_{index}",
        "title": f"Сценарий {index}",
        "quality_issues": [],
        "quality_warnings": [],
        "dataset_product_ids": [product_id],
        "cosmetic_bag_unique_products": [_product(product_id)],
        "routine": {
            "morning": [_item(product_id, step="cleanser", part="morning")],
            "evening": [],
        },
    }


def _payload(samples: list[dict]) -> dict:
    return {
        "dataset_provenance": {
            "database": "koyash",
            "products_total": 69,
            "dataset_products": 69,
            "sample_like_products": 0,
            "dataset_products_loaded_for_export": 69,
            "required_product_source": "dataset",
            "all_export_products_verified_dataset": True,
            "exported_dataset_product_count": 5,
            "exported_dataset_product_ids": [f"product_{index}" for index in range(5)],
        },
        "summary": {
            "sample_count": 8,
            "quality_issue_count": 0,
            "quality_warning_count": 0,
            "unique_cosmetic_bag_count": 5,
            "all_products_verified_dataset": True,
            "export_ok": True,
        },
        "samples": samples,
    }


def test_validator_accepts_clean_utf8_dataset_verified_export(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is True
    assert report["unique_cosmetic_bag_count"] == 5


def test_validator_rejects_mojibake(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["title"] = "╨Ъ╨╛╨╝╨▒╨╕"
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("mojibake" in error for error in report["errors"])


def test_validator_rejects_spf_in_evening(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["routine"] = {
        "morning": [],
        "evening": [_item("spf_bad", step="spf", part="evening")],
    }
    samples[0]["cosmetic_bag_unique_products"] = [_product("spf_bad", step="spf")]
    samples[0]["dataset_product_ids"] = ["spf_bad"]
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("spf_not_morning" in error for error in report["errors"])


def test_validator_rejects_non_dataset_product_source(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["cosmetic_bag_unique_products"][0] = _product(
        "product_0",
        source=None,
        verified=False,
    )
    samples[0]["routine"]["morning"][0]["product"] = _product(
        "product_0",
        source=None,
        verified=False,
    )
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("source_is_not_dataset" in error for error in report["errors"])
    assert any("dataset_verified_is_not_true" in error for error in report["errors"])
