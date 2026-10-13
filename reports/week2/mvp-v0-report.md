# MVP v0 Report

## Purpose

The purpose of MVP v0 is to demonstrate that the KOYASH product has a runnable technical foundation.

MVP v0 is not intended to implement the full recommendation system. It shows that the frontend, backend, Docker setup, and basic API communication work correctly.

## Implemented functionality

MVP v0 includes:

* React frontend created with Vite;
* FastAPI backend;
* Docker Compose setup;
* backend health check endpoint;
* sample products API endpoint;
* frontend button for checking backend status;
* frontend button for loading sample products from the backend;
* basic product card rendering.

## Runnable artifact

The project can be run locally using Docker Compose.

Repository local setup instructions are available in the root `README.md`.

Run from the repository root:

```bash
docker compose up --build
```

Then open:

```text
Frontend:
http://localhost:5173

Backend health check:
http://localhost:8000/health

Sample products API:
http://localhost:8000/api/sample-products
```

## MVP v0 demo video

Video link:

```text
https://drive.google.com/file/d/1p6ZeusoUYIeFc3152ZiSlrldobR33cX-/view?usp=sharing
```

The video demonstrates:

* starting the project with Docker Compose;
* opening the frontend;
* checking backend status from the frontend;
* loading sample products from the backend;
* opening the backend health endpoint;
* opening the sample products API endpoint.

## Smoke check scenario

The repeatable smoke check scenario is:

1. Start Docker Desktop.
2. Run:

```bash
docker compose up --build
```

3. Open:

```text
http://localhost:5173
```

4. Click **Check backend**.

Expected result:

```text
Backend status is displayed on the frontend.
```

5. Click **Load sample products**.

Expected result:

```text
Sample product cards are displayed on the frontend.
```

6. Open:

```text
http://localhost:8000/health
```

Expected result:

```json
{
  "status": "ok",
  "service": "koyash-api",
  "version": "0.0.1"
}
```

7. Open:

```text
http://localhost:8000/api/sample-products
```

Expected result:

```text
The backend returns sample skincare product data.
```

## Relationship to MVP v1 scope

MVP v0 supports the technical foundation for the selected MVP v1 scope.

The selected MVP v1 scope includes:

* US-01: Understand the service from the landing page;
* US-02: Complete a step-by-step questionnaire;
* US-03: Select a comfortable budget;
* US-04: Exclude allergens and unwanted ingredients;
* US-05: Receive rule-based recommendations from the database;
* US-06: View a personal cosmetic bag;
* US-07: Understand why each product was recommended.

MVP v0 does not fully implement these stories yet. Instead, it proves that the team can run the application, connect frontend and backend, and display product data received from an API.

## Limitations

Current MVP v0 limitations:

* no real product database yet;
* sample products are hardcoded;
* no full questionnaire implementation;
* no real recommendation algorithm;
* no user accounts;
* no admin panel;
* no persistent storage;
* no production deployment yet;
* no LLM-based recommendation logic.

These limitations are expected for MVP v0. They will be addressed in later project stages according to the approved MVP scope.

## Evidence screenshots

Evidence screenshots are stored in:

```text
reports/week2/images/
```

Relevant screenshots include:

* MVP v0 frontend smoke check;
* backend health endpoint;
* sample products API endpoint.
