# KOYASH professional questionnaire v2

## Goal

The v2 questionnaire replaces the seven-question design prototype with an
eleven-step contract. New questions are not decorative: each selection maps to
a deterministic filter, score component, or routine-building rule. Age is the
only optional profile field and is explicitly excluded from product filtering.

The recommendation algorithm remains rule based. An LLM must not interpret
questionnaire answers or choose products.

## Question contract

| Step | ID | Required | Deterministic effect |
|---:|---|:---:|---|
| 1 | `skin_type` | yes | exact or `all` skin-type score |
| 2 | `concerns` | yes | concern overlap score, maximum five values |
| 3 | `primary_concern` | yes | explicit bonus for the highest-priority concern |
| 4 | `sensitivity_level` | yes | irritant filtering or risk penalty |
| 5 | `budget` | yes | price hard cap and budget score |
| 6 | `restrictions` | no selections required | hard ingredient exclusion |
| 7 | `experience` | yes | complexity and risk penalties |
| 8 | `routine_preference` | yes | minimal, balanced, or complete schedule |
| 9 | `texture_preference` | yes | small normalized texture bonus |
| 10 | `values` | yes | product-value overlap, maximum three values |
| 11 | `age` | no | aggregate profile analytics only |

## Supported values

### Skin type

`normal`, `oily`, `dry`, `combination`, `sensitive`, `unknown`.

Sensitivity is asked separately because any skin type can be reactive. The
legacy `sensitive` skin type remains supported for compatibility.

### Concerns

The UI offers concern values that currently have meaningful coverage in the
normalized dataset: acne, sebum, dryness, dehydration, reactivity,
pigmentation, and age changes. `unknown` is removed during normalization.

`primary_concern` must come from the selected concern set. The frontend limits
its options to the prior answer, while the backend also includes it in the
normalized concern list if an older client omits it there.

### Sensitivity

- `high`: products with explicit fragrance, alcohol, or essential-oil risk
  flags are excluded;
- `medium`: matching irritant flags receive a deterministic score penalty;
- `low` and `unknown`: no extra sensitivity restriction is added.

The contextual `sensitive_attention` label is not itself an irritant. Treating
every non-empty risk flag as a hard failure previously removed all moisturizer
candidates from the sensitive scenario.

### Routine preference

- `minimal`: cleanser, moisturizer, and morning SPF where candidates exist;
- `balanced`: the base routine plus an evening toner and one targeted step;
- `complete`: toner in both dayparts and available serum/treatment steps.

The builder does not schedule masks as a daily step because the current API has
no frequency contract. Mask/exfoliation support requires reviewed frequency and
usage metadata rather than a cosmetic extra card.

### Texture and values

Imported Russian and English formats are grouped into `lightweight`, `cream`,
or `rich`. A match adds a small score bonus and never overrides hard filters.

The UI offers only values represented by catalog data: `soft_formula`, `vegan`,
`cruelty_free`, and `price_quality`. Vague legacy choices such as `quality` and
`fast_result` are not presented. Legacy API payloads remain accepted and are
normalized where a safe mapping already exists.

## Validation and compatibility

- concerns: maximum five;
- values: the v2 UI allows three; the API accepts up to eight for legacy clients;
- predefined plus custom restrictions: maximum ten values per list;
- every list item: trimmed, unique, maximum 100 characters;
- anonymous ID: maximum 120 characters;
- age: 12–100 when supplied;
- old payloads work through defaults for all new fields.

The questionnaire response exposes `required`, selection limits, dependency
metadata, and custom-input length so the frontend and API share one contract.

## Versioning

- questionnaire: `professional-v2`;
- recommendation algorithm: `rule-based-v2`.

Stored recommendation sessions retain their algorithm version. This makes v1
and v2 output distinguishable in history and analytics.

The fixed routine audit improves from `8 / 0 / 23` to `8 / 0 / 1`; see
`docs/routine-quality-v2.md` for the reviewed remaining mask-frequency gap.
