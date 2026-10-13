# KOYASH Feedback and Replacement Flow

## Purpose

The feedback flow is not just a form. It is a product loop:

1. The user marks a recommended product as unsuitable.
2. The backend stores feedback.
3. The backend interprets the reason.
4. The backend generates replacement candidates.
5. The user can select a replacement.
6. The data can later be used for analytics and dashboard charts.

## Feedback reasons

- `too_expensive`
- `dislikes_brand`
- `composition_concern`
- `texture_not_suitable`
- `too_many_steps`
- `other`

## Replacement strategies

| Reason | Strategy |
|---|---|
| `too_expensive` | cheaper same-step product |
| `dislikes_brand` | same-step product from another brand |
| `composition_concern` | safer or softer formula |
| `texture_not_suitable` | same-step product with another texture |
| `too_many_steps` | future routine simplification |
| `other` | best alternative for the same routine step |

## API

```text
POST /api/v1/recommendations/{recommendation_id}/feedback
GET  /api/v1/recommendations/{recommendation_id}/replacements
POST /api/v1/recommendations/{recommendation_id}/replacements/{replacement_session_id}/select
