import argparse
import json
from pathlib import Path
from typing import Any

from app.algorithms.routine_quality import build_audit_report
from app.algorithms.routine_quality_scenarios import ROUTINE_QUALITY_SCENARIOS
from app.importers.product_dataset import load_products_from_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit KOYASH routine quality against the real product dataset.",
    )
    parser.add_argument(
        "--dataset",
        default="/data/products.xlsx",
        help="Path to products.xlsx or CSV dataset.",
    )
    parser.add_argument(
        "--output",
        help="Write the deterministic JSON report to this path.",
    )
    parser.add_argument(
        "--fail-on-contract-errors",
        action="store_true",
        help="Exit with code 2 when any invalid routine contract is detected.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    return parser.parse_args()


def _json_text(report: dict[str, Any], *, compact: bool) -> str:
    if compact:
        return json.dumps(report, ensure_ascii=False, sort_keys=True)
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)


def main() -> int:
    args = parse_args()
    preview = load_products_from_dataset(Path(args.dataset))
    report = build_audit_report(
        products=preview.products,
        scenarios=ROUTINE_QUALITY_SCENARIOS,
        dataset_error_count=len(preview.errors),
    )
    text = _json_text(report, compact=args.compact)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"Routine quality report written to: {output_path}")
    else:
        print(text)

    summary = report["summary"]
    print(
        "Routine quality summary: "
        f"scenarios={summary['scenario_count']}, "
        f"contract_errors={summary['contract_error_count']}, "
        f"quality_gaps={summary['quality_gap_count']}"
    )

    if args.fail_on_contract_errors and summary["contract_error_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
