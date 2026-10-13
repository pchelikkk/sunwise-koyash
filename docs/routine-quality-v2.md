# KOYASH rule-based-v2 routine quality result

## Result

`rule-based-v2` was measured with the same 69-product dataset and the same
eight deterministic scenarios introduced by Step 4.10A.

| Metric | rule-based-v1 | rule-based-v2 |
|---|---:|---:|
| contract errors | 0 | 0 |
| total quality gaps | 23 | 1 |
| scenario quality gaps | 9 | 0 |
| warnings | 1 | 0 |
| ignored available steps | 2 | 1 |
| overused products | 2 | 0 |
| terminology gaps | 10 | 0 |

The tracked `docs/routine-quality-baseline.json` contains the complete v2
scenario output and is compared byte-for-meaning through a JSON regression
test.

## Improvements

- morning moisturizer is present whenever a candidate survives hard filters;
- the sensitive scenario now keeps contextual `sensitive_attention` products
  while still excluding explicit fragrance, alcohol, and essential-oil risks;
- the sensitive scenario receives moisturizer in both dayparts;
- balanced routines use an evening toner;
- minimal legacy requests no longer receive an overloaded routine;
- enum values match the runtime concern and routine-step vocabulary;
- no product appears in 60% or more of the fixed scenarios;
- hard restrictions, deterministic sorting, and SPF daypart behavior remain
  unchanged.

## Intentional remaining gap

`mask` remains available in the dataset but is not scheduled. A mask is not a
safe daily routine step by default, and the current product/API contract does
not expose reviewed frequency or application duration. Adding it merely to
reach zero gaps would make the recommendation less trustworthy.

The remaining quality-gap count of one therefore records an explicit product
decision rather than a hidden builder defect.

## Reproduction

```bash
python scripts/audit_routine_quality.py \
  --dataset /data/products.xlsx \
  --output /tmp/routine-quality-report.json \
  --fail-on-contract-errors
```

Expected summary:

```text
scenarios=8, contract_errors=0, quality_gaps=1
```
