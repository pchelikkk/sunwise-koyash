# Development Process

Project: KOYASH  
Team: Sunwise  
Increment: MVP v2 (Sprint 3)

This document describes how the Sunwise team actually works: the git workflow,
review rules, configuration management, and how work items move from backlog to done.

## Git workflow

The team uses a trunk-based workflow with a protected `main` branch. Each issue is
implemented on a short-lived branch named after the issue number and a short
description (for example `docs/45-46-process-and-qa`). Work reaches `main` only through
an issue-linked, reviewed merge request.

gitGraph
commit id: "MVP v0 foundation"
branch feature/mvp1
commit id: "questionnaire + recommendations"
checkout main
merge feature/mvp1 tag: "v0.1.0"
branch feature/mvp1-polish
commit id: "design + QA + deploy"
checkout main
merge feature/mvp1-polish tag: "v0.2.0"
branch feature/mvp2-frontend
commit id: "frontend-backend integration"
checkout main
merge feature/mvp2-frontend
branch docs/architecture
commit id: "architecture + ADRs"
checkout main
merge docs/architecture tag: "v0.3.0"

## Roles per work item

- **Implementer** — writes the code or documentation and opens the merge request.
- **Reviewer** — a different team member who reviews and approves the merge request.

The implementer and the reviewer are never the same person.

## Work item lifecycle

1. A Product Backlog Item is created as a GitLab issue from a template
   (User Story / Course Task / Other PBI / Bug Report) and estimated in story points.
2. The issue is assigned to the current sprint milestone and moved on the board:
   `status::todo → status::in-progress → status::review → status::done`.
3. The implementer creates a branch, commits the change, and opens a merge request
   that links the issue with `Closes #<id>`.
4. CI runs the backend test suite on the merge request.
5. A second team member reviews against the acceptance criteria and the Definition of
   Done, then approves.
6. The merge request is merged into `main`; the issue Work Status is set to **Done**.

## Merge request rules

- Every merge request is linked to at least one issue.
- Every merge request is approved by a reviewer who is not the author.
- CI must pass before merge.
- `CHANGELOG.md` is updated for user-visible changes.
- The merge request follows the Definition of Done (`docs/definition-of-done.md`).

## Configuration management

- **Versioning:** the project follows Semantic Versioning. Releases are tagged on
  `main` (`v0.1.0`, `v0.2.0`, `v0.3.0`) and mapped to the corresponding sprint
  milestone and MVP version.
- **Secrets:** runtime configuration is provided through environment variables and
  `.env` files that are not committed. `.env.example` documents the required keys.
- **Reproducible environments:** the whole system runs with Docker Compose
  (`docker compose up -d --build`), so local, CI, and VM environments stay consistent.
- **Data:** the backend seeds its initial catalogue on startup, so a fresh deployment
  is immediately usable.
- **Traceability:** issues, merge requests, milestones, and releases are cross-linked
  so every change can be traced from backlog to production.

## Related documentation

- Architecture: `docs/architecture/README.md`
- Quality requirements: `docs/quality-requirements.md`
- Testing: `docs/testing.md`
- Definition of Done: `docs/definition-of-done.md`