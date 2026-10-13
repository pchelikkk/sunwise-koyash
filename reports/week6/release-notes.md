# Release Notes — v0.4.0

Project: KOYASH  
Team: Sunwise  
Assignment: 6  
Release: v0.4.0  
Date: 2026-07-12

## Release purpose

This release represents the Sprint 4 / Assignment 6 increment of KOYASH: an integrated
Week 6 trial (MVP v3 candidate) with a working backend, prepared for a facilitated
customer trial, UAT, and Sprint Review.

## Repository

`https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash`

## Trial deployment

- Week 6 trial deployment (university VM): http://10.93.26.208:8080/
- The same VM host previously served MVP v2 (v0.3.0).

## Included in this release

- backend covering the complete end-to-end flow (questionnaire → recommendation →
  account → history), demonstrated live to the customer;
- current frontend wired to the live API for a facilitated trial;
- per-product budget filtering across the recommendation set (pending customer
  validation, #61);
- questionnaire trimmed from 7 to 6 steps;
- approved design direction (with minor edits) for the final MVP v3;
- CONTRIBUTING.md and AGENTS.md entry points;
- customer handover documentation and an updated roadmap;
- UAT scenarios UAT-06 and UAT-07;
- the Week 6 report set.

## Testing and quality

- Testing: `docs/testing.md`
- Quality requirements: `docs/quality-requirements.md`
- Quality requirement tests: `docs/quality-requirement-tests.md`
- Definition of Done: `docs/definition-of-done.md`

## Customer trial, UAT, and Sprint Review

- Sprint Review / UAT recording: shared privately via Moodle
- Sprint Review summary: `reports/week6/sprint-review-summary.md`
- Sprint Review notes: `reports/week6/sprint-review-notes.md`
- Feedback traceability: `reports/week6/customer-feedback-traceability.md`

> During the Week 6 session the product was shown as a facilitated trial (working
> backend + current frontend). It is not yet ready for fully independent customer use;
> see `docs/customer-handover.md`.

## Public demo

Planned for Week 7 (MVP v3 final).

## GitLab release link

`https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v0.4.0`

## Follow-ups (Week 7 / Sprint 5)

- Validate and fix per-product budget filtering (#61);
- Fix replacement category matching (#62);
- Apply approved design 1:1 + morning/evening labeling (#50);
- LLM prompt update + joint evaluation (#63);
- Repository and secrets handover after the defense (#64).
