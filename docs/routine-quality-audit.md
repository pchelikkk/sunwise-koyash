# KOYASH Step 4.10A routine quality audit

## Scope

Step 4.10A introduces a deterministic contract, eight fixed customer scenarios,
a dataset-wide audit CLI, regression tests, and a tracked baseline. It does not
change the recommendation algorithm.

Dataset:

```text
data/products.xlsx
69 valid products
0 invalid rows
```

Algorithm baseline:

```text
rule-based-v1
```

## Baseline summary

```json
{
  "scenario_count": 8,
  "contract_error_count": 0,
  "quality_gap_count": 23,
  "scenario_quality_gap_count": 9,
  "warning_count": 1,
  "ignored_available_step_count": 2,
  "overused_product_count": 2,
  "terminology_gap_count": 10
}
```

The current routine builder does not create invalid schedules in the audited
scenarios: SPF remains in the morning, mask/exfoliation are not placed in the
morning, and step order is valid. The audit nevertheless confirms several
systemic quality gaps that Step 4.10B must address.

## Finding 1: morning moisturizer is missing in all scenarios

All eight scenarios lack a morning moisturizer.

For seven scenarios, an allowed moisturizer candidate exists after hard filters.
This isolates the primary cause to the current routine builder, which only adds
moisturizer to the evening routine.

For the sensitive scenario, no moisturizer survives the hard filters. That is a
separate filtering/coverage problem and must not be hidden by simply forcing an
unsafe product into the routine.

## Finding 2: sensitive scenario has no moisturizer at all

Scenario:

```text
sensitive_reactivity_no_fragrance_alcohol
```

Result:

```text
morning: cleanser, SPF
evening: cleanser, serum
```

No moisturizer candidate survives the fragrance, alcohol, and sensitive-risk
filters. Step 4.10B must inspect the meaning of dataset `risk_flags` and avoid
interpreting every non-empty risk flag as an absolute sensitive-skin rejection.

## Finding 3: toner and mask are available but never selected

Dataset distribution:

```json
{
  "cleanser": 16,
  "toner": 18,
  "serum": 12,
  "moisturizer": 9,
  "spf": 9,
  "mask": 5
}
```

Selected schedule distribution across the eight scenarios:

```json
{
  "cleanser": 16,
  "serum": 8,
  "moisturizer": 7,
  "spf": 8
}
```

Ignored available steps:

```text
toner
mask
```

The current builder searches only for cleanser, serum, treatment, moisturizer,
and SPF. It has no selection branch for toner, mask, or exfoliation.

## Finding 4: two products dominate the scenario set

Products selected in six of eight scenarios:

```text
product_053 — andplus, 2% BHA Cream Cleanser 31.2
product_068 — POGONIA, Idebenone Mild SPF 50+
```

Each has a scenario selection ratio of `0.75`. Deterministic selection is
expected, but this level of reuse indicates that scoring/tie-breaking and
scenario diversity need review.

Step 4.10B should improve diversity without adding randomness and without
selecting lower-quality products merely to reduce frequency.

## Finding 5: enum and terminology drift

`RoutineStep` does not contain:

```text
toner
exfoliation
mask
```

The concern vocabulary uses canonical runtime values that are absent from the
current `Concern` enum:

```text
dehydration
dullness
pigmentation
pores
reactivity
redness
```

The enum still contains the legacy value:

```text
sensitivity
```

while request normalization maps sensitivity aliases to:

```text
reactivity
```

## Step 4.10B targets

Step 4.10B should make reviewed algorithm changes with these targets:

1. keep `contract_error_count` at zero;
2. add morning moisturizer whenever an allowed candidate exists;
3. resolve the sensitive no-moisturizer path through calibrated safety logic or
   an explicit safe fallback policy;
4. support toner as an optional step without overloading beginner routines;
5. schedule mask/exfoliation only in reviewed evening cases;
6. preserve SPF-only-in-morning behavior;
7. align enums with runtime/dataset terminology;
8. reduce unjustified product concentration without randomness;
9. update the tracked baseline only after reviewing the changed scenario output.

## Reproduction

Inside the backend container:

```bash
python scripts/audit_routine_quality.py \
  --dataset /data/products.xlsx \
  --output /tmp/routine-quality-report.json \
  --fail-on-contract-errors
```

Copy the generated report for review:

```powershell
docker cp `
  "koyash-backend:/tmp/routine-quality-report.json" `
  ".\routine-quality-report.json"
```

The command exits successfully when contract errors are zero. Known quality gaps
remain visible in the JSON report and are intentionally not converted into a
false green quality claim.
