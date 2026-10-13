# KOYASH

KOYASH is a skincare recommendation product developed by Team Sunwise for the
Software Project course.

Users complete a guided skincare questionnaire and receive an explainable cosmetic
bag recommendation. The React SPA and the FastAPI backend run together as a single
deployable stack.

## Current status

v1.0.1 is the final MVP v3 patch release (Sprint 5 / Week 7). It ships the redesigned frontend and the
customer-trial follow-ups (catalog/favorites removed, detected skin type shown, guest
bag saving), validated per-product budget filtering, corrected in-category product
replacement, and a guarded LLM explanation layer. The protected administrator workspace
adds analytics, catalog-quality controls and validated CSV/XLSX import. The customer
accepted the product with the documented post-defense handover actions and confirmed
readiness for Demo Day.

## Current release

Release: v1.0.1

Release link:

https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v1.0.1

## Product and documentation

- **Open the deployed product:** http://10.93.26.208:8080/
- **Open the hosted documentation:** https://s-anisimov.gitlab.pg.innopolis.university/sunwise-koyash/
- **Customer handover:** [docs/customer-handover.md](docs/customer-handover.md)
- **Contribution guide:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **AI/agent guidance:** [AGENTS.md](AGENTS.md)

Previous final release: v1.0.0 —
https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v1.0.0

Week 6 trial release: v0.4.0 —
https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v0.4.0

## Deployed app

Final product access on the university VM (single public port):

http://10.93.26.208:8080/

The SPA and the API share the same origin through nginx, so no CORS configuration is
required.

## Maintained engineering documentation

- [Architecture](docs/architecture/README.md) (static, dynamic, deployment views and ADRs)
- [Administrator security boundary](docs/admin-security.md)
- [Development process and configuration management](docs/development-process.md)
- [Quality requirements](docs/quality-requirements.md) and [testing](docs/testing.md)
- [Product experience](docs/product-experience-v3.md) and [questionnaire contract](docs/professional-questionnaire-v3.md)
- [Definition of Done](docs/definition-of-done.md), [roadmap](docs/roadmap.md), and
  [user acceptance tests](docs/user-acceptance-tests.md)

## Repository structure

backend/            FastAPI backend (API, services, algorithms, repositories, seed)
frontend/           React/Vite SPA + Dockerfile + nginx config
docs/               Project documentation (architecture, QA, UAT, process)
reports/week2..7/   Weekly report artifacts
docker-compose.yml  Full-stack deployment (frontend + backend + mongo)

## Run the full stack

1. Create the backend env file and set a real secret:

cp backend/.env.example backend/.env   # then set a real JWT_SECRET_KEY

   `MONGO_URI` already points to the `mongo` service defined in docker-compose.

2. Build and start everything:

docker compose up -d --build

   On startup the backend validates and idempotently synchronizes the canonical
   `data/products.xlsx` catalog. Invalid rows stop synchronization instead of entering
   recommendations.

3. Open the app (single entry point):

   http://localhost:8080/

   The API is reachable same-origin under `http://localhost:8080/api/v1/...`.
   Interactive API docs are at `http://localhost:8000/docs`.

## Presentation admin and optional LLM

Create or refresh a local-only administrator without committing its password:

```powershell
docker compose exec -T `
  -e KOYASH_DEMO_ADMIN_EMAIL=admin@koyash-demo.ru `
  -e KOYASH_DEMO_ADMIN_PASSWORD='<strong-local-password>' `
  backend python scripts/create_demo_admin.py
```

Populate deterministic presentation analytics (the cleanup flag removes only known
local test accounts and legacy sample-product activity):

```powershell
docker compose exec -T backend python scripts/seed_demo_analytics.py --clean-legacy-demo
```

For direct OpenAI explanations, put `OPENAI_API_KEY` in `backend/.env`, keep
`LLM_PROVIDER=openai`, switch `LLM_ENABLED=true`, and recreate the backend container.
The model can rewrite only the short explanation of an already selected product; it
cannot change products, scores, hard exclusions, or usage instructions.

## Run components locally (development)

Backend:

cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload

Frontend:

cd frontend
npm install
npm run dev

   Vite proxies `/api` to the local backend on port 8000, matching the production nginx
   contract.

## Backend API

The API is served under the `/api/v1` prefix and includes:

- questionnaire;
- adaptive, deterministic skin-type guidance for users who are unsure of their type;
- recommendations (create, load, explanations, scoring, hard exclusions);
- internal product/catalog services, recommendation-scoped product details, routine
  sharing, and owner-checked recommendation history;
- feedback and product replacements;
- authentication (register, login, token) and account/profile;
- restrictions suggestions and custom restriction normalization;
- privacy-aware analytics event ingestion and protected admin dashboards;
- administrator catalog issue review and audited safe-field editing;
- owner-checked recommendation, feedback, and replacement access;
- health check (`/health`, `/api/v1/health`).

## Tests

Backend tests are located in `backend/tests/`. They start the application and require a
MongoDB instance.

docker run -d --name koyash-mongo-test -p 27017:27017 \
-e MONGO_INITDB_ROOT_USERNAME=koyash \
-e MONGO_INITDB_ROOT_PASSWORD=koyash_dev_password \
mongo:7
cd backend
python -m pip install -r requirements.txt
export MONGO_URI="mongodb://koyash:koyash_dev_password@localhost:27017/?authSource=admin"
export MONGO_DB_NAME="koyash_test"
export JWT_SECRET_KEY="koyash-test-secret-key-at-least-32-bytes"
PYTHONPATH=. pytest

See `docs/testing.md` for the full test map and CI details.

Catalog prices and product images can be checked against approved merchant pages
in dry-run mode and applied with guarded, atomic workbook writes. See
`docs/catalog-metadata-refresh.md`.

Current release-readiness evidence is recorded in `docs/release-readiness-v1.md`.

## CI

GitLab CI runs the backend test suite against a `mongo:7` service on merge requests and
on the default branch. The configuration is in `.gitlab-ci.yml`.

## User acceptance testing

UAT scenarios are documented in `docs/user-acceptance-tests.md`. Customer UAT and the
Sprint Reviews were conducted with the customer, Diana.

- Week 7 final review summary: `reports/week7/customer-review-summary.md`
- Week 7 feedback traceability: `reports/week7/customer-feedback-traceability.md`
- Customer filtering/LLM review JSON: `docs/customer-review/koyash-cosmetic-bags-samples.json`
- Week 6 customer trial + UAT + Sprint Review notes: `reports/week6/sprint-review-notes.md`
- Week 7 Sprint Review notes: `reports/week7/sprint-review-notes.md`
- Public demo video (MVP v3): https://drive.google.com/drive/folders/1oT0mSEMmlGJWGsdO9V_DbxgnTE3d6uI0?usp=drive_link
- Previous customer UAT recording: https://youtu.be/NJOCVpa68-4

## Reports

- Week 7 (current): `reports/week7/README.md`
- Week 6: `reports/week6/README.md`
- Week 5: `reports/week5/README.md`
- Week 4: `reports/week4/README.md`
- Week 3: `reports/week3/`
- Week 2: `reports/week2/`

## Release notes

- v1.0.1: `reports/week7/release-notes-v1.0.1.md`
- v1.0.0: `reports/week7/release-notes.md`
- v0.4.0: `reports/week6/release-notes.md`
- Changelog: `CHANGELOG.md`

## Team

Team Sunwise.
