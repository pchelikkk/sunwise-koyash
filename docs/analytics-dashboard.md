# KOYASH protected analytics dashboard API

## Scope

Step 4.9C adds one protected aggregate endpoint:

```text
GET /api/v1/admin/analytics/dashboard
```

The endpoint is intentionally hidden from OpenAPI/Swagger and is available only to an
active user whose current MongoDB role is `admin`.

Access behavior:

```text
without bearer token -> 401
role=user            -> 403
role=admin           -> 200
```

The backend authorization boundary remains authoritative. A hidden frontend route is not
a security control by itself.

## Period filters

The default request returns the last 30 UTC calendar days, including the current day:

```text
GET /api/v1/admin/analytics/dashboard
GET /api/v1/admin/analytics/dashboard?days=7
GET /api/v1/admin/analytics/dashboard?days=30
GET /api/v1/admin/analytics/dashboard?days=90
```

An explicit half-open UTC range is also supported:

```text
GET /api/v1/admin/analytics/dashboard?date_from=2026-07-01T00:00:00Z&date_to=2026-08-01T00:00:00Z
```

Rules:

- `date_from` and `date_to` must be supplied together;
- `date_from` must be earlier than `date_to`;
- `days` must be between 1 and 365;
- the requested interval cannot exceed `ANALYTICS_RAW_EVENT_TTL_DAYS`;
- explicit ranges use `[date_from, date_to)` semantics;
- naive timestamps are interpreted as UTC;
- invalid filters return `422`.

The retention bound prevents a dashboard response from silently combining long-lived domain
records with raw server-event data that has already expired from MongoDB.

## Source-of-truth rules

Business metrics do not trust browser claims.

| Metric | Source |
|---|---|
| registrations | `users.created_at` |
| questionnaires completed | server-owned `questionnaire_completed` events |
| recommendations generated | `recommendation_sessions.created_at` |
| feedback submitted | `feedback_events.created_at` |
| replacement sessions | `replacement_sessions.created_at` |
| replacement selections | non-empty `replacement_sessions.selected_product_external_id` |
| LLM success/fallback | server-owned analytics events |
| public/server event totals | `analytics_events.event_source` |

This mixed strategy uses domain collections for persisted business actions and trusted server
events where no separate source collection exists.

## Dashboard sections

### `overview`

Returns aggregate counts for:

- registrations;
- completed questionnaires;
- generated recommendations;
- submitted feedback;
- replacement sessions and selections;
- LLM success and fallback;
- public and server events.

### `conversion`

Each rate includes its numerator, denominator, and percentage:

- questionnaire -> recommendation;
- feedback -> replacement session;
- replacement session -> selected replacement;
- LLM fallback / all LLM outcomes.

A zero denominator produces `0.0`, not a division error.

### `activity`

Returns one zero-filled UTC point per calendar day. Missing days are represented explicitly so
the frontend does not need to repair chart gaps.

### `products`

Returns at most ten items per list:

- top recommended products;
- products with the most negative feedback;
- products most frequently replaced;
- replacement products most frequently selected.

A product appearing in both morning and evening counts only once per recommendation session.
Product name and brand are enriched from the product catalog. Historical unknown product IDs
remain visible with `name=null` and `brand=null` instead of causing the endpoint to fail.

### `feedback`

Returns total feedback, reason counts, and reason breakdowns by product. Feedback comment text is
never returned.

### `replacements`

Returns generated/selected totals, selection conversion, and replacement reason counts.

### `audience`

Returns aggregate distributions for:

- skin types;
- concerns;
- restrictions;
- budgets;
- experience.

Raw free-text custom restrictions are never exposed. Sessions that contain one or more custom
restrictions contribute only to the aggregate bucket `custom`.

## Privacy boundary

The dashboard response must not contain:

- `user_id`;
- `anonymous_id`;
- email or full name;
- password hashes;
- access/reset tokens;
- authorization headers;
- feedback comments;
- LLM prompts;
- API credentials;
- raw event metadata.

The legacy `/admin/analytics/summary` endpoint remains available for compatibility, but its recent
event feed is reduced to an anonymized allowlist: event type, source, product external ID, and
timestamp.

## Empty state

A valid interval with no data returns:

- zero overview counts;
- zero conversion rates;
- zero-filled daily activity;
- empty product and feedback lists;
- empty audience dictionaries.

It must not return `404`, `500`, or omit dashboard sections.

Unexpected aggregation failures are logged server-side and return a generic `503` response.
Internal exception text and stack traces are not exposed to the client.

## Verification

Focused tests:

```powershell
docker compose exec -T backend pytest `
  tests/test_analytics_dashboard.py `
  tests/test_analytics.py `
  tests/test_server_event_tracking.py `
  tests/test_server_event_tracking_hardening.py `
  -q
```

Full backend and runtime-catalog isolation:

```powershell
docker compose exec -T backend pytest -q

docker compose exec -T backend python scripts/check_product_catalog_state.py --strict-dataset
```

The catalog check must run after pytest without cleanup or reimport.
