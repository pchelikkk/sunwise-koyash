# ADR 0004 — Data seeding on application startup

- Status: Accepted
- Date: 2026-07-05
- Related quality requirements: QR-02 (main flow availability)

## Context

For the recommendation flow to work right after deployment, the product catalogue,
restrictions, and ingredient aliases must be present. Manual seeding steps make
deployments error-prone and can leave the deployed MVP in a non-working state during a
customer review.

## Decision

Run `seed_initial_data` inside the FastAPI `lifespan` startup, after the MongoDB
connection is established. Seeding is idempotent so repeated startups do not duplicate
data.

## Consequences

- Positive: `docker compose up -d --build` produces a fully working system with no
  manual data steps; the main flow is available immediately after deploy.
- Positive: reproducible environments across the VM and local machines.
- Negative: application startup performs writes; seed routines must remain idempotent
  and reasonably fast.