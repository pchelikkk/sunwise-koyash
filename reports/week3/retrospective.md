# Sprint 1 Retrospective

This retrospective is public and sanitized. No sensitive personal information or private conflict details are included.

## What Went Well

1. **Clear role split:** Dividing responsibilities between design, backend, and documentation kept work parallel and reduced blockers.
2. **Early risk identification:** Flagging US-05 (rule-based recommendations) as the highest-risk item in Sprint Planning allowed the team to start dataset inspection early and avoid a last-minute surprise.
3. **Story splitting:** Splitting large stories (US-02 → US-02 + US-14, US-07 → US-07 + US-15) made Sprint items smaller and easier to review independently.
4. **Customer feedback loop:** The team completed a live Sprint Review with the customer and received direct feedback on MVP v1 functionality and design direction.
5. **Design direction validation:** The customer approved the palette, gradient, and light background direction, which reduced uncertainty for the next design iteration.

## What Did Not Go Well

1. **Dataset field gaps:** The real product dataset did not cover all filtering fields needed for US-05, requiring unplanned mapping work during the Sprint.
2. **Sprint Review scheduling:** The customer Sprint Review was scheduled close to the end of the Sprint window, reducing buffer time for implementing requested changes.
3. **Issue tracker setup delay:** Issue templates and the MR template were set up later in the Sprint than planned, which meant early MRs had less structured review evidence.
4. **MVP/design divergence:** The working MVP and the future design prototype developed in parallel, so some feedback had to be captured as follow-up design tasks rather than immediate implementation.

## Action Points

1. **Schedule customer touchpoints at Sprint start** — book the Sprint Review meeting on day 1 of the next Sprint to ensure buffer time for follow-up changes.
2. **Complete issue and MR templates before first commit** — treat repository workflow setup as a Sprint 0 prerequisite or the first Course Task of each Sprint.
3. **Create design feedback issues immediately after reviews** — every accepted customer comment should become either a backlog item, a design task, or a documented decision.
4. **Inspect dataset fields before writing final filtering rules** — avoid writing recommendation logic for fields that are missing or inconsistent in real data.
5. **Keep documentation and implementation synchronized** — update backlog, roadmap, customer-review evidence, and release notes as soon as implementation status changes.
