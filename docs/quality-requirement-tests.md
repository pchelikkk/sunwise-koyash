# Quality Requirement Tests

Project: KOYASH  
Team: Sunwise  
Assignment: 5  
Release: v0.3.0

---

## QRT-01 — Product data and explanation check

- Linked quality requirement: QR-01
- Test type: Automated backend/API test
- Location: `backend/tests/test_products.py`, `backend/tests/test_recommendations.py`

### Purpose

Verify that product data and generated recommendation items contain the information
required for explainable recommendation cards.

### Expected result

- Seeded products expose stable identifiers and required fields.
- Recommendation items contain a positive score, explanation fields (`why_here`,
  `budget_reason`, `safety_note`, `how_to_use`), and a consistent score breakdown.

### Evidence

Backend/API tests and the CI pipeline.

---

## QRT-02 — Backend and database availability check

- Linked quality requirement: QR-02
- Test type: Automated API smoke test
- Location: `backend/tests/test_health.py`

### Purpose

Verify that the backend and its database dependency are available for the main flow.

### Expected result

The `/health` and `/api/v1/health` endpoints return HTTP 200, status `ok`, and a
database status of `ok`.

### Evidence

Backend/API tests and the CI pipeline.

---

## QRT-03 — Questionnaire and main flow operability

- Linked quality requirement: QR-03
- Test type: Automated API test + UAT scenario
- Location: `backend/tests/test_questionnaire.py`, `backend/tests/test_recommendations.py`, `docs/user-acceptance-tests.md`
- Deployed MVP: `http://10.93.26.208:8080/`

### Purpose

Verify that the questionnaire is well-formed and that a user can complete the main
flow and reach a recommendation result.

### Expected result

The questionnaire returns the expected structure, a recommendation can be created from
questionnaire answers, and the customer can complete the flow on the deployed MVP.

### Evidence

- automated tests;
- customer UAT recording (`https://youtu.be/NJOCVpa68-4`);
- deployed MVP link.

---

## QRT-04 — Registration, login, and profile check

- Linked quality requirement: QR-01, QR-02
- Test type: Automated backend/API test
- Location: `backend/tests/test_auth_users.py`

### Purpose

Verify that users can register, log in, retrieve their profile, and update it, and that
protected endpoints reject unauthenticated access.

### Expected result

- Registration returns a bearer token and a linked profile.
- Duplicate registration returns 409; wrong password returns 401.
- `users/me` requires a valid token; profile updates persist.

### Evidence

Backend/API tests and UAT-04.

---

## QRT-05 — Feedback and replacement check

- Linked quality requirement: QR-01
- Test type: Automated backend/API test
- Location: `backend/tests/test_feedback_replacements.py`

### Purpose

Verify that product feedback produces suitable replacement candidates and that a
replacement can be selected.

### Expected result

- Feedback returns replacement candidates for the same routine step.
- Replacements can be listed and one can be selected.
- Feedback on an unknown recommendation returns 404.

### Evidence

Backend/API tests and UAT-05.