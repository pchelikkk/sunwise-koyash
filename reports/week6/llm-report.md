# LLM Usage Report

Project: KOYASH  
Team: Sunwise  
Assignment: 6  
Release: v0.4.0

## Purpose of LLM usage

The team used LLM assistance to support documentation, planning, and structuring of the
Week 6 artifacts. It was used for:

- organizing the Week 6 report structure;
- drafting the Sprint Review summary and notes from the recorded session;
- drafting the customer handover document and roadmap update;
- updating UAT scenarios and release notes;
- planning GitLab issues, branches, and merge request descriptions.

## Product LLM layer

KOYASH also contains an optional in-product LLM explanation layer, documented in
`AGENTS.md` and `docs/llm-integration-plan.md`. It is disabled by default
(`LLM_ENABLED=false`) and never changes hard exclusions or the recommendation score; it
only rephrases explanations. The prompt update and a joint evaluation with the customer
are planned for Week 7 (#63).

## Human responsibility

All final decisions, repository changes, customer communication, deployment, UAT, and
submission responsibility remain with the team. The team reviewed and adapted generated
text before including it in the repository, and every artifact was merged through a
merge request reviewed by a non-author.

## LLM-assisted artifacts

- `README.md`, `CONTRIBUTING.md`, `AGENTS.md`
- `docs/customer-handover.md`, `docs/roadmap.md`, `docs/user-acceptance-tests.md`
- `reports/week6/README.md`
- `reports/week6/sprint-review-summary.md`
- `reports/week6/sprint-review-notes.md`
- `reports/week6/customer-feedback-traceability.md`
- `reports/week6/reflection.md`
- `reports/week6/retrospective.md`
- `reports/week6/release-notes.md`
- `reports/week6/llm-report.md`

## Verification

The team checked generated content against Assignment 6 requirements, the recorded
customer session, actual project links, the repository structure, and the release scope.

## Limitations

LLM assistance did not replace customer validation, implementation, deployment, or final
responsibility. The team remained responsible for factual accuracy and for replacing
placeholder links with final links.
