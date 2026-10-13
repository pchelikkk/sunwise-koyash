# ADR 0002 — MongoDB as the primary data store

- Status: Accepted
- Date: 2026-07-05
- Related quality requirements: QR-01 (recommendation data correctness)

## Context

The product catalogue, recommendations, feedback, and user data evolve quickly during
MVP iterations. We need a store that supports flexible, document-shaped data and an
async driver compatible with FastAPI.

## Decision

Use MongoDB 7 as the primary data store, accessed through the async `pymongo` client.
The database name is `koyash`, indexes are created on startup, and data is persisted in
the `koyash_mongo_data` Docker volume.

## Consequences

- Positive: flexible document schema allows fast iteration on product and
  recommendation structures.
- Positive: async driver fits the FastAPI/uvicorn stack.
- Negative: no relational constraints; data integrity must be enforced at the
  application layer with Pydantic schemas and repository logic.
- Negative: cross-collection consistency is the application's responsibility.