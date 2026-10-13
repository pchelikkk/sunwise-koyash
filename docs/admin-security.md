# KOYASH admin security boundary

The admin analytics API is intentionally not shown in OpenAPI/Swagger and is not linked from the normal user interface.

Access rules:

- no bearer token: `401`;
- active user with role `user`: `403`;
- active user with role `admin`: allowed;
- inactive users remain blocked;
- registration and profile update reject the `role` field;
- JWT stores only the user id, while the current role is loaded from MongoDB on every request, so demotion takes effect immediately.

The public analytics endpoint accepts only client-safe UI event types. Server-owned events such as feedback, registration and replacement selection must be written by backend services, not supplied by a browser. The browser cannot submit `user_id`; authenticated identity is derived from the bearer token.

## Promote an existing user

Dry run:

```bash
docker compose exec -T backend python scripts/set_user_role.py --email admin@example.com --role admin
```

Apply:

```bash
docker compose exec -T backend python scripts/set_user_role.py --email admin@example.com --role admin --apply
```

Demotion uses the same command with `--role user --apply`.

## Protected dashboard

`GET /api/v1/admin/analytics/dashboard`, `GET /api/v1/admin/catalog/quality`,
`GET /api/v1/admin/catalog/issues`,
`POST /api/v1/admin/catalog/import`, and
`PATCH /api/v1/admin/catalog/products/{external_id}` use the same `require_admin`
dependency. Analytics remains outside the public OpenAPI surface and returns aggregate
values only. User identifiers, anonymous identifiers, contact data, comments,
credentials, prompts, and raw event metadata are outside the dashboard contract.

The catalog editor exposes only presentation/operation fields: description, usage,
HTTP(S) image and product URLs, and activation. It cannot change source, ingredients,
price, scoring, or eligibility metadata. Each effective change stores before/after
values and the server-resolved administrator id in `admin_audit_events`.

The dataset import accepts only CSV/XLSX files up to 10 MB and 5,000 products.
Every row is parsed and validated before the first product write; duplicate
`external_id` values cancel the import. A successful import records the file hash,
row counts, administrator id and synchronization mode in the audit log. Missing
products may be marked inactive, never deleted, and an administrator-uploaded
dataset remains the runtime source of truth after a service restart.
