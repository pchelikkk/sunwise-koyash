# Reflection — Week 7

Project: KOYASH
Team: Sunwise
Assignment: 6
Sprint: 5
Release: v1.0.0

## Sprint goal

Deliver the final MVP v3, complete the customer transition, publish the `v1.0.0`
release, and prepare the Demo Day materials.

## Lessons learned

### From problems we faced

- The external design mockups turned out to be less functional than the product
  needed, so the team built a more functional custom frontend and validated it with
  the customer. Lesson: check design feasibility against real flows before committing.
- A replacement-category defect (a gel offered for a cream) reached the Week 6 session.
  Encoding the domain constraint as an explicit in-category rule with tests, and
  returning exactly the available number of alternatives, resolved it. Lesson: turn
  domain rules into explicit, tested logic.

### From decisions that worked

- Keeping a deterministic recommendation engine and letting the LLM only reword
  explanations kept the product predictable and safe.
- Multi-source price parsing reached about 90%+ coverage and satisfied the customer.
- Splitting the work into small, cross-reviewed merge requests kept quality high and
  made the final delivery auditable.

## What we would do differently

- Freeze the design direction earlier and avoid depending on mockups that may not fit
  the interaction flow.
- Stand up the customer-facing deployment earlier so independent use is testable sooner.

## Outcome

The customer accepted the product as final and confirmed the team is ready for the
defense. MVP v3 is released as `v1.0.0` and deployed on the university VM.
