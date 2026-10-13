# KOYASH analytics event contract

## Trust boundary

Analytics events have an explicit `event_source`:

- `public` — UI interaction events accepted from the browser through `/api/v1/analytics/events`;
- `server` — domain events emitted only by backend services after the operation succeeds.

Dashboard conversion and business metrics must use server-owned events or source domain collections. A browser event must never be treated as proof that registration, recommendation, feedback, replacement selection, or an LLM request succeeded.

## Server-owned events

- `registration_completed`
- `questionnaire_completed`
- `recommendation_generated`
- `feedback_submitted`
- `replacement_generated`
- `replacement_selected`
- `profile_saved`
- `llm_explanation_success`
- `llm_explanation_fallback`

## Public UI events

- `questionnaire_opened`
- `questionnaire_started`
- `question_answered`
- `result_viewed`
- `product_viewed`
- `product_details_opened`

## Data minimization

Server analytics metadata must not contain:

- email;
- full name;
- phone;
- password;
- access/reset tokens;
- authorization headers;
- feedback comment text;
- prompts or LLM API credentials.

Exact user and anonymous identifiers may remain in raw MongoDB event documents for attribution, but admin responses must not expose those identifiers directly.

## Reliability

Analytics writes are best-effort. A temporary analytics failure must not break registration, recommendation generation, feedback submission, replacement selection, profile saving, or deterministic LLM fallback.

## Identity integrity

For authenticated recommendation requests, identity is taken from the authenticated
user record. A client-provided `anonymous_id` cannot replace that identity.
Feedback and replacement events inherit identity from the saved recommendation,
not from feedback request fields.

Sensitive metadata detection covers nested and compound key variants such as
`access_token`, `password_hash`, `user_email`, API keys, cookies, credentials,
and prompt fields.


## Protected aggregate dashboard

`GET /api/v1/admin/analytics/dashboard` combines trusted server events with source domain
collections. Public UI events are counted separately and are never accepted as proof of a
successful registration, recommendation, feedback, replacement, profile, or LLM operation.

The dashboard uses UTC half-open periods and refuses intervals longer than the raw analytics event
retention window. Responses contain aggregate counts and catalog labels only. Raw identifiers,
comments, prompts, credentials, and metadata are not returned. Free-text custom restrictions are
reduced to the aggregate bucket `custom`.
