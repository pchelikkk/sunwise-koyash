# LLM Usage Report — Week 7

Project: KOYASH
Team: Sunwise
Assignment: 6
Sprint: 5
Release: v1.0.0

## Purpose of LLM usage

The team used LLM assistance to support documentation, planning, and structuring of the
Week 7 artifacts. It was used for:

- organizing the Week 7 report set;
- drafting the Sprint Review summary and notes from the recorded session;
- updating the customer handover, roadmap, UAT, changelog, and release notes;
- planning the Sprint 5 issues, branches, and merge request descriptions.

## Product LLM layer

KOYASH contains an optional in-product LLM explanation layer, documented in `AGENTS.md`
and `docs/llm-integration-plan.md`. This sprint the customer-authored system and user
prompts were integrated (#63). The model receives the full concern list and the exact
product-level `matched_concerns` separately, and only the latter may ground a
concern-specific phrase. Runtime policy validation rejects unsupported personalization,
medical or guarantee-like claims, invalid punctuation, omitted ingredients/concerns,
and output over 200 characters. The layer stays disabled by default
(`LLM_ENABLED=false`), never changes hard exclusions or recommendation scores, and only
rewords explanations. The configured model is `gpt-4o-mini`; deterministic fallback
remains available for every provider failure or policy rejection.

## Human responsibility

All final decisions, repository changes, customer communication, deployment, UAT, and
submission responsibility remain with the team. The team reviewed and adapted generated
text before including it in the repository, and every artifact was merged through a
merge request reviewed by a non-author.

## LLM-assisted artifacts

- `README.md`, `CONTRIBUTING.md`, `AGENTS.md`
- `docs/customer-handover.md`, `docs/roadmap.md`, `docs/user-acceptance-tests.md`
- `CHANGELOG.md`
- `reports/week7/README.md`
- `reports/week7/sprint-review-summary.md`
- `reports/week7/sprint-review-notes.md`
- `reports/week7/customer-feedback-traceability.md`
- `reports/week7/reflection.md`
- `reports/week7/retrospective.md`
- `reports/week7/release-notes.md`
- `reports/week7/llm-report.md`

## Verification

The team checked generated content against the Assignment 6 requirements, the recorded
customer session, the customer-provided prompt, the eight-scenario filtration JSON,
the actual project links, the repository structure, and the release scope. Prompt,
schema, provider, fallback, and recommendation-flow tests are automated.

## Limitations

LLM assistance did not replace customer validation, implementation, deployment, or final
responsibility. The team remained responsible for factual accuracy and for using final
links.
