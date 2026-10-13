from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Literal

from app.algorithms.filters import apply_hard_filters
from app.algorithms.normalizer import CONCERN_ALIASES, normalized_request
from app.algorithms.routine_builder import build_routine
from app.algorithms.scoring import ScoredProduct, score_products
from app.algorithms.sorting import sort_scored_products
from app.core.enums import Concern, RoutineStep
from app.schemas.recommendation import RecommendationRequest

DAYPARTS = ("morning", "evening")
KNOWN_ROUTINE_STEPS = (
    "cleanser",
    "toner",
    "serum",
    "treatment",
    "moisturizer",
    "spf",
    "exfoliation",
    "mask",
)
MORNING_ORDER = {
    "cleanser": 10,
    "toner": 20,
    "serum": 30,
    "treatment": 40,
    "moisturizer": 50,
    "spf": 60,
}
EVENING_ORDER = {
    "cleanser": 10,
    "exfoliation": 20,
    "toner": 30,
    "serum": 40,
    "treatment": 50,
    "moisturizer": 60,
    "mask": 70,
}
# Eight deterministic scenarios are deliberately broad. Requiring six of eight
# selections avoids treating a single scenario change (5/8) as catalogue-wide
# overuse while still surfacing products that dominate three quarters of users.
DEFAULT_OVERUSE_RATIO = 0.75

Severity = Literal["error", "gap", "warning"]


@dataclass(frozen=True)
class QualityFinding:
    code: str
    severity: Severity
    message: str
    daypart: str | None = None
    routine_step: str | None = None
    product_external_id: str | None = None
    candidate_available: bool | None = None

    def model_dump(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def _product_from_item(item: Any) -> dict[str, Any]:
    if isinstance(item, ScoredProduct):
        return item.product

    if isinstance(item, dict):
        nested = item.get("product")
        if isinstance(nested, dict):
            return nested
        return item

    product = getattr(item, "product", None)
    if isinstance(product, dict):
        return product
    if product is not None and hasattr(product, "model_dump"):
        return product.model_dump()

    raise TypeError(f"Unsupported routine item type: {type(item)!r}")


def _step_from_item(item: Any) -> str:
    if isinstance(item, dict):
        direct = item.get("routine_step") or item.get("step")
        if direct:
            return str(direct)

    direct = getattr(item, "routine_step", None)
    if direct:
        return str(direct)

    return str(_product_from_item(item).get("routine_step") or "")


def _score_from_item(item: Any) -> int | None:
    if isinstance(item, ScoredProduct):
        return item.score.total

    if isinstance(item, dict):
        value = item.get("score")
        if isinstance(value, int):
            return value

    value = getattr(item, "score", None)
    if isinstance(value, int):
        return value

    return None


def _product_id_from_item(item: Any) -> str:
    product = _product_from_item(item)
    return str(product.get("external_id") or product.get("product_id") or "")


def routine_signature(routine: dict[str, list[Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}

    for daypart in DAYPARTS:
        result[daypart] = []
        for item in routine.get(daypart, []):
            product = _product_from_item(item)
            result[daypart].append(
                {
                    "external_id": _product_id_from_item(item),
                    "routine_step": _step_from_item(item),
                    "score": _score_from_item(item),
                    "name": product.get("name"),
                    "brand": product.get("brand"),
                }
            )

    return result


def _missing_step_finding(
    daypart: str,
    step: str,
    code: str,
    *,
    available_steps: set[str] | None,
) -> QualityFinding:
    candidate_available = None if available_steps is None else step in available_steps
    candidate_note = ""
    if candidate_available is True:
        candidate_note = ", although an allowed candidate exists"
    elif candidate_available is False:
        candidate_note = ", and no allowed candidate exists after hard filters"

    return QualityFinding(
        code=code,
        severity="gap",
        message=f"{daypart} routine has no {step}{candidate_note}",
        daypart=daypart,
        routine_step=step,
        candidate_available=candidate_available,
    )


def _audit_daypart(daypart: str, items: list[Any]) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    seen_ids: set[str] = set()
    seen_steps: set[str] = set()
    previous_rank = -1
    order = MORNING_ORDER if daypart == "morning" else EVENING_ORDER

    for item in items:
        step = _step_from_item(item)
        product_id = _product_id_from_item(item)

        if step not in KNOWN_ROUTINE_STEPS:
            findings.append(
                QualityFinding(
                    code="unknown_routine_step",
                    severity="error",
                    message=f"Unknown routine step: {step or '<empty>'}",
                    daypart=daypart,
                    routine_step=step or None,
                    product_external_id=product_id or None,
                )
            )
            continue

        if daypart == "evening" and step == "spf":
            findings.append(
                QualityFinding(
                    code="spf_in_evening",
                    severity="error",
                    message="SPF must not be scheduled in the evening",
                    daypart=daypart,
                    routine_step=step,
                    product_external_id=product_id or None,
                )
            )

        if daypart == "morning" and step in {"exfoliation", "mask"}:
            findings.append(
                QualityFinding(
                    code=f"{step}_in_morning",
                    severity="error",
                    message=f"{step} must not be scheduled in the morning MVP routine",
                    daypart=daypart,
                    routine_step=step,
                    product_external_id=product_id or None,
                )
            )

        if product_id and product_id in seen_ids:
            findings.append(
                QualityFinding(
                    code="duplicate_product_in_daypart",
                    severity="error",
                    message="The same product is repeated inside one daypart",
                    daypart=daypart,
                    routine_step=step,
                    product_external_id=product_id,
                )
            )
        seen_ids.add(product_id)

        if step in seen_steps:
            findings.append(
                QualityFinding(
                    code="duplicate_step_in_daypart",
                    severity="error",
                    message="The same routine step is repeated inside one daypart",
                    daypart=daypart,
                    routine_step=step,
                    product_external_id=product_id or None,
                )
            )
        seen_steps.add(step)

        rank = order.get(step)
        if rank is not None and rank < previous_rank:
            findings.append(
                QualityFinding(
                    code="routine_step_order_violation",
                    severity="error",
                    message=f"{step} is out of the canonical {daypart} order",
                    daypart=daypart,
                    routine_step=step,
                    product_external_id=product_id or None,
                )
            )
        if rank is not None:
            previous_rank = max(previous_rank, rank)

    return findings


def audit_routine(
    routine: dict[str, list[Any]],
    *,
    experience: str,
    skin_type: str,
    available_steps: set[str] | None = None,
) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    morning = list(routine.get("morning", []))
    evening = list(routine.get("evening", []))

    if not morning and not evening:
        findings.append(
            QualityFinding(
                code="empty_routine",
                severity="error",
                message="Recommendation routine is empty",
            )
        )
        return findings

    findings.extend(_audit_daypart("morning", morning))
    findings.extend(_audit_daypart("evening", evening))

    morning_steps = {_step_from_item(item) for item in morning}
    evening_steps = {_step_from_item(item) for item in evening}

    if "cleanser" not in morning_steps:
        findings.append(
            _missing_step_finding(
                "morning",
                "cleanser",
                "missing_morning_cleanser",
                available_steps=available_steps,
            )
        )
    if "cleanser" not in evening_steps:
        findings.append(
            _missing_step_finding(
                "evening",
                "cleanser",
                "missing_evening_cleanser",
                available_steps=available_steps,
            )
        )
    if "spf" not in morning_steps:
        findings.append(
            _missing_step_finding(
                "morning",
                "spf",
                "missing_morning_spf",
                available_steps=available_steps,
            )
        )
    if "moisturizer" not in morning_steps:
        findings.append(
            _missing_step_finding(
                "morning",
                "moisturizer",
                "missing_morning_moisturizer",
                available_steps=available_steps,
            )
        )
    if "moisturizer" not in evening_steps:
        findings.append(
            _missing_step_finding(
                "evening",
                "moisturizer",
                "missing_evening_moisturizer",
                available_steps=available_steps,
            )
        )

    normalized_experience = experience.strip().lower()
    if normalized_experience in {"beginner", "minimal"}:
        unique_ids = {
            _product_id_from_item(item)
            for item in [*morning, *evening]
            if _product_id_from_item(item)
        }
        if len(unique_ids) > 4:
            findings.append(
                QualityFinding(
                    code="beginner_routine_overloaded",
                    severity="gap",
                    message="Beginner/minimal routine contains more than four unique products",
                )
            )

        advanced_steps = {_step_from_item(item) for item in [*morning, *evening]}.intersection(
            {"treatment", "exfoliation", "mask"}
        )
        for step in sorted(advanced_steps):
            findings.append(
                QualityFinding(
                    code="beginner_advanced_step",
                    severity="gap",
                    message=f"Beginner/minimal routine contains advanced step: {step}",
                    routine_step=step,
                )
            )

    if skin_type.strip().lower() == "sensitive" and "moisturizer" not in evening_steps:
        findings.append(
            QualityFinding(
                code="sensitive_missing_evening_moisturizer",
                severity="warning",
                message="Sensitive routine has no evening moisturizer",
                daypart="evening",
                routine_step="moisturizer",
            )
        )

    return findings


def _scenario_report(
    *,
    scenario: dict[str, Any],
    products: list[dict[str, Any]],
) -> tuple[dict[str, Any], Counter[str], Counter[str]]:
    request = normalized_request(RecommendationRequest(**scenario["input"]))
    filter_result = apply_hard_filters(products=products, request=request)
    scored = score_products(filter_result.allowed_products, request)
    sorted_products = sort_scored_products(scored)
    routine = build_routine(
        sorted_products,
        request.experience,
        request.routine_preference,
    )
    available_steps = {
        str(product.get("routine_step") or "")
        for product in filter_result.allowed_products
        if product.get("routine_step")
    }
    findings = audit_routine(
        routine,
        experience=request.experience,
        skin_type=request.skin_type,
        available_steps=available_steps,
    )
    signature = routine_signature(routine)

    step_counter: Counter[str] = Counter()
    scenario_product_counter: Counter[str] = Counter()

    for daypart in DAYPARTS:
        for item in signature[daypart]:
            step_counter[item["routine_step"]] += 1
            product_id = item["external_id"]
            if product_id:
                scenario_product_counter[product_id] = 1

    return (
        {
            "scenario_id": scenario["id"],
            "title": scenario["title"],
            "input": request.model_dump(exclude={"anonymous_id", "skin_diagnostic_answers"}),
            "allowed_product_count": len(filter_result.allowed_products),
            "filter_reasons": filter_result.filter_reasons,
            "routine": signature,
            "findings": [finding.model_dump() for finding in findings],
            "contract_error_count": sum(finding.severity == "error" for finding in findings),
            "quality_gap_count": sum(finding.severity == "gap" for finding in findings),
            "warning_count": sum(finding.severity == "warning" for finding in findings),
        },
        step_counter,
        scenario_product_counter,
    )


def _terminology_report(products: list[dict[str, Any]]) -> dict[str, list[str]]:
    dataset_steps = {str(product.get("routine_step") or "") for product in products} - {""}
    enum_steps = {item.value for item in RoutineStep}
    known_steps = set(KNOWN_ROUTINE_STEPS)
    canonical_concerns = {
        "acne",
        "age_changes",
        "dehydration",
        "dryness",
        "dullness",
        "pigmentation",
        "pores",
        "post_acne",
        "reactivity",
        "redness",
        "sebum",
        "uneven_tone",
        "unknown",
    }
    canonical_concerns.update(CONCERN_ALIASES.values())
    canonical_concerns.update(
        str(concern) for product in products for concern in product.get("concerns", []) if concern
    )
    enum_concerns = {item.value for item in Concern}

    return {
        "dataset_routine_steps": sorted(dataset_steps),
        "known_routine_steps": sorted(known_steps),
        "routine_step_enum_values": sorted(enum_steps),
        "routine_step_enum_missing_known_values": sorted(known_steps - enum_steps),
        "canonical_concern_values": sorted(canonical_concerns),
        "concern_enum_values": sorted(enum_concerns),
        "concern_enum_missing_canonical_values": sorted(canonical_concerns - enum_concerns),
        "concern_enum_legacy_values": sorted(enum_concerns - canonical_concerns),
    }


def build_audit_report(
    *,
    products: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    dataset_error_count: int = 0,
    overuse_ratio: float = DEFAULT_OVERUSE_RATIO,
) -> dict[str, Any]:
    dataset_step_counts = Counter(
        str(product.get("routine_step") or "unknown") for product in products
    )
    selected_step_counts: Counter[str] = Counter()
    selected_product_scenarios: Counter[str] = Counter()
    scenario_reports: list[dict[str, Any]] = []

    for scenario in scenarios:
        report, step_counts, scenario_product_counts = _scenario_report(
            scenario=scenario,
            products=products,
        )
        scenario_reports.append(report)
        selected_step_counts.update(step_counts)
        selected_product_scenarios.update(scenario_product_counts)

    product_lookup = {
        str(product.get("external_id")): product
        for product in products
        if product.get("external_id")
    }
    scenario_count = len(scenarios)
    top_selected_products = []

    for product_id, count in selected_product_scenarios.most_common(10):
        ratio = count / scenario_count if scenario_count else 0.0
        product = product_lookup.get(product_id, {})
        top_selected_products.append(
            {
                "external_id": product_id,
                "name": product.get("name"),
                "brand": product.get("brand"),
                "routine_step": product.get("routine_step"),
                "selected_scenario_count": count,
                "scenario_ratio": round(ratio, 3),
            }
        )

    overused_products = [
        item for item in top_selected_products if item["scenario_ratio"] >= overuse_ratio
    ]

    ignored_steps = sorted(
        step
        for step, count in dataset_step_counts.items()
        if count > 0 and selected_step_counts.get(step, 0) == 0
    )
    terminology = _terminology_report(products)
    scenario_errors = sum(item["contract_error_count"] for item in scenario_reports)
    scenario_gaps = sum(item["quality_gap_count"] for item in scenario_reports)
    scenario_warnings = sum(item["warning_count"] for item in scenario_reports)
    dataset_gaps = len(ignored_steps) + len(overused_products)
    terminology_gaps = len(terminology["routine_step_enum_missing_known_values"])
    terminology_gaps += len(terminology["concern_enum_missing_canonical_values"])
    terminology_gaps += len(terminology["concern_enum_legacy_values"])

    return {
        "schema_version": "routine-quality-audit-v1",
        "algorithm_version": "rule-based-v2",
        "dataset": {
            "product_count": len(products),
            "invalid_row_count": dataset_error_count,
            "routine_step_distribution": dict(sorted(dataset_step_counts.items())),
        },
        "summary": {
            "scenario_count": scenario_count,
            "contract_error_count": scenario_errors,
            "quality_gap_count": scenario_gaps + dataset_gaps + terminology_gaps,
            "scenario_quality_gap_count": scenario_gaps,
            "warning_count": scenario_warnings,
            "ignored_available_step_count": len(ignored_steps),
            "overused_product_count": len(overused_products),
            "terminology_gap_count": terminology_gaps,
        },
        "selection": {
            "selected_step_distribution": dict(sorted(selected_step_counts.items())),
            "ignored_available_steps": ignored_steps,
            "top_selected_products": top_selected_products,
            "overused_products": overused_products,
        },
        "terminology": terminology,
        "scenarios": scenario_reports,
    }
