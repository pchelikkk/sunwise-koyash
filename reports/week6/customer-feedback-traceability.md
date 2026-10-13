# Customer Feedback Traceability

Project: KOYASH  
Team: Sunwise  
Assignment: 6

## Purpose

This document connects customer feedback from the Week 6 facilitated trial / UAT /
Sprint Review to product decisions, resulting backlog items, and follow-up roadmap work.

## Session context

The team demonstrated a working backend with the current frontend. The customer
interacted with the flow and gave live feedback (session recorded). Unlike the previous
review, the customer did not test the product fully independently, because the frontend
was not yet ready for unfacilitated use.

## Traceability table

| Area | Customer feedback | Decision | Resulting PBI | Status |
|---|---|---|---|---|
| Design | Mockups approved with minor edits as final MVP v3 direction | Apply approved design 1:1 across screens | #50 | Planned |
| Routine labeling | Label the routine as morning / evening | Add explicit morning/evening labels | #50 | Planned |
| Budget filtering | Filtering must apply per product, not only to the total | Validate per-product filtering; customer checks 3–5 samples | #61 | Pending validation |
| Product replacement | A gel must not replace a cream | Enforce same-category replacement + tests | #62 | Planned |
| Questionnaire | Too many steps | Trim questionnaire from 7 to 6 steps | #50 | Planned |
| Explanations | Keep explanations clear and trustworthy | Update LLM prompt and evaluate jointly | #63 | Planned |
| Handover | Take over repo/deployment after defense | Transfer repository and secrets after the defense | #64 | Planned |
| Documentation | Review the README | Update README for the trial | #51 | Done |

## Roadmap impact

- Week 6 trial (this increment): working backend end to end, facilitated trial, approved
  design direction, v0.4.0 release.
- Week 7 (MVP v3 final): validated filtering, corrected replacement logic, approved
  design applied 1:1, LLM prompt evaluation, public demo, and handover.

## Summary

The Week 6 trial produced concrete, testable feedback because the backend was live. The
design direction is now settled, and the remaining work is a small set of well-scoped
follow-ups (#50, #61–#64) toward the final MVP v3.
