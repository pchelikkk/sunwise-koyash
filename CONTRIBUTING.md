# Contributing to KOYASH

This guide is the entry point for contributing to KOYASH. It summarizes the workflow;
the full process lives in `docs/development-process.md` and the completion criteria in
`docs/definition-of-done.md`.

## Workflow in short

1. Every change starts from a GitLab issue created from a template
   (User Story / Course Task / Other PBI / Bug Report) and linked to the current
   sprint milestone.
2. Create a short-lived branch named after the issue number and a short description,
   for example `docs/51-readme-trial` or `backend/57-release-candidate`.
3. Commit focused changes and open a merge request using the default MR template.
   Link the issue with `Closes #<id>`.
4. CI must pass (the backend test suite runs on every merge request).
5. A reviewer who is not the author reviews against the acceptance criteria and the
   Definition of Done, then approves.
6. Merge into `main`; set the issue Work Status to Done.

## Golden rules

- The implementer and the reviewer are never the same person.
- Every merge request is linked to at least one issue.
- Update `CHANGELOG.md` for any user-visible change.
- Documentation is written in English and contains no secrets or private customer data.
- Runtime configuration goes through environment variables / `.env` files that are
  never committed; `.env.example` documents the required keys.
- Releases are tagged on `main` using Semantic Versioning and mapped to the sprint
  milestone and MVP version.

## Branch naming

`<type>/<issue-number(s)>-<short-slug>`, where `<type>` is one of
`feature`, `backend`, `frontend`, `docs`, `ci`, `fix`
(for example `docs/51-52-readme-contributing-agents`).

## Local development

See `README.md` for full-stack (`docker compose up -d --build`) and per-component
instructions (backend `uvicorn app.main:app --reload`, frontend `npm run dev`).

## Review checklist

Use the review checklist in `docs/definition-of-done.md` before approving a merge
request.