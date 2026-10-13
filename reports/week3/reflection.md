# Week 3 Reflection

## Learning Points

- **Product Backlog migration:** Migrating user stories from a document into issue-based tracking clarified ownership and made progress visible. Stable IDs (US-XXX) proved essential for traceability across artifacts.
- **Backlog refinement:** Splitting US-02 into US-02 + US-14 and US-07 into US-07 + US-15 made individual stories smaller and more actionable for Sprint planning.
- **Estimation:** Planning Poker highlighted that US-05 (rule-based recommendations, 13 SP) carries the highest risk due to uncertainty in the real product dataset structure.
- **Sprint Planning:** Defining a Sprint Goal first helped the team select only stories that contributed to a coherent user-facing slice rather than picking the easiest items.
- **MVP v1 delivery:** Dataset inspection for US-05 revealed field mapping gaps that had to be resolved before filtering rules could be finalized — confirming the identified main risk.
- **Workflow enforcement:** Issue-linked branches and MR reviews made accountability explicit and kept the codebase stable.
- **Customer review:** A live review with Diana clarified that the MVP v1 direction is acceptable and that the strongest short-term progress should happen in design polish.

## Validated Assumptions

- **Confirmed:** Hard exclusion constraints such as allergens must be applied before any ranking.
- **Confirmed:** One question per screen is the right UX pattern for the current questionnaire direction.
- **Confirmed:** The real product dataset does not fully cover all required fields out of the box; field mapping is necessary before stable rule implementation.
- **Confirmed:** The customer likes the light background, palette, and gradient direction used in MVP v1 and wants the team to continue developing it.
- **Confirmed:** The product should not look like a generic AI template; it needs a stronger visual or conceptual anchor.
- **Revised:** Initial estimate for US-06 was lower; routine layout required more frontend work than expected once the explanation payload was factored in.

## Friction and Gaps

- Real product data field coverage for skin type and concern matching is incomplete. A partial workaround is acceptable for MVP v1, while a fuller solution should be refined later.
- Design and implementation are not fully synchronized yet: the working MVP demonstrates functionality, while the design prototype shows the intended visual direction.
- US-10 (view previous recommendations) requires identity/history storage that was not feasible within Sprint 1 scope.
- Video demonstration still has to be recorded after final MVP v1 state is confirmed.
- Some design changes from customer review are follow-up tasks rather than completed changes.

## Planned Response

- Apply the most important customer feedback from Sprint Review: layout spacing, logo simplification, contrast check, and stronger visual anchor.
- Record and publish a sanitized video demonstration under two minutes.
- Tag SemVer release `v0.1.0` mapped to MVP v1 after final acceptance and merge.
- Open refinement issues for US-08, US-09, and US-10 ahead of Sprint 2 planning.
- Revisit product dataset field mapping and create a follow-up PBI for improved coverage in MVP v2.
- Keep design decisions traceable through issues, merge requests, and Week 3 report evidence.
