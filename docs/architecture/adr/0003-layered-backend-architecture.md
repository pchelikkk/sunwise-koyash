# ADR 0003 — Layered backend architecture

- Status: Accepted
- Date: 2026-07-05
- Related quality requirements: QR-01 (functional correctness), maintainability

## Context

Recommendation logic must be correct, testable, and easy to change. Mixing HTTP
handling, business logic, and database access in one place would make the system hard
to test and maintain.

## Decision

Structure the backend in explicit layers:

- **API layer** (`api/v1/endpoints`): thin FastAPI handlers, request/response only.
- **Service layer** (`services`): business orchestration.
- **Algorithms** (`algorithms`): pure functions for filtering, scoring, sorting, and
  routine building.
- **Repository layer** (`repositories`): all MongoDB access.
- **Schemas** (`schemas`) and **Core** (`core`) for validation and cross-cutting
  concerns.

Dependencies point inward and are wired with FastAPI dependency injection.

## Consequences

- Positive: high cohesion and low coupling; storage details are isolated behind
  repositories; pure algorithms are easy to unit test.
- Positive: recommendation logic can change without touching HTTP or persistence code.
- Negative: more boilerplate and dependency wiring than a single-module approach.