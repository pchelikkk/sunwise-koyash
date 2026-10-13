# KOYASH routine quality contract

## Purpose

This contract defines machine-checkable rules for the deterministic KOYASH
morning/evening routine. Step 4.10A adds the contract and a reproducible audit;
it does not change product selection, filtering, scoring, or routine building.

The contract separates three classes of findings:

- `error`: an invalid schedule that must never be returned;
- `gap`: valid output that does not yet meet the intended product quality;
- `warning`: additional context that requires review but is not a standalone
  contract failure.

The audit CLI may fail on `error` findings while still recording the current
quality gaps as a baseline for Step 4.10B.

## Supported routine steps

The runtime contract recognizes:

```text
cleanser
toner
serum
treatment
moisturizer
spf
exfoliation
mask
```

The audit reports drift between this runtime vocabulary, the product dataset,
and `RoutineStep` enum values.

## Daypart rules

### Morning

Canonical order:

```text
cleanser -> toner -> serum -> treatment -> moisturizer -> spf
```

Hard rules:

- SPF is allowed only in the morning;
- mask is not allowed in the morning MVP routine;
- exfoliation is not allowed in the morning MVP routine;
- a step must not be repeated inside the same daypart;
- a product must not be repeated inside the same daypart;
- the schedule must follow the canonical order.

Quality targets:

- cleanser should be present;
- moisturizer should be present;
- SPF should be present.

### Evening

Canonical order:

```text
cleanser -> exfoliation -> toner -> serum -> treatment -> moisturizer -> mask
```

Hard rules:

- SPF is not allowed in the evening;
- a step must not be repeated inside the same daypart;
- a product must not be repeated inside the same daypart;
- the schedule must follow the canonical order.

Quality targets:

- cleanser should be present;
- moisturizer should be present.

The same cleanser may be scheduled in both morning and evening. It remains one
unique product in the cosmetic bag and two uses in the schedule.

## Candidate-aware missing-step findings

When a base step is missing, the audit records whether a product for that step
survived the hard filters:

- `candidate_available: true` means the routine builder ignored an allowed
  candidate;
- `candidate_available: false` means filtering or dataset coverage left no
  allowed candidate;
- omitted means the routine was audited without candidate context.

This distinction prevents Step 4.10B from treating builder defects and filtering
coverage defects as the same problem.

## Beginner and minimal routines

For `beginner` and `minimal` experience levels:

- more than four unique products is a quality gap;
- treatment, exfoliation, and mask steps are quality gaps unless explicitly
  introduced by a later reviewed contract.

## Sensitive routines

A sensitive routine without an evening moisturizer is recorded as a warning in
addition to the missing-step gap. The missing-step finding states whether an
allowed moisturizer candidate exists.

## Dataset-wide checks

The deterministic audit also reports:

- product count and invalid dataset rows;
- product distribution by `routine_step`;
- selected step distribution across eight fixed scenarios;
- available dataset steps never selected by the builder;
- products selected in at least 75% of scenarios (six of the eight fixed
  scenarios), so one changed scenario cannot create a false catalogue-wide
  overuse alert;
- routine-step enum drift;
- concern vocabulary drift.

## Baseline policy

`docs/routine-quality-baseline.json` is a deterministic snapshot produced from:

```text
data/products.xlsx
rule-based-v2 filters/scoring/sorting/routine builder
8 fixed audit scenarios
```

The test suite compares the current report with this tracked baseline. A future
algorithm change must update the baseline intentionally and explain each changed
metric in its Merge Request. Silently weakening or deleting the snapshot test is
not an acceptable way to make Step 4.10B pass.

## CLI

Generate a report without failing on known quality gaps:

```bash
python scripts/audit_routine_quality.py \
  --dataset /data/products.xlsx \
  --output /tmp/routine-quality-report.json
```

Fail only when an invalid routine contract is detected:

```bash
python scripts/audit_routine_quality.py \
  --dataset /data/products.xlsx \
  --output /tmp/routine-quality-report.json \
  --fail-on-contract-errors
```
