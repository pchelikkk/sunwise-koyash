# Sprint Review Notes — Week 7

Project: KOYASH
Team: Sunwise
Assignment: 6
Sprint: 5
Release: v1.0.0
Customer: Diana

## Session

- Type: final Sprint Review + UAT + transition confirmation.
- Attendees: the customer (Diana) and the Sunwise team.
- Format: the team demonstrated the final MVP v3; the customer reviewed the product and
  confirmed acceptance.
- Recording: kept private and shared with instructors via Moodle. The key conclusions
  are summarized below; the transcript is not published in the repository.

## Agenda

1. Final product walkthrough (questionnaire, recommendation, replacement, admin panel).
2. Confirmation of the Week 6 follow-ups.
3. Budget filtering and replacement validation.
4. Explanation quality and the LLM prompt.
5. Transition, acceptance, and handover.

## Notes

### Product walkthrough

- The team demonstrated the full flow: guided questionnaire with age validation and
  adaptive branching, budget filtering, full/basic routine, per-product replacement
  with a reason, sharing the cosmetic bag, and registration with history.
- The admin analytics panel was demonstrated (completed selections, unique visitors
  over 7/30/90-day periods, feedback reasons, and product management). The customer
  asked for it to be shown during the demo.

### Follow-ups from the Week 6 trial

- The product catalog and favorites were removed as out of concept.
- The detected skin type is now shown after the questionnaire.
- Guests can save their cosmetic bag by signing in.

### Budget filtering and replacement

- Per-product budget filtering was validated.
- The replacement logic was corrected: replacements stay in the same category and
  return exactly the number of genuinely available alternatives, with no filler item.

### Explanations / LLM

- Explanation quality was accepted. The in-product LLM layer stays disabled by default
  and only rewords the deterministic explanations.
- The team supplied the requested filtration JSON and integrated the customer-authored
  prompt for `gpt-4o-mini`. The prompt receives exact `matched_concerns`; runtime
  validation rejects ungrounded or unsafe text and falls back deterministically.

### Transition and acceptance

- The customer accepted the product as final and stated the team is ready for the
  defense.
- Handover level: `Ready for independent use` (deployed on the university VM).
- Written acceptance was provided by the customer and is kept private (Moodle).
- Repository ownership and production secrets are handed over after the defense over a
  secure channel (#64).

## UAT outcome

| ID | Scenario | Result |
|---|---|---|
| UAT-01 | Open MVP and understand the landing page | Passed |
| UAT-02 | Complete the questionnaire and reach the result | Passed |
| UAT-03 | Review reasoning and product feedback | Passed |
| UAT-04 | Account, login, and recommendation history | Passed |
| UAT-05 | Product feedback and replacement | Passed |
| UAT-06 | Per-product budget filtering | Passed (validated by the customer) |
| UAT-07 | Independent (unfacilitated) use | Passed |
| UAT-08 | Detected skin type shown on the result | Passed |
| UAT-09 | Guest bag preserved after sign-in | Passed |

## Decisions and action items

- Publish `v1.0.0`; keep the VM as the access point.
- Record the public demo video (#73); prepare the Demo Day deck and rehearsal (#74).
- Keep the integrated prompt and filtration-sample contract verified (#63).
- Complete the repository and secrets handover after the defense (#64).
