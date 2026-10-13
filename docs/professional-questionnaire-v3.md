# KOYASH professional questionnaire v3

## Product goal

The questionnaire asks only questions that either affect deterministic recommendation
behavior or are explicitly optional. Copy is written in plain Russian, describes
observable skin experiences, avoids medical diagnosis, and explains why every answer
is requested. An LLM never interprets answers or chooses products.

Users who know their skin type see ten or eleven effective questions: when only one
concern is selected, it becomes the priority automatically. Selecting “Помогите
определить” reveals four clarification questions, for a maximum of fifteen. The UI
recalculates progress from currently relevant questions, so hidden branches do not
create empty steps.

## Question contract

| Order | ID | Visibility | Deterministic effect |
|---:|---|---|---|
| 1 | `skin_type` | always | skin profile or diagnostic branch |
| 2 | `diagnostic_after_cleansing` | unknown type | diagnostic evidence |
| 3 | `diagnostic_midday_shine` | unknown type | diagnostic evidence |
| 4 | `diagnostic_pore_visibility` | unknown type | diagnostic evidence |
| 5 | `diagnostic_flaking` | unknown type | diagnostic evidence |
| 6 | `concerns` | always | concern score, maximum five |
| 7 | `primary_concern` | two or more actionable concerns | priority score bonus |
| 8 | `sensitivity_level` | always | irritant exclusion/penalty |
| 9 | `budget` | always | hard per-product price cap and score |
| 10 | `restrictions` | always, selections optional | hard ingredient exclusion |
| 11 | `experience` | always | complexity and safety weighting |
| 12 | `routine_preference` | always | minimal, balanced, or complete routine |
| 13 | `texture_preference` | always | tie-break preference only |
| 14 | `values` | always | verified catalog-value overlap, maximum three |
| 15 | `age` | always, answer optional | aggregate statistics only |

## User-friendly behavior

- Neutral answers such as `unknown`, `none`, and `no_preference` are exclusive and are
  removed before recommendation scoring where appropriate.
- “Пока не знаю” never forces an irrelevant primary-concern step.
- A single concern becomes the priority automatically, avoiding a redundant question.
- Sensitivity asks about lived reactions and explicitly states that it is not a medical
  diagnosis.
- Restrictions explain the difference between exact catalog matching and free text.
- Age can be skipped and does not change product eligibility.
- Each budget label states the actual per-product cap: 1,200 RUB for `minimum`, 2,200
  RUB for `balanced`, and no hard cap for `premium`.

## Skin-type clarification

`POST /api/v1/skin-diagnosis` resolves the four clarification answers to `normal`,
`oily`, `dry`, or `combination`. The response contains transparent scores, decisive
signals, bounded confidence, and a non-medical disclaimer. The same evidence is
resolved server-side when sent with a recommendation request.

## Version and compatibility

- questionnaire: `professional-v3`;
- recommendation algorithm: `rule-based-v2`;
- existing request values remain accepted through backend normalization;
- stored recommendations retain their algorithm version and resolved skin profile.

Contract tests verify question ids, limits, conditional visibility, human-readable
copy, diagnostic behavior, neutral-answer normalization, and the hard budget boundary.
