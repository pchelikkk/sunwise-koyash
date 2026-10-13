# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Documentation

- Added a GitLab Pages documentation portal and routed the repository entry point to it.
- Completed the Assignment 6 Week 6 and Week 7 public evidence indexes with hosted
  documentation, factual release/MR links, contribution traceability, UAT outcomes,
  transition status, and inspectable screenshots.
- Updated the roadmap to identify v1.0.1 as the final course state without speculative
  post-course release planning.

## [1.0.1] - 2026-07-19

MVP v3 patch release after the final customer-prompt and presentation-readiness audit.

### Added

- The customer-authored explanation prompt now receives both the complete user
  concern list and the exact product-level `matched_concerns` as separate fields.
- Runtime policy validation rejects overlong, medical, unsupported, incorrectly
  personalized, or factually ungrounded LLM explanations before they reach users.
- Adaptive deterministic skin-type guidance for users who select “I do not know”.
- A fifteen-question professional questionnaire with conditional diagnostic steps.
- A faceted, paginated product catalog with full product details and dynamic counts.
- Authenticated favorites, a server-synced cosmetic bag with guest migration, and
  server-owned recommendation history.
- Native share/copy support for completed routines with an admin share KPI.
- A protected catalog-quality view alongside the aggregate admin analytics dashboard.
- A polished responsive React experience based on the approved Figma direction.
- A safe admin catalog issue queue and editor for media, product links, usage
  instructions, and activation status, with an audit event for every update.
- Idempotent startup synchronization of the validated 69-product canonical dataset.
- Vitest and Playwright coverage for questionnaire branching, catalog details,
  authentication, the admin workspace, and desktop/mobile layouts.

### Changed

- Recommendation responses now expose the resolved skin profile and diagnostic
  confidence without changing the deterministic selection boundary.
- Password-reset links now open a functional SPA reset route.
- Product responses expose catalog-backed ingredients, values, volume, pricing, and
  source metadata needed by the user interface.
- Questionnaire copy, answer labels, and explanations now use plain, user-friendly
  Russian and keep neutral answers exclusive.
- Minimum and balanced budgets are enforced as hard per-product price caps.
- Missing usage instructions and safe external URLs are normalized during import.
- Official EMANSI, Tony Morris, and Maskoholic prices, links, instructions, and imagery
  raise active-catalog image coverage to 98.5% without substituting lookalike products.
- GitLab CI now runs Ruff, backend tests, frontend unit tests, dependency audit,
  production build, and browser end-to-end tests.

### Security

- Password-reset token consumption is atomic and access tokens are revoked after a
  password change through per-user authentication versioning.
- Recommendation, feedback, and replacement resources enforce owner access for both
  authenticated and anonymous sessions without revealing whether another user's
  recommendation exists.

## [1.0.0] - 2026-07-19

Final MVP v3 release.

### Added

- Detected skin type shown on the questionnaire result (#66).
- Guest cosmetic bag preserved by signing in (#67).
- Week 7 report set under `reports/week7/` (README, sprint review summary and notes, customer feedback traceability, reflection, retrospective, LLM usage report, release notes).
- UAT scenarios UAT-08 (skin type shown) and UAT-09 (guest bag preserved).

### Changed

- Shipped the redesigned, more functional frontend as the final MVP v3 direction (#50).
- Validated and enforced per-product budget filtering (#61).
- Corrected in-category product replacement to return only genuinely available items (#62).
- Finalized the LLM explanation prompt; the layer stays disabled by default (#63).
- Bumped backend and frontend version to 1.0.0.
- Root README, `docs/roadmap.md`, `docs/customer-handover.md`, `docs/user-acceptance-tests.md`, and `AGENTS.md` updated for the final MVP v3.
- Customer transition recorded: handover level `Ready for independent use`, confirmation status `Accepted with follow-up items`.

### Removed

- Product catalog and favorites removed as out of product concept (#65).

## [0.4.0] - 2026-07-12

### Added

- Week 6 trial deployment on the university VM toward the final MVP v3.
- `CONTRIBUTING.md` and `AGENTS.md` as top-level contributor and LLM-layer entry points.
- `docs/customer-handover.md` describing how to run, operate, and take ownership of KOYASH, plus the transition status.
- Week 6 report set under `reports/week6/` (README, sprint review summary and notes, customer feedback traceability, reflection, retrospective, LLM usage report).
- UAT scenarios UAT-06 (per-product budget filtering) and UAT-07 (independent use).
- Release notes for the Sprint 4 / Week 6 trial increment.

### Changed

- Root README updated for the Week 6 trial and the v0.4.0 release.
- `docs/roadmap.md` extended with the Assignment 6 / Sprint 4 increment and the Week 7 plan.
- Questionnaire trimmed from 7 to 6 steps per customer request.
- Budget filtering applied per product across the recommendation set (pending customer validation).
- Application version bumped to 0.4.0.

### Notes

This release represents the Sprint 4 / Assignment 6 increment: an integrated Week 6 trial
(MVP v3 candidate) with a working backend, a facilitated customer trial / UAT / Sprint
Review with Diana, an approved design direction, and the supporting documentation.
Applying the approved design 1:1, the replacement-category fix, filtering validation, and
the repository/secrets handover are tracked for Week 7 (#50, #61–#64).

## [0.3.0] - 2026-07-05

### Added

- Full-stack integration of the React SPA with the FastAPI backend through a typed API client.
- Single-port production deployment: nginx serves the built SPA and reverse-proxies `/api` to the backend (no CORS configuration).
- `frontend` service in `docker-compose.yml`, `frontend/Dockerfile`, `frontend/nginx.conf`, and `frontend/.env.example`.
- Backend analytics ingestion endpoint (`POST /api/v1/analytics/events`).
- Architecture documentation with static, dynamic, and deployment views as diagrams-as-code, plus Architecture Decision Records (ADR-0001..0004).
- Development process documentation with a git workflow gitGraph and configuration management.
- UAT scenarios UAT-04 (account and recommendation history) and UAT-05 (feedback and replacement).
- Quality requirement tests QRT-04 and QRT-05.
- New backend tests (`test_recommendation_contract.py`) and CI coverage for auth tests.
- Week 5 report artifacts and release notes for the Sprint 3 increment.
- Customer feedback traceability for the Sprint Review conducted with Diana.

### Changed

- Recommendation, feedback/replacement, authentication, account, and history flows now call the live backend API.
- QA documentation (testing, quality requirements, quality requirement tests, Definition of Done) updated to reflect MVP v2.
- Root README rewritten for the integrated MVP v2 and the v0.3.0 release.
- Application version bumped to 0.3.0.

### Removed

- Broken legacy backend test (`backend/tests/legacy_test_api.py`).

### Notes

This release represents the Sprint 3 / Assignment 5 increment: the first integrated,
end-to-end MVP v2 running as a single deployable stack on the university VM, with
architecture, process, testing, UAT, and release documentation.

## [0.2.0] - 2026-06-28

### Added

- Latest adaptive MVP v1 prototype.
- Deployed MVP v1 access through the university VM.
- Public sanitized demo video.
- Presentation deck for Assignment 4.
- Customer UAT and Sprint Review recording.
- Backend API tests.
- GitLab CI checks for backend tests, frontend build, prototype artifact, and links.
- Quality requirements for Assignment 4.
- Quality requirement tests.
- Testing documentation.
- User acceptance test scenarios.
- VM deployment documentation.
- Week 4 report structure.
- Release notes for the Sprint 2 increment.

### Changed

- Prepared the repository for the final Assignment 4 submission.
- Updated documentation around testing, UAT, deployment, and release evidence.
- Connected the Sprint 2 increment to customer feedback received from Diana.
- Prepared the project for v0.2.0 release.

### Notes

This release represents the Sprint 2 / Assignment 4 increment prepared for customer UAT, Sprint Review, VM deployment, public demo, presentation, and final course submission.
