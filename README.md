# KOYASH

Skincare recommendation web app developed by **Team Sunwise** for the Software Project course at Innopolis University.

## Features and stack

- Guided questionnaire, deterministic product recommendations and replacement suggestions.
- Accounts and saved recommendation history.
- Protected admin analytics and catalog management.
- Optional LLM explanations with deterministic fallback.
- React/Vite, FastAPI, MongoDB, Docker Compose/nginx.

## Run locally

Requires Docker Engine / Docker Desktop with Compose.

```powershell
Copy-Item backend/.env.example backend/.env
# Replace JWT_SECRET_KEY in backend/.env with a unique 32+ byte secret.
docker compose up -d --build
```

Open http://localhost:8080/ (API documentation: http://localhost:8000/docs).
The default Compose file uses local development database credentials. LLM explanations are disabled by default; the recommendation engine works without an API key.

The original university deployment is accessible only from the university network. This repository provides source code for local deployment, not a public hosted demo.

## Documentation

- [Architecture](docs/architecture/README.md)
- [Recommendation algorithm](docs/recommendation-algorithm.md)
- [Development process](docs/development-process.md)
- [Testing](docs/testing.md)
- [Changelog](CHANGELOG.md)
- [Original v1.0.1 release notes](reports/week7/release-notes-v1.0.1.md)

## Source and publication notes

Portfolio copy from the downloaded GitLab `main` archive, containing the documented final course release **v1.0.1** and later documentation updates. The original GitLab currently returns HTTP 403 from this environment.

The archive does not contain `.git`, original commits, tags or release attachments. Earlier releases cannot be reconstructed from this snapshot. The GitHub release is explicitly a portfolio snapshot, not a mirror of the original release history.

Team attribution and the original MIT license are preserved. Customer review exports, consultation worksheet, recordings and report screenshots are excluded. The catalog includes only the `Products` worksheet (69 product rows). Example email placeholders are normalized. [Original archived README](ARCHIVE_README.md) retains historical links; some reference unavailable GitLab pages or omitted review artifacts.

## Verification of this copy

Python sources parse successfully; the cleaned catalog is accepted by the product importer. Frontend build and five frontend tests passed during the archive review. Full-stack/backend integration tests require MongoDB and have not been run for this publication; Docker Engine is currently unavailable locally.
