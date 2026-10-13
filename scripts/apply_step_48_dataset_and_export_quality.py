from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def replace_block(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


# 1. Fix dataset routine_step inference.
importer_path = ROOT / "backend/app/importers/product_dataset.py"
text = importer_path.read_text(encoding="utf-8")

new_infer_step = r'''
def _contains_any(text: str, markers: list[str]) -> bool:
    normalized = normalize_header(text)

    return any(normalize_header(marker) in normalized for marker in markers)


def _infer_step(row: dict[str, Any], name: str, category: str, functional_category: str) -> str:
    explicit = _clean_value(row.get("routine_step"))

    if explicit:
        return _normalize_by_alias(explicit, STEP_ALIASES, default="other")

    # Important:
    # routine_step must describe the product type, not the marketing function.
    # "Moisturizing toner" is still toner.
    # "BHA cleansing gel" is still cleanser.
    # "Hydrating serum" is still serum.
    identity_text = normalize_header(f"{category} {name}")
    all_text = normalize_header(f"{category} {name} {functional_category}")

    spf_markers = [
        "spf",
        "sunscreen",
        "санскрин",
        "солнцезащит",
        "солнцезащитный",
        "защита от солнца",
    ]
    cleanser_markers = [
        "cleanser",
        "cleansing",
        "очищение",
        "очищающий",
        "очищающая",
        "умывание",
        "гель для умывания",
        "пенка",
        "мицеллярная вода",
        "мицеллярная пенка",
        "foam cleanser",
        "cleansing gel",
        "gel cleanser",
    ]
    toner_markers = [
        "toner",
        "tonic",
        "toning",
        "тоник",
        "тонер",
        "тонизир",
        "эссенция",
        "essence",
        "lotion toner",
        "toning lotion",
    ]
    serum_markers = ["serum", "сыворотка", "актив"]
    mask_markers = ["mask", "маска"]
    exfoliation_markers = [
        "exfoliant",
        "exfoliation",
        "peeling",
        "пилинг",
        "эксфолиант",
        "эксфолиация",
        "скраб",
    ]
    moisturizer_markers = [
        "moisturizer",
        "moisturiser",
        "cream",
        "крем",
        "гель крем",
        "гель-крем",
        "увлажняющий крем",
        "эмульсия",
        "дневной крем",
        "ночной крем",
    ]

    # Product identity from category/name has priority.
    if _contains_any(identity_text, spf_markers):
        return "spf"

    if _contains_any(identity_text, cleanser_markers):
        return "cleanser"

    if _contains_any(identity_text, toner_markers):
        return "toner"

    if _contains_any(identity_text, serum_markers):
        return "serum"

    if _contains_any(identity_text, mask_markers):
        return "mask"

    if _contains_any(identity_text, exfoliation_markers):
        return "exfoliation"

    if _contains_any(identity_text, moisturizer_markers):
        return "moisturizer"

    # Fallback only when category/name are not enough.
    if _contains_any(all_text, spf_markers):
        return "spf"

    if _contains_any(all_text, cleanser_markers):
        return "cleanser"

    if _contains_any(all_text, toner_markers):
        return "toner"

    if _contains_any(all_text, serum_markers):
        return "serum"

    if _contains_any(all_text, mask_markers):
        return "mask"

    if _contains_any(all_text, exfoliation_markers):
        return "exfoliation"

    if _contains_any(all_text, moisturizer_markers):
        return "moisturizer"

    return "other"
'''

text = replace_block(
    text,
    "def _infer_step(",
    "\ndef _infer_skin_types",
    new_infer_step,
)
importer_path.write_text(text, encoding="utf-8")


# 2. Fix reactivity/sensitivity normalization.
normalizer_path = ROOT / "backend/app/algorithms/normalizer.py"
text = normalizer_path.read_text(encoding="utf-8")

new_concern_aliases = '''CONCERN_ALIASES = {
    "reactivity": "reactivity",
    "sensitivity": "reactivity",
    "sensitive": "reactivity",
    "реактивность": "reactivity",
    "чувствительность": "reactivity",
    "чувствительная кожа": "reactivity",
    "unknown": "unknown",
    "затрудняюсь ответить": "unknown",
    "пока не знаю": "unknown",
}'''

text = replace_block(
    text,
    "CONCERN_ALIASES = {",
    "\n\nVALUE_ALIASES",
    new_concern_aliases,
)
normalizer_path.write_text(text, encoding="utf-8")


# 3. Make customer export script support safe file output.
export_path = ROOT / "backend/scripts/export_customer_cosmetic_bags.py"
text = export_path.read_text(encoding="utf-8")

text = text.replace(
    "import json\nimport os\nimport sys\nfrom typing import Any",
    "import argparse\nimport json\nimport os\nimport sys\nfrom pathlib import Path\nfrom typing import Any",
)

new_main = r'''
def build_export() -> dict[str, Any]:
    result = {
        "purpose": "KOYASH customer review export for LLM prompt tuning",
        "api_base_url": API_BASE_URL,
        "important_note": (
            "Product choice is deterministic. LLM must only rewrite explanations "
            "using llm_user_prompt_context."
        ),
        "samples": [],
    }

    with httpx.Client(timeout=30.0) as client:
        for scenario in SCENARIOS:
            result["samples"].append(_request_recommendation(client, scenario))

    issue_count = sum(len(sample["quality_issues"]) for sample in result["samples"])
    warning_count = sum(len(sample.get("quality_warnings", [])) for sample in result["samples"])
    unique_bag_count = len(
        {
            tuple(
                sorted(
                    str(product.get("external_id"))
                    for product in sample.get("cosmetic_bag_unique_products", [])
                    if product.get("external_id")
                )
            )
            for sample in result["samples"]
        }
    )

    result["summary"] = {
        "sample_count": len(result["samples"]),
        "quality_issue_count": issue_count,
        "quality_warning_count": warning_count,
        "unique_cosmetic_bag_count": unique_bag_count,
        "export_ok": issue_count == 0,
    }

    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Export KOYASH customer cosmetic bag samples as UTF-8 JSON.",
    )
    parser.add_argument(
        "--output",
        help=(
            "Optional output path. Use this inside Docker and copy the file with "
            "docker cp to avoid PowerShell encoding issues."
        ),
    )
    args = parser.parse_args(argv)

    result = build_export()
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"Export written to {output_path}", file=sys.stderr)
    else:
        print(rendered, end="")

    if result["summary"]["quality_issue_count"] != 0:
        sys.exit(1)
'''

text = text[: text.index("def main() -> None:")] + new_main + '\n\nif __name__ == "__main__":\n    main()\n'
export_path.write_text(text, encoding="utf-8")


# 4. Add customer JSON validator.
validator_path = ROOT / "backend/scripts/validate_customer_cosmetic_bags.py"
validator_path.write_text(r'''
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


def validate_export(path: str | Path) -> dict[str, Any]:
    export_path = Path(path)
    raw_text = export_path.read_text(encoding="utf-8-sig")
    data = json.loads(raw_text)

    errors: list[str] = []
    warnings: list[str] = []

    if any(marker in raw_text for marker in MOJIBAKE_MARKERS):
        errors.append("mojibake_detected")

    summary = data.get("summary") or {}
    samples = data.get("samples") or []

    if summary.get("sample_count") != 8:
        errors.append(f"expected_8_samples_got_{summary.get('sample_count')}")

    if len(samples) != 8:
        errors.append(f"expected_8_sample_items_got_{len(samples)}")

    if summary.get("quality_issue_count") != 0:
        errors.append(f"quality_issue_count_not_zero:{summary.get('quality_issue_count')}")

    if summary.get("export_ok") is not True:
        errors.append("summary_export_ok_is_not_true")

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

        for part, item in _routine_items(sample):
            step = _item_step(item)
            product = item.get("product") or {}
            product_id = product.get("external_id") or "unknown"
            brand = product.get("brand")
            source = product.get("source")

            if brand in SAMPLE_BRANDS:
                errors.append(f"{scenario_id}:sample_brand:{brand}:{product_id}")

            if source not in {None, "dataset"}:
                errors.append(f"{scenario_id}:non_dataset_source:{source}:{product_id}")

            if step == "spf" and part != "morning":
                errors.append(f"{scenario_id}:spf_not_morning:{product_id}")

            if step == "exfoliation" and part == "morning":
                errors.append(f"{scenario_id}:exfoliation_in_morning:{product_id}")

            if not product.get("name") or not product.get("brand"):
                errors.append(f"{scenario_id}:missing_product_identity:{product_id}")

            llm_context = item.get("llm_user_prompt_context") or {}
            if not llm_context.get("name") or not llm_context.get("step"):
                warnings.append(f"{scenario_id}:weak_llm_context:{product_id}")

    if len(unique_bags) < 5:
        errors.append(f"expected_at_least_5_unique_cosmetic_bags_got_{len(unique_bags)}")

    return {
        "path": str(export_path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "unique_cosmetic_bag_count": len(unique_bags),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate KOYASH customer cosmetic bag export JSON.")
    parser.add_argument("path")
    args = parser.parse_args(argv)

    report = validate_export(args.path)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
'''.lstrip(), encoding="utf-8")


# 5. Add importer regression tests.
product_test_path = ROOT / "backend/tests/test_product_dataset_importer.py"
text = product_test_path.read_text(encoding="utf-8")

append_tests = r'''


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
'''

if "test_step_inference_keeps_toner_as_toner_when_it_says_moisturizing" not in text:
    product_test_path.write_text(text + append_tests, encoding="utf-8")


# 6. Add normalizer tests.
(ROOT / "backend/tests/test_request_normalizer_contract.py").write_text(r'''
from app.algorithms.normalizer import normalized_request
from app.schemas.recommendation import RecommendationRequest


def _request(concerns: list[str]) -> RecommendationRequest:
    return RecommendationRequest(
        age=24,
        skin_type="combination",
        concerns=concerns,
        budget="balanced",
        excluded_ingredients=[],
        custom_restrictions=[],
        experience="guided",
        values=[],
        anonymous_id="normalizer-test",
    )


def test_reactivity_stays_aligned_with_dataset_concern() -> None:
    normalized = normalized_request(_request(["reactivity", "unknown"]))

    assert normalized.concerns == ["reactivity"]


def test_sensitivity_alias_maps_to_reactivity() -> None:
    normalized = normalized_request(_request(["sensitivity", "чувствительность", "реактивность"]))

    assert normalized.concerns == ["reactivity"]
'''.lstrip(), encoding="utf-8")


# 7. Add JSON validator tests.
(ROOT / "backend/tests/test_customer_cosmetic_bags_validator.py").write_text(r'''
import json

from scripts.validate_customer_cosmetic_bags import validate_export


def _item(product_id: str, *, step: str = "cleanser", part: str = "morning") -> dict:
    return {
        "part": part,
        "step": step,
        "product": {
            "external_id": product_id,
            "name": product_id,
            "brand": "Dataset Brand",
            "routine_step": step,
            "source": "dataset",
        },
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
        "cosmetic_bag_unique_products": [
            {
                "external_id": product_id,
                "name": product_id,
                "brand": "Dataset Brand",
                "routine_step": "cleanser",
                "source": "dataset",
            }
        ],
        "routine": {
            "morning": [_item(product_id, step="cleanser", part="morning")],
            "evening": [],
        },
    }


def test_validator_accepts_clean_utf8_export(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    payload = {
        "summary": {
            "sample_count": 8,
            "quality_issue_count": 0,
            "quality_warning_count": 0,
            "unique_cosmetic_bag_count": 5,
            "export_ok": True,
        },
        "samples": samples,
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is True
    assert report["unique_cosmetic_bag_count"] == 5


def test_validator_rejects_mojibake(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["title"] = "╨Ъ╨╛╨╝╨▒╨╕"
    payload = {
        "summary": {
            "sample_count": 8,
            "quality_issue_count": 0,
            "export_ok": True,
        },
        "samples": samples,
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("mojibake" in error for error in report["errors"])


def test_validator_rejects_spf_in_evening(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["routine"] = {
        "morning": [],
        "evening": [_item("spf_bad", step="spf", part="evening")],
    }
    samples[0]["cosmetic_bag_unique_products"] = [
        {
            "external_id": "spf_bad",
            "name": "spf_bad",
            "brand": "Dataset Brand",
            "routine_step": "spf",
            "source": "dataset",
        }
    ]
    payload = {
        "summary": {
            "sample_count": 8,
            "quality_issue_count": 0,
            "export_ok": True,
        },
        "samples": samples,
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("spf_not_morning" in error for error in report["errors"])
'''.lstrip(), encoding="utf-8")


# 8. Remove debug output and ignore it.
debug_file = ROOT / "docs/customer-review/export-debug-output.txt"
if debug_file.exists():
    debug_file.unlink()

gitignore_path = ROOT / ".gitignore"
gitignore_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

if "docs/customer-review/export-debug-output.txt" not in gitignore_text:
    gitignore_path.write_text(
        gitignore_text.rstrip() + "\n\ndocs/customer-review/export-debug-output.txt\n",
        encoding="utf-8",
    )

print("Step 4.8 patch applied successfully.")