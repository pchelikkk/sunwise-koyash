# KOYASH professional product experience

This document describes the production-facing experience delivered on top of the
deterministic `rule-based-v2` recommendation core.

## User journeys

The React SPA exposes the following same-origin routes:

- `/#home` — product promise, benefits, and entry points;
- `/#quiz` — adaptive professional questionnaire;
- `/#review`, `/#loading`, and `/#results` — answer review and explainable morning
  and evening routines;
- `/#catalog` — searchable, filterable product catalog;
- `/#account` and `/#history` — profile, favorites, and owned recommendation history;
- `/#login`, `/#register`, `/#forgot-password`, and `/#reset?token=...` — account lifecycle;
- `/#admin` — aggregate analytics and catalog-quality dashboard for administrators.

All API traffic is routed through `/api/v1` by nginx; Vite uses the same proxy contract
in local development. Authenticated requests use the current access token.
Recommendation, feedback, and replacement reads are owner-checked: an authenticated
session must match the saved user, and an anonymous session must present the same
anonymous identifier that created the recommendation.

## Adaptive skin-type guidance

The complete question and branching contract is documented in
`docs/professional-questionnaire-v3.md`.

The questionnaire contains ten or eleven questions for a user who knows their skin
type: a single concern becomes the priority automatically, while multiple concerns add
one priority question. If the user selects `unknown`, four conditional questions become
visible, for a maximum total of fifteen:

1. comfort immediately after cleansing;
2. midday shine distribution;
3. pore visibility;
4. flaking frequency.

`POST /api/v1/skin-diagnosis` resolves these answers deterministically to `normal`,
`oily`, `dry`, or `combination`. It returns transparent per-type scores, the decisive
signals, and a bounded confidence level. The same answer object can be sent as
`skin_diagnostic_answers` in `POST /api/v1/recommendations`; the recommendation service
then resolves the type before hard filtering and scoring.

This is cosmetic guidance, not a medical diagnosis. The response always includes a
disclaimer and does not infer disease or prescribe treatment.

## Product discovery and library

`GET /api/v1/products/catalog` supports:

- full-text search over product name, brand, category, description, and ingredients;
- multi-select filters for routine step, budget, skin type, concern, and product values;
- an optional known-irritant filter and an inclusive price range;
- deterministic relevance, price, and name sorting;
- pagination up to 48 products per page;
- dynamic facet counts and catalog price bounds.

Product cards and details expose only catalog-backed attributes, including key
ingredients, usage, texture, values, risk flags, volume, price per milliliter, and
verified external links when available. Authenticated users can save or remove a
product through `/api/v1/users/me/favorites/{product_external_id}`.

`GET /api/v1/users/me/recommendations` returns only recommendation sessions owned by
the authenticated user. Pagination is bounded to 50 records per request.

## Recommendation result

The result UI shows:

- the resolved skin profile and confidence when guidance was used;
- morning and evening order, scores, and deterministic explanations;
- hard-filter totals and coverage of requested restrictions;
- an explicit warning when a restriction has no exact catalog match;
- the algorithm version for auditability;
- product detail, favorite, feedback, and replacement actions backed by live APIs;
- a source marker for explanations (`deterministic` or `llm`) in the API contract.

Submitting negative product feedback creates a replacement session. When compatible
alternatives exist, selecting one replaces the original product in every matching
morning/evening occurrence of the stored recommendation and recalculates the unique
routine total. It does not add the alternative to the cosmetic bag. When no candidate
passes the same hard restrictions, the interface states that no safe replacement was
found and keeps the original routine unchanged.

The browser never changes product eligibility or order. All selection decisions remain
inside the deterministic backend boundary documented in
`docs/recommendation-algorithm.md`.

When `LLM_ENABLED=true` and VseLLM credentials are configured, the backend asks the
model to rewrite only `why_here` after the deterministic routine has been selected.
Product IDs, ordering, hard filters, score totals, safety notes, and usage instructions
remain unchanged. Provider errors, empty responses, and unsafe claims fall back to the
deterministic explanation without failing the recommendation request.

## Administrator experience

`/#admin` is visible only to a signed-in administrator. It combines the protected
aggregate analytics endpoint with `GET /api/v1/admin/catalog/quality` and displays:

- period totals and funnel coverage;
- product-selection and audience distributions without direct identifiers;
- catalog dataset status, active/inactive totals, completeness, routine-step coverage,
  risk-flag counts, and missing-field counts;
- completeness bars for usage instructions, product links, and images;
- a filterable catalog issue queue;
- a constrained editor for media URLs, product URLs, usage instructions, and product
  activation. Scoring and source fields are intentionally not editable, and every
  update is written to `admin_audit_events`.

Historic analytics can contain incomplete legacy funnel events. The UI marks a
conversion as unavailable when its denominator is missing or produces an impossible
rate instead of presenting a misleading percentage.

## UX and accessibility baseline

The interface follows the warm pink, blush, white, sun, and cottage direction from the
approved Figma file while increasing text contrast and information density where the
prototype was only illustrative. It supports desktop and narrow mobile layouts, visible
focus states, semantic controls, keyboard-operated dialogs, reduced-motion preference,
loading and empty states, and recoverable API errors.

The landing page keeps all explanatory content visible without hover-only or decorative
reveal interactions. Its editorial sections reuse the prototype's open spacing,
handwritten accents, soft organic surfaces, and pink line-art language while giving the
product promise, benefits, process, safety model, and brand origin a clear reading order.
Catalog and recommendation fallbacks use a consistent inline SVG illustration family for
cleanser, toner, serum, cream, mask, and SPF packaging. Real catalog imagery still takes
priority when a valid image URL is present.

## Verification

The delivery gate includes:

- the complete backend test suite;
- strict runtime catalog validation against `data/products.xlsx`;
- Ruff and Python byte-compilation checks for changed backend modules;
- a production Vite build;
- browser smoke checks for landing, questionnaire branching, catalog filters, product
  details, authentication, admin analytics, and mobile overflow.

The current evidence and exact command results are recorded in
`docs/release-readiness-v1.md`.
