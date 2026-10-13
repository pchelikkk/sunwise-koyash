import json
from pathlib import Path

from app.algorithms.routine_quality import audit_routine, build_audit_report
from app.algorithms.routine_quality_scenarios import ROUTINE_QUALITY_SCENARIOS
from app.algorithms.scoring import ScoredProduct
from app.importers.product_dataset import load_products_from_dataset
from app.schemas.recommendation import ScoreBreakdown

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPOSITORY_ROOT / "data" / "products.xlsx"
BASELINE_PATH = REPOSITORY_ROOT / "docs" / "routine-quality-baseline.json"


def _scored(external_id: str, step: str, *, total: int = 100) -> ScoredProduct:
    return ScoredProduct(
        product={
            "external_id": external_id,
            "name": external_id,
            "brand": "Test Brand",
            "routine_step": step,
        },
        score=ScoreBreakdown(total=total),
    )


def _codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_valid_basic_routine_has_no_findings() -> None:
    cleanser = _scored("cleanser", "cleanser")
    moisturizer = _scored("moisturizer", "moisturizer")
    routine = {
        "morning": [cleanser, moisturizer, _scored("spf", "spf")],
        "evening": [cleanser, _scored("serum", "serum"), moisturizer],
    }

    findings = audit_routine(
        routine,
        experience="basic",
        skin_type="normal",
        available_steps={"cleanser", "serum", "moisturizer", "spf"},
    )

    assert findings == []


def test_cross_daypart_cleanser_reuse_is_allowed() -> None:
    cleanser = _scored("cleanser", "cleanser")
    moisturizer = _scored("moisturizer", "moisturizer")
    routine = {
        "morning": [cleanser, moisturizer, _scored("spf", "spf")],
        "evening": [cleanser, moisturizer],
    }

    findings = audit_routine(
        routine,
        experience="basic",
        skin_type="normal",
    )

    assert "duplicate_product_in_daypart" not in _codes(findings)


def test_forbidden_daypart_steps_are_contract_errors() -> None:
    routine = {
        "morning": [
            _scored("cleanser-am", "cleanser"),
            _scored("mask", "mask"),
            _scored("peel", "exfoliation"),
            _scored("moisturizer-am", "moisturizer"),
            _scored("spf-am", "spf"),
        ],
        "evening": [
            _scored("cleanser-pm", "cleanser"),
            _scored("moisturizer-pm", "moisturizer"),
            _scored("spf-pm", "spf"),
        ],
    }

    findings = audit_routine(
        routine,
        experience="advanced",
        skin_type="normal",
    )

    assert {"mask_in_morning", "exfoliation_in_morning", "spf_in_evening"}.issubset(
        _codes(findings)
    )
    assert all(
        finding.severity == "error"
        for finding in findings
        if finding.code in {"mask_in_morning", "exfoliation_in_morning", "spf_in_evening"}
    )


def test_duplicate_and_out_of_order_steps_are_contract_errors() -> None:
    routine = {
        "morning": [
            _scored("moisturizer", "moisturizer"),
            _scored("serum", "serum"),
            _scored("serum", "serum"),
            _scored("spf", "spf"),
        ],
        "evening": [
            _scored("cleanser", "cleanser"),
            _scored("moisturizer-pm", "moisturizer"),
        ],
    }

    findings = audit_routine(
        routine,
        experience="basic",
        skin_type="normal",
    )

    assert {
        "duplicate_product_in_daypart",
        "duplicate_step_in_daypart",
        "routine_step_order_violation",
    }.issubset(_codes(findings))


def test_missing_step_records_candidate_availability() -> None:
    cleanser = _scored("cleanser", "cleanser")
    routine = {
        "morning": [cleanser, _scored("spf", "spf")],
        "evening": [cleanser],
    }

    findings = audit_routine(
        routine,
        experience="basic",
        skin_type="normal",
        available_steps={"cleanser", "moisturizer", "spf"},
    )
    moisturizer_findings = [
        finding for finding in findings if finding.routine_step == "moisturizer"
    ]

    assert len(moisturizer_findings) == 2
    assert all(finding.candidate_available is True for finding in moisturizer_findings)


def test_beginner_advanced_steps_are_quality_gaps() -> None:
    routine = {
        "morning": [
            _scored("cleanser-am", "cleanser"),
            _scored("moisturizer-am", "moisturizer"),
            _scored("spf", "spf"),
        ],
        "evening": [
            _scored("cleanser-pm", "cleanser"),
            _scored("treatment", "treatment"),
            _scored("moisturizer-pm", "moisturizer"),
        ],
    }

    findings = audit_routine(
        routine,
        experience="beginner",
        skin_type="normal",
    )

    assert "beginner_advanced_step" in _codes(findings)
    assert any(
        finding.code == "beginner_advanced_step" and finding.severity == "gap"
        for finding in findings
    )


def test_real_dataset_audit_has_no_contract_errors() -> None:
    preview = load_products_from_dataset(DATASET_PATH)
    report = build_audit_report(
        products=preview.products,
        scenarios=ROUTINE_QUALITY_SCENARIOS,
        dataset_error_count=len(preview.errors),
    )

    assert report["dataset"] == {
        "product_count": 69,
        "invalid_row_count": 0,
        "routine_step_distribution": {
            "cleanser": 15,
            "mask": 5,
            "moisturizer": 8,
            "serum": 12,
            "spf": 9,
            "toner": 20,
        },
    }
    assert report["summary"]["scenario_count"] == 8
    assert report["summary"]["contract_error_count"] == 0


def test_real_dataset_audit_captures_known_quality_gaps() -> None:
    preview = load_products_from_dataset(DATASET_PATH)
    report = build_audit_report(
        products=preview.products,
        scenarios=ROUTINE_QUALITY_SCENARIOS,
        dataset_error_count=len(preview.errors),
    )

    assert report["summary"] == {
        "scenario_count": 8,
        "contract_error_count": 0,
        "quality_gap_count": 1,
        "scenario_quality_gap_count": 0,
        "warning_count": 0,
        "ignored_available_step_count": 1,
        "overused_product_count": 0,
        "terminology_gap_count": 0,
    }
    assert report["selection"]["ignored_available_steps"] == ["mask"]
    assert report["selection"]["overused_products"] == []
    assert report["terminology"]["routine_step_enum_missing_known_values"] == []
    assert report["terminology"]["concern_enum_missing_canonical_values"] == []
    assert report["terminology"]["concern_enum_legacy_values"] == []


def test_tracked_baseline_matches_current_algorithm() -> None:
    preview = load_products_from_dataset(DATASET_PATH)
    report = build_audit_report(
        products=preview.products,
        scenarios=ROUTINE_QUALITY_SCENARIOS,
        dataset_error_count=len(preview.errors),
    )
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    assert report == baseline
