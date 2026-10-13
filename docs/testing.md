# Testing

Project: KOYASH  
Team: Sunwise  
Assignment: 6
Release: v0.4.0 + unreleased professional product increment

## Testing strategy

The professional product increment uses backend API/integration tests, frontend unit
tests, browser end-to-end tests, a production build, dataset audits, and visual QA.

Automated backend tests cover:

- backend and database availability (`/health`);
- questionnaire structure;
- adaptive skin-type diagnosis and conditional questionnaire steps;
- restriction suggestions and custom restriction normalization;
- product catalogue seeding, lookup, filters, sorting, facets, and quality metrics;
- recommendation creation, explanations, scoring, and hard exclusions;
- feedback and replacement flow;
- registration, login, current user, and profile updates;
- favorites, server-synced cosmetic bag, owned recommendation history, and
  password-reset invalidation;
- privacy-safe administrator analytics and authorization boundaries;
- recommendation contract stability and input validation.

## Automated backend tests

Backend tests are located in `backend/tests/`:

| Test file | Area |
|---|---|
| `test_health.py` | Backend and database availability |
| `test_questionnaire.py` | Questionnaire structure and custom restrictions |
| `test_restrictions.py` | Restriction suggestions and alias normalization |
| `test_products.py` | Product catalogue seeding and lookup |
| `test_product_catalog.py` | Faceted product catalog filters, sorting, and validation |
| `test_product_dataset_sync.py` | Validated and idempotent 69-product startup synchronization |
| `test_skin_diagnosis.py` | Deterministic diagnosis and unknown-type recommendation flow |
| `test_user_library.py` | Favorites, cosmetic bag, and recommendation history |
| `test_admin_catalog.py` | Administrator-only catalog quality metrics |
| `test_recommendations.py` | Recommendation creation, explanations, exclusions |
| `test_feedback_replacements.py` | Feedback and product replacement flow |
| `test_auth_users.py` | Registration, login, current user, profile |
| `test_recommendation_contract.py` | Recommendation stability and input validation |

## How to run backend tests locally

The tests start the FastAPI application, which connects to MongoDB and seeds initial
data, so a MongoDB instance must be available.

```text
# Start a local MongoDB.
docker run -d --name koyash-mongo-test -p 27017:27017 \
-e MONGO_INITDB_ROOT_USERNAME=koyash \
-e MONGO_INITDB_ROOT_PASSWORD=koyash_dev_password \
mongo:7

cd backend
python -m pip install -r requirements.txt
export MONGO_URI="mongodb://koyash:koyash_dev_password@localhost:27017/?authSource=admin"
export MONGO_DB_NAME="koyash_test"
export JWT_SECRET_KEY="koyash-test-secret-key-at-least-32-bytes"
python -m ruff check app tests
PYTHONPATH=. pytest
```

## Frontend automated tests

From `frontend/`:

```text
npm ci
npm audit --audit-level=high
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Vitest verifies adaptive question visibility, request normalization, and exclusive
neutral answers. Playwright runs the landing, adaptive questionnaire, product detail,
replacement, saved-collection migration, recommendation sharing, authentication, and
administrator catalog-editor flows in Desktop Chrome and a Pixel 7 viewport. The
landing scenario also fails on horizontal overflow or console errors.

## Continuous integration

The root `.gitlab-ci.yml` runs three independent jobs on merge requests and the default
branch: Ruff plus backend tests against MongoDB 7; frontend audit/unit/build; and
Playwright desktop/mobile E2E in the matching official browser image.

## Critical artifacts

| Artifact | Why it is critical | Verification |
|---|---|---|
| `backend/tests/` | Verifies the backend/API behavior of MVP v2 | Automated tests + CI |
| `frontend/src/` | Integrated SPA served by nginx | UAT + deployed MVP |
| `docker-compose.yml` | Reproducible deployment of the full stack | Deployed MVP review |
| `docs/user-acceptance-tests.md` | Customer-facing acceptance scenarios | UAT session |
| `reports/week5/README.md` | Main Week 5 evidence index | Manual review |

## Deployed MVP

`http://10.93.26.208:8080/`

## UAT evidence

Customer UAT recording (customer walkthrough):

`https://youtu.be/NJOCVpa68-4`

Sprint Review recording:

`https://drive.google.com/file/d/1i7aIeD_VB48icuNjcxg_aJ-wGxWxNz9B/view`

## Public demo evidence

Public demo video:

`https://youtu.be/wyW-npfxQjs`

## Current evidence

The exact local gate results for this increment are kept in
`docs/release-readiness-v1.md`. Customer approval and merge remain separate review
steps; they are not substituted by automated tests.
