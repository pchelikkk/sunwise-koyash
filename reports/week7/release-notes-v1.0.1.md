# Release Notes — v1.0.1

Project: KOYASH  
Assignment: 6  
Increment: MVP v3 patch  
Date: 2026-07-19

## Purpose

This patch closes the final post-release audit without changing the deterministic
recommendation boundary. It integrates the customer-authored constrained LLM prompt,
strengthens policy validation and fallback behavior, completes the production-facing
frontend and admin experience, and records the final Demo Day evidence.

## Verification

- Backend: 195 tests, Ruff and compileall passed.
- Frontend: 5 unit tests and 26 desktop/mobile E2E tests passed.
- Production build passed; npm audit reports 0 vulnerabilities.
- Customer JSON validator: 8 valid and unique cosmetic bags, 69 dataset products,
  68 active products, no validation errors or validator warnings.

## Required Assignment 6 links

- Sprint 5 milestone: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/milestones/5
- Product access: http://10.93.26.208:8080/
- Run instructions: ../../README.md
- Customer handover: ../../docs/customer-handover.md
- Week 7 report: README.md
- Public sanitized demo: https://drive.google.com/drive/folders/1oT0mSEMmlGJWGsdO9V_DbxgnTE3d6uI0?usp=drive_link
- Changelog: ../../CHANGELOG.md
- GitLab release: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v1.0.1

## Compatibility and rollback

This is a backward-compatible patch over `v1.0.0`. The previous final release remains
available as the immediate rollback point. Runtime secrets are not stored in Git.
