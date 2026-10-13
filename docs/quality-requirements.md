# Quality Requirements

Project: KOYASH  
Team: Sunwise  
Assignment: 5  
Release: v0.3.0

## Quality model

The team uses ISO/IEC 25010 quality characteristics and sub-characteristics to define measurable quality requirements for the Sprint 2 / Assignment 4 increment.

The selected quality requirements focus on:

- correctness of recommendation data and explanations;
- reliability of the main MVP flow;
- usability of the questionnaire and result experience.

---

## QR-01 — Recommendation constraint correctness

- ISO/IEC 25010 characteristic: Functional suitability
- Sub-characteristic: Functional correctness
- Priority: High
- Related scope: MVP v1 product recommendation/result screen

### Requirement

The recommendation result must provide product cards with enough structured information to support explainable skincare recommendations.

### Rationale

The main value of KOYASH is not just showing a product list, but helping the user understand why a cosmetic bag was recommended. During the project, the team identified explainability as a key part of trust in the MVP.

### Acceptance criteria

- The result contains product cards.
- Product cards contain product name.
- Product cards contain brand.
- Product cards contain category.
- Product cards contain positive price.
- Product cards contain explanation/reason text.
- The user can understand why products were selected.

### Verification

Covered by QRT-01.


### Related architecture decisions

- ADR 0002 — MongoDB as the primary data store (`docs/architecture/adr/0002-mongodb-primary-datastore.md`)
- ADR 0003 — Layered backend architecture (`docs/architecture/adr/0003-layered-backend-architecture.md`)

---

## QR-02 — Main flow availability

- ISO/IEC 25010 characteristic: Reliability
- Sub-characteristic: Availability
- Priority: High
- Related scope: backend/API technical foundation and deployed MVP access

### Requirement

The MVP technical foundation must remain available for the main review scenario.

### Rationale

Assignment 4 requires the latest Sprint increment to be accessible for customer UAT and TA review. The system must provide a stable access point for the deployed MVP and backend/API checks where applicable.

### Acceptance criteria

- The deployed MVP URL opens successfully.
- The user can access the main KOYASH prototype.
- The backend health endpoint returns an OK response if backend is exposed in the deployment.
- The main review scenario is not blocked by missing deployment instructions.

### Verification

Covered by QRT-02.


### Related architecture decisions

- ADR 0001 — Single-port nginx serving the SPA and reverse-proxying the API (`docs/architecture/adr/0001-single-port-nginx-reverse-proxy.md`)
- ADR 0004 — Data seeding on application startup (`docs/architecture/adr/0004-startup-data-seeding.md`)

---

## QR-03 — Questionnaire operability

- ISO/IEC 25010 characteristic: Usability
- Sub-characteristic: Operability
- Priority: High
- Related scope: MVP v1 landing page, questionnaire, result screen

### Requirement

A first-time user must be able to open KOYASH, understand the purpose of the product, start the questionnaire, complete it, and reach the recommendation result without registration or external instructions.

### Rationale

The customer feedback emphasized that the product should feel understandable, warm, and guided. The MVP should not feel like a dry technical form or generic AI-generated interface.

### Acceptance criteria

- The landing page communicates the product purpose.
- The main CTA is visible.
- The questionnaire is understandable.
- The user can complete the main scenario.
- The result screen is reachable.
- The product reasoning is readable.

### Verification

Covered by QRT-03.


### Related architecture decisions

- ADR 0001 — Single-port nginx serving the SPA and reverse-proxying the API (`docs/architecture/adr/0001-single-port-nginx-reverse-proxy.md`)