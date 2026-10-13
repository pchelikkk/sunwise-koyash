import argparse
import json
import sys
from pathlib import Path
from typing import Any

SAMPLE_BRANDS = {
    "Koyash Sample",
    "Soft Lab",
    "Clear Skin",
    "Sun Basic",
    "KOYASH Test",
}

MOJIBAKE_MARKERS = ("╨", "╤", "Ð", "Ñ", "â")


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]

    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            result.extend(_walk_strings(key))
            result.extend(_walk_strings(item))
        return result

    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_walk_strings(item))
        return result

    return []


def _routine_items(sample: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    routine = sample.get("routine") or {}
    result: list[tuple[str, dict[str, Any]]] = []

    for part in ("morning", "evening"):
        for item in routine.get(part) or []:
            result.append((part, item))

    return result


def _item_step(item: dict[str, Any]) -> str:
    product = item.get("product") or {}
    return str(item.get("step") or item.get("routine_step") or product.get("routine_step") or "")


def _unique_product_ids(sample: dict[str, Any]) -> tuple[str, ...]:
    products = sample.get("cosmetic_bag_unique_products") or []
    ids = [str(product.get("external_id")) for product in products if product.get("external_id")]

    if not ids:
        for _, item in _routine_items(sample):
            product = item.get("product") or {}
            product_id = product.get("external_id")
            if product_id:
                ids.append(str(product_id))

    return tuple(sorted(set(ids)))


def _validate_export_product(
    *,
    errors: list[str],
    scenario_id: str,
    product: dict[str, Any],
    location: str,
) -> None:
    product_id = product.get("external_id") or "unknown"
    brand = product.get("brand")
    source = product.get("source")
    dataset_verified = product.get("dataset_verified")
    dataset_external_id = product.get("dataset_external_id")

    if brand in SAMPLE_BRANDS:
        errors.append(f"{scenario_id}:{location}:sample_brand:{brand}:{product_id}")

    if source != "dataset":
        errors.append(f"{scenario_id}:{location}:source_is_not_dataset:{source}:{product_id}")

    if dataset_verified is not True:
        errors.append(f"{scenario_id}:{location}:dataset_verified_is_not_true:{product_id}")

    if dataset_external_id != product_id:
        errors.append(
            f"{scenario_id}:{location}:dataset_external_id_mismatch:{dataset_external_id}:{product_id}"
        )

    if not product.get("name") or not product.get("brand"):
        errors.append(f"{scenario_id}:{location}:missing_product_identity:{product_id}")

    if not product.get("routine_step"):
        errors.append(f"{scenario_id}:{location}:missing_routine_step:{product_id}")


def validate_export(path: str | Path) -> dict[str, Any]:
    export_path = Path(path)
    raw_text = export_path.read_text(encoding="utf-8-sig")
    data = json.loads(raw_text)

    errors: list[str] = []
    warnings: list[str] = []

    if any(marker in raw_text for marker in MOJIBAKE_MARKERS):
        errors.append("mojibake_detected")

    summary = data.get("summary") or {}
    provenance = data.get("dataset_provenance") or {}
    samples = data.get("samples") or []

    if summary.get("sample_count") != 8:
        errors.append(f"expected_8_samples_got_{summary.get('sample_count')}")

    if len(samples) != 8:
        errors.append(f"expected_8_sample_items_got_{len(samples)}")

    if summary.get("quality_issue_count") != 0:
        errors.append(f"quality_issue_count_not_zero:{summary.get('quality_issue_count')}")

    if summary.get("export_ok") is not True:
        errors.append("summary_export_ok_is_not_true")

    if summary.get("all_products_verified_dataset") is not True:
        errors.append("summary_all_products_verified_dataset_is_not_true")

    if provenance.get("required_product_source") != "dataset":
        errors.append("dataset_provenance_required_product_source_is_not_dataset")

    if provenance.get("all_export_products_verified_dataset") is not True:
        errors.append("dataset_provenance_all_export_products_verified_dataset_is_not_true")

    if int(provenance.get("dataset_products") or 0) <= 0:
        errors.append("dataset_provenance_has_no_dataset_products")

    if int(provenance.get("sample_like_products") or 0) != 0:
        errors.append(f"dataset_provenance_sample_like_not_zero:{provenance.get('sample_like_products')}")

    strings = _walk_strings(data)
    bad_strings = [text for text in strings if any(marker in text for marker in MOJIBAKE_MARKERS)]

    if bad_strings:
        errors.append(f"mojibake_strings:{len(bad_strings)}")

    unique_bags = set()

    for sample in samples:
        scenario_id = sample.get("scenario_id", "unknown")
        sample_issues = sample.get("quality_issues") or []

        if sample_issues:
            errors.append(f"{scenario_id}:quality_issues:{sample_issues}")

        product_ids = _unique_product_ids(sample)

        if not product_ids:
            errors.append(f"{scenario_id}:empty_cosmetic_bag")
        else:
            unique_bags.add(product_ids)

        for index, product in enumerate(sample.get("cosmetic_bag_unique_products") or []):
            _validate_export_product(
                errors=errors,
                scenario_id=scenario_id,
                product=product,
                location=f"unique_products[{index}]",
            )

        for part, item in _routine_items(sample):
            step = _item_step(item)
            product = item.get("product") or {}
            product_id = product.get("external_id") or "unknown"

            _validate_export_product(
                errors=errors,
                scenario_id=scenario_id,
                product=product,
                location=f"routine.{part}",
            )

            if step == "spf" and part != "morning":
                errors.append(f"{scenario_id}:spf_not_morning:{product_id}")

            if step == "exfoliation" and part == "morning":
                errors.append(f"{scenario_id}:exfoliation_in_morning:{product_id}")

            llm_context = item.get("llm_user_prompt_context") or {}
            if not llm_context.get("name") or not llm_context.get("step"):
                warnings.append(f"{scenario_id}:weak_llm_context:{product_id}")
            if llm_context.get("matched_concerns") != item.get("matched_concerns"):
                errors.append(f"{scenario_id}:llm_matched_concerns_mismatch:{product_id}")

    if len(unique_bags) < 5:
        errors.append(f"expected_at_least_5_unique_cosmetic_bags_got_{len(unique_bags)}")

    return {
        "path": str(export_path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "dataset_provenance": provenance,
        "unique_cosmetic_bag_count": len(unique_bags),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Validate KOYASH customer cosmetic bag export JSON."
    )
    parser.add_argument("path")
    args = parser.parse_args(argv)

    report = validate_export(args.path)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
