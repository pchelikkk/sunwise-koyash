# Customer Feedback Traceability

Project: KOYASH  
Team: Sunwise  
Assignment: 5

## Purpose

This document connects customer feedback from the MVP v1 review / facilitated UAT
session to product decisions, resulting backlog items, and follow-up roadmap work.

## Session context

The customer reviewed the **frontend prototype** during the recorded session
(customer-executed walkthrough from ~00:11:00). At review time the backend was not
yet connected, so demonstrated data was placeholder (e.g. a non-existent "SPF 50"
item). Frontend↔backend integration and deployment (MVP v2) were completed
immediately after the review.

## Traceability table

| Area | Evidence | Customer feedback | Decision | Resulting PBI | Status |
|---|---:|---|---|---|---|
| Backend integration | 14:23–15:17 | Backend not connected; data is random | Integrate frontend with real backend data | #41 | Done |
| Filtering | 15:17 | Filtering is missing / expected | Filter by skin type, concerns, budget via API; deeper faceting on roadmap | #41 | Partially done |
| Total price | 16:04 | Total sum should be visible | Show total on the result screen | #41 | Done |
| Product images | 09:19–10:47 | Show product image; concern about scale (300+) and low-quality images | Keep image slot; decide sourcing/scaling with backend | #18 | Under review |
| Budget labels | 12:16–12:53 | Rename to "Бюджетный / Средний сегмент / Люкс" | Rename frontend display labels (enum unchanged) | #50 | Planned |
| Questionnaire content | 13:02–15:17 | Remove confusing questions ("форматы", "минимум шагов") | Review and trim questionnaire content | #50 | Planned |
| Custom input | 11:27 | Limit custom input (~100 chars) | Add max-length validation | #50 | Planned |
| Typography | 00:11–00:22 | Headings should be bolder (Montserrat bold) | Batch into design overhaul | #50 | Deferred |
| Element sizing | 07:25–09:19 | Make icons/buttons/blocks smaller, more square | Batch into design overhaul | #50 | Deferred |
| Layout & margins | 03:45–05:10 | Respect margins; don't stretch text full width; remove dashed line; add light accent | Batch into design overhaul | #50 | Deferred |
| Step alignment | 00:50–01:35 | Center sun icons; equal spacing between steps | Batch into design overhaul | #50 | Deferred |
| Brightness & logo | 01:36–06:59 | Lighten main block/contour; adjust logo placement | Batch into design overhaul | #50 | Deferred |
| Test outputs | 17:32–18:20 | Team should run tests and send results to the customer | Prepare and share test runs | #47 | In progress |

## Rationale for deferred design work

This sprint prioritized the customer's top two gaps — a connected backend and real
filtering — plus deployment and architecture hardening. The detailed visual feedback
is grouped into a single backlog item (#50) so the redesign can be applied
consistently across all screens, aligned with the designer's mockups, in the next
sprint rather than piecemeal.

## Roadmap impact

- MVP v2 (this increment): frontend↔backend integration, real recommendations,
  deployment.
- Next increment: design overhaul per designer mockups, questionnaire content
  cleanup, budget label rename, custom input limit, product image strategy.

## Summary

The MVP v1 review produced actionable feedback for both the current increment and
future work. The strongest accepted progress is the connected backend and real
recommendation data (the customer's #1 requested gap), while detailed design
feedback is tracked as a prioritized backlog item for the next sprint.