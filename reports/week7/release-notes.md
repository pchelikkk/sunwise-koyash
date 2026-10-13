# Release Notes — v1.0.0

Project: KOYASH
Team: Sunwise
Assignment: 6
Sprint: 5
Release: v1.0.0 (MVP v3)
Date: 2026-07-19

## Release purpose

This is the final MVP v3 release of KOYASH. It applies the redesigned frontend and the
customer-trial follow-ups, fixes and validates the recommendation backend, finalizes
the explanation prompt, and completes the customer transition.

## Repository

https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash

## Deployment

- Final product access (university VM): http://10.93.26.208:8080/
- The SPA and the API share the same origin through nginx, so no CORS configuration is
  required.

## Included in this release

- redesigned, more functional frontend as the final MVP v3 direction (#50);
- product catalog and favorites removed as out of concept (#65);
- detected skin type shown on the questionnaire result (#66);
- guest cosmetic bag preserved by signing in (#67);
- validated per-product budget filtering (#61);
- corrected in-category product replacement with the correct number of alternatives
  (#62);
- finalized LLM explanation prompt, disabled by default (#63);
- updated customer handover, roadmap, UAT, and the Week 7 report set;
- the repository and secrets handover package (#64).

## Testing and quality

- Testing: `docs/testing.md`
- Quality requirements: `docs/quality-requirements.md`
- Quality requirement tests: `docs/quality-requirement-tests.md`
- Definition of Done: `docs/definition-of-done.md`

## Customer review and acceptance

- Sprint Review recording: shared privately via Moodle.
- Sprint Review summary: `reports/week7/sprint-review-summary.md`
- Sprint Review notes: `reports/week7/sprint-review-notes.md`
- Feedback traceability: `reports/week7/customer-feedback-traceability.md`
- Customer confirmation status: `Accepted with follow-up items`; handover level
  `Ready for independent use` (see `docs/customer-handover.md`).

## Public demo

Public sanitized demo video (MVP v3):
https://drive.google.com/drive/folders/1oT0mSEMmlGJWGsdO9V_DbxgnTE3d6uI0?usp=drive_link

## GitLab release link

https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v1.0.0

## Follow-ups (post-defense)

- Repository and secrets handover over a secure channel (#64);
- Customer-authored LLM prompt integrated and verified against the filtration-sample
  contract (#63).
