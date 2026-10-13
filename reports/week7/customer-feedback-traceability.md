# Week 7 customer feedback traceability

Source: customer review recording and transcript, 17 July 2026, 00:00–30:45.

The customer accepted the demonstrated product with the refinements below and
said the team was ready for submission. This table separates requested product
changes from handover actions that require an external account decision.

| Time | Customer decision or request | Implementation | Verification | PBI / action | Status |
| --- | --- | --- | --- | --- | --- |
| 01:58 | Show the detected skin type after the guided diagnostic | The questionnaire calls the deterministic skin-diagnosis endpoint after the final diagnostic answer and shows type, confidence and evidence before concerns | Playwright desktop/mobile diagnostic scenario; backend skin-diagnosis tests | #66 | Complete |
| 06:21–08:16 | Provide the exact post-filtering JSON so the prompt can be reviewed against machine output | Eight controlled recommendation scenarios include input, filter summary, score breakdown, routine, dataset provenance and the exact LLM context | JSON validator; all products verified against `source=dataset` | #63 | Complete |
| 08:21 | Count a product used both morning and evening only once in the total | Existing recommendation contract keeps the schedule in both routines and calculates the basket from unique products | Recommendation and export validator suites | #61 | Complete |
| 08:43–10:36 | Return only genuinely suitable replacements and replace the selected item in the routine and price | Existing same-step thresholded replacement flow retained; the old item is removed from both routine sections and the new total is persisted | Playwright replacement regression test; backend replacement tests | #62 | Complete |
| 13:33–14:58 | Remove public catalog and favorites because KOYASH is a selection service, not a store | Catalog, favorites and cosmetic-bag shopping navigation removed from the public product journey; obsolete hashes redirect home | Playwright public-navigation regression tests | #65 | Complete |
| 15:53–17:23 | Let a guest save the finished routine when creating or entering an account | Result page offers “Войти и сохранить”; registration/login claims only unowned recommendations created by the same anonymous browser | Backend ownership/isolation tests; Playwright guest result scenario | #67 | Complete |
| 17:51–20:33 | Keep the analytics-heavy admin area and show it at Demo Day | Dashboard retained as a protected admin-only surface with usage funnel, audience, feedback, replacements and catalog quality/editor views | Admin API and Playwright dashboard tests | Demo Day action | Complete |
| 20:38–21:38 | Import a future 200–300 product dataset in one action, with fallbacks for incomplete enrichment | Protected CSV/XLSX import validates the whole file before writes, upserts products, optionally deactivates missing rows, records an audit event and becomes the restart-safe source of truth | Backend import, validation, audit and restart-preservation tests; Playwright admin import scenario | #64 handover support | Complete |
| 23:51 | Move the repository from GitLab to GitHub and send the customer the link | No external repository was created automatically because the destination owner/name and access policy were not specified | Requires team/customer account decision | #64 | External handover action |
| 26:28 | University-only deployment is sufficient for Demo Day | No infrastructure expansion required by this review | Customer acceptance in recording | Deployment constraint | Accepted |

## Product boundary confirmed by the review

KOYASH solves one primary job: collect a short skin profile and return a ready,
explainable routine. It is not a marketplace. Store links remain attached to
selected products only as a handoff after the recommendation, while product
selection, safety exclusions and replacement ranking stay deterministic.

## Positive feedback and remaining transition action

- The customer highlighted the protected admin analytics as a Demo Day strength.
- Corrected replacement behavior and the multi-source pricing approach were accepted.
- The university VM is sufficient for Demo Day.
- Repository migration and ownership transfer remain a post-defense external action
  under #64; they require the customer-side destination and access decision.
