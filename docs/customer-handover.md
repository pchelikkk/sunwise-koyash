# Customer Handover — KOYASH

Project: **KOYASH** · Team: **Sunwise (12)** · Customer: **Diana**

This document describes how to run, operate, and take ownership of KOYASH, and records
the transition status agreed with the customer.

## Status after Week 7 (final MVP v3)

- **Handover level:** `Ready for independent use`. The final MVP v3 is deployed on the
  university VM and can be used by the customer without team facilitation.
- **Customer confirmation status:** `Accepted with follow-up items`. The customer
  accepted the product as final and confirmed the team is ready for the defense.
- **Design:** the redesigned, more functional frontend was shipped as the final MVP v3
  and accepted by the customer.

## What is delivered

- Integrated stack: React SPA + FastAPI backend + MongoDB.
- End-to-end flow: questionnaire -> explainable recommendation -> account/profile ->
  history, with per-product feedback and in-category replacement.
- Detected skin type shown on the result; guests can save their bag by signing in.
- Admin analytics panel (completed selections, unique visitors, feedback reasons,
  product management).
- Deployment on the university VM, the final `v1.0.1` MVP v3 patch release, and the full documentation set.

## Deployment

- Final product access (university VM): http://10.93.26.208:8080/
- Recommended target for a customer-owned deployment: the university VM or an
  equivalent Docker host.

## How to run (self-hosting)

Full stack via Docker Compose: `docker compose up -d --build` (app on `:8080`).
See `README.md` and `docs/development-process.md` for details.

## Configuration and secrets

- Runtime configuration is provided through environment variables; templates are in
  `.env.example`, `backend/.env.example`, and `frontend/.env.example`.
- Required keys: MongoDB (`MONGO_URI`, `MONGO_DB_NAME`), `JWT_SECRET_KEY`, optional LLM
  layer (`LLM_ENABLED` plus `OPENAI_*` or `VSELLM_*`), optional SMTP for password reset
  (`SMTP_*`).
- Secrets are **not** stored in the repository. Production secrets and database access
  are transferred to the customer separately over a secure channel after the course
  defense (see Transfer plan).

## Transfer plan

1. The team defends the project; the customer attends the defense.
2. After the defense, a handover meeting is organized with the customer.
3. Repository ownership/access is transferred; production secrets and MongoDB access are
   shared over a secure channel (never committed to the repository).
4. This document is updated to `Independently used by customer` or `Deployed or operated
   on customer side` once completed. Tracked in issue #64.

## Follow-up items after acceptance

- Repository and secrets handover after the defense (#64).
- The customer-authored LLM prompt and the reviewed filtration sample are integrated.
  The layer remains optional and the deterministic fallback stays available (#63).

## Repository and contacts

- Repository: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash
- Team: Sunwise. Backend and deployment owner: Sergei.
