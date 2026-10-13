# Week 5 Report — KOYASH

Project: KOYASH  
Team: Sunwise  
Assignment: 5  
Sprint: 3  
Release: v0.3.0  
Customer: Diana

## Overview

This week the team delivered the first integrated end-to-end increment (MVP v2): the
React SPA and the FastAPI backend now run together as a single deployable stack on the
university VM. The rest of the work packaged the increment with architecture, process,
testing, UAT, and release documentation.

## Deployed MVP

`http://10.93.26.208:8080/`

## What is new in MVP v2

- Frontend and backend are integrated through a typed API client.
- Single-port deployment: nginx serves the SPA and reverse-proxies `/api` to the
  backend (no CORS configuration).
- Live questionnaire, recommendations, feedback/replacements, authentication, account,
  and history flows.
- Analytics event ingestion endpoint.

## Evidence

- Customer UAT recording (customer walkthrough): `https://youtu.be/NJOCVpa68-4`
- Sprint Review recording: `https://drive.google.com/file/d/1i7aIeD_VB48icuNjcxg_aJ-wGxWxNz9B/view`
- Public demo video: `https://youtu.be/wyW-npfxQjs`

> At the time of the recorded walkthrough the SPA was shown with placeholder data; the
> backend integration landed immediately after and is covered by automated tests and
> the deployed MVP.

## Documentation index

| Area | Document |
|---|---|
| Architecture (views + ADRs) | `docs/architecture/README.md` |
| Development process | `docs/development-process.md` |
| Quality requirements | `docs/quality-requirements.md` |
| Quality requirement tests | `docs/quality-requirement-tests.md` |
| Testing | `docs/testing.md` |
| Definition of Done | `docs/definition-of-done.md` |
| User acceptance tests | `docs/user-acceptance-tests.md` |
| Customer feedback traceability | `reports/week5/customer-feedback-traceability.md` |
| Roadmap | `docs/roadmap.md` |
| Release notes | `reports/week5/release-notes.md` |
| Retrospective | `reports/week5/retrospective.md` |

## Sprint 3 summary

- Milestone: Sprint 3.
- Delivered: full-stack integration (#41), VM deployment of the integrated stack (#42),
  architecture docs (#43), ADRs (#44), development process (#45), tests and QA docs
  (#46), UAT update (#47), feedback traceability and roadmap (#48), release v0.3.0
  (#49), and the supporting user stories (#18, #19, #20).
- Deferred: a larger design overhaul based on the latest customer feedback is tracked as
  a backlog item (#50) for the next sprint, with rationale documented in the feedback
  traceability report.

## Customer feedback

The Sprint Review confirmed the integrated direction resolves the customer's main
earlier gaps. New design-oriented feedback from this session is captured and prioritized
for the next sprint. See `reports/week5/customer-feedback-traceability.md`.