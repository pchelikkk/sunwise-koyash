# KOYASH deterministic recommendation algorithm

Current version: `rule-based-v2`.

## Non-negotiable boundary

Product filtering, scoring, ordering, and routine construction are fully
deterministic. The optional LLM layer may rewrite an explanation after the
result is fixed; it must not add, remove, rank, or replace products.

## Pipeline

1. Validate `RecommendationRequest` limits and supported v2 fields.
2. If `skin_type=unknown`, require and deterministically evaluate the four guided
   diagnostic answers.
3. Normalize aliases, case, concerns, values, and restrictions.
4. Load active products from the repository.
5. Apply hard filters.
6. Calculate a transparent score for every allowed product.
7. Sort by score and deterministic tie-break fields.
8. Build morning and evening schedules from the requested routine preference.
9. Generate deterministic explanations and persist the versioned result.

## Guided skin-type resolution

Users who cannot self-report a skin type answer four observable-behavior questions.
Each answer adds fixed evidence weights to normal, oily, dry, and combination profiles.
The highest score wins with a stable tie-break order. The response exposes all scores,
the supporting signals, and a bounded confidence percentage so the decision is
inspectable.

The resolved type is applied before filtering and scoring and is persisted in
`skin_profile`. A self-reported type produces the same response shape with method
`self_reported`. The helper is cosmetic guidance only; it does not perform image
analysis, infer disease, or replace a dermatologist.

## Hard filters

A product is removed before scoring when:

- it is inactive;
- it matches a supported predefined or custom restriction;
- a high-sensitivity profile matches an explicit fragrance, alcohol, or
  essential-oil risk flag;
- a beginner product carries an explicit `active_formula` flag;
- the `minimum` budget hard cap of 1,200 RUB is exceeded.

`sensitive_attention` is contextual source metadata and is not an irritant by
itself. It cannot be used as the sole reason to remove a product.

### Restriction coverage

`filter_summary.restriction_coverage` makes restriction handling observable.
For every normalized predefined or custom restriction it returns the number of
active catalog products matched before scoring. A zero-match value is listed in
`unmatched_restrictions`; this means the current catalog data did not contain an
exact value or supported alias, not that the ingredient was proven safe.

The API intentionally avoids substring matching. For example, a broad search
for `alcohol` could incorrectly remove fatty alcohols when the user meant
ethanol or denatured alcohol. Raw custom values therefore require an exact
normalized ingredient/flag match unless a reviewed alias exists.

## Score components

- base routine-step availability;
- overlap with selected concerns;
- additional primary-concern match;
- exact skin-type match or a smaller `all` match;
- budget match;
- experience and formula-risk compatibility;
- sensitivity compatibility;
- normalized texture preference;
- requested catalog-backed values;
- desired routine complexity;
- explicit penalties for incompatible risk and budget combinations.

Every component is returned in `ScoreBreakdown`. No random value is used.

## Routine construction

Base order:

```text
morning: cleanser -> toner -> moisturizer -> SPF
evening: cleanser -> toner -> serum -> treatment -> moisturizer
```

The actual steps depend on `routine_preference`:

- `minimal`: cleanser, moisturizer, and morning SPF;
- `balanced`: base steps plus evening toner and one targeted step;
- `complete`: toner in both dayparts plus available serum/treatment steps.

A missing candidate produces a shorter routine; the builder never pads output
with a product from another step. Masks and exfoliation are not added until the
API has reviewed frequency and application metadata.

## Replacement contract

Replacement candidates reuse the normalized request and the same hard-filter
function. They must match the original `routine_step`, exclude products already
present in the routine, use deterministic ordering, and return zero to three
real candidates without filler.

## Versioning

Selection changes require a new `algorithm_version`. Stored sessions retain
their version so analytics, history, tests, and customer review can distinguish
old and new results.
