# Week 6 Report — KOYASH

**Project:** KOYASH, an explainable skincare recommendation service<br>
**Team:** Sunwise (#12) · **Assignment:** 6 · **Sprint:** 4<br>
**Trial release:** [v0.4.0](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v0.4.0)<br>
**Customer review outcome:** `Ready for guided trial` · `Accepted with follow-up items`

## Sprint 4 at a glance

| Item | Evidence |
|---|---|
| Sprint Goal | Deliver a stable Week 6 trial of the integrated product, let the customer execute the trial, run UAT and the Sprint Review, prepare customer-facing documentation, and assess transition readiness before the final MVP v3. |
| Dates | 6–12 July 2026 |
| Product Backlog | [GitLab board](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/boards) |
| Sprint Backlog | [Sprint 4 issues](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/?milestone_title=Sprint%204) |
| Milestone | [Sprint 4](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/milestones/4) — 10 completed items |
| Story Points | Not estimated. This is recorded as a process deviation; no estimate was fabricated after delivery. |

Sprint 4 produced a stable, deployed trial increment. The customer interacted with the
live questionnaire and recommendation flow in a facilitated session, approved the
design direction with minor edits, and converted the remaining product and transition
gaps into a small, inspectable Sprint 5 scope.

## Trial release changes

- Integrated questionnaire → recommendation → account/history flow demonstrated against
  the live backend.
- Per-product budget filtering clarified and prepared for customer validation (#61).
- Questionnaire reduced after the customer identified unnecessary friction.
- Same-category replacement defect identified and isolated for correction (#62).
- Approved visual direction and explicit morning/evening routine labeling tracked in #50.
- Customer-facing entry point, handover, roadmap, UAT, changelog, release notes, CI, and
  report artifacts completed through issues #51–#60.

## Product and documentation access

- **Week 6 trial:** [http://10.93.26.208:8080/](http://10.93.26.208:8080/)
- **Run and access instructions:** [root README](../../README.md#run-the-full-stack)
- **Hosted documentation:** [KOYASH documentation site](https://s-anisimov.gitlab.pg.innopolis.university/sunwise-koyash/)
- [README](../../README.md) · [CONTRIBUTING](../../CONTRIBUTING.md) · [AGENTS](../../AGENTS.md)
- [Customer handover](../../docs/customer-handover.md) · [Roadmap](../../docs/roadmap.md)
- [Architecture and ADRs](../../docs/architecture/README.md)
- [Quality requirements](../../docs/quality-requirements.md) · [Testing](../../docs/testing.md)
- [Development process](../../docs/development-process.md) · [UAT](../../docs/user-acceptance-tests.md)

## Customer-facing documentation review

| Finding | Week 6 conclusion | Response |
|---|---|---|
| Clear | The deployed entry point and main questionnaire flow were understandable in the facilitated trial. | Keep one prominent product URL and concise run instructions. |
| Clear | The README was suitable as the repository entry point for the trial. | Maintained through #51 and linked to handover guidance. |
| Unclear | The difference between the trial build and the final independent-use state needed to be explicit. | Handover level recorded as `Ready for guided trial`; Week 7 conditions documented. |
| Missing | Final owner-side repository/secrets transfer could not happen before the defense. | Secure post-defense transfer tracked in #64; no secret is committed. |
| Missing | Filtering samples, replacement constraints, and the final explanation policy needed customer validation. | Converted to #61–#63 with acceptance criteria and tests. |

The review covered the README, access and Docker deployment instructions, handover,
configuration/secrets baseline, troubleshooting expectations, and known limitations.
The maintained [customer handover](../../docs/customer-handover.md) is the authoritative
operational document.

## Trial, UAT, and transition readiness

The customer used the trial with team facilitation. UAT-01–UAT-05 covered the landing,
questionnaire, recommendation, account/history, feedback, and replacement flow. UAT-06
defined the per-product budget check and UAT-07 captured the independent-use target.
The live session found no release-blocking failure, but independent use was intentionally
deferred until the redesigned frontend and Week 6 follow-ups were complete.

**Week 6 state:** `Ready for guided trial` and `Accepted with follow-up items`.

**Required for Week 7:** validate the budget rule on customer samples, enforce
same-category replacement, ship the approved redesign, finish the explanation prompt
evaluation, and prepare the repository/secrets handover.

## Customer feedback → Sprint 5 work

| Customer feedback | Decision | Issue | Week 6 state |
|---|---|---|---|
| Apply the approved mockups consistently | Ship the redesign and morning/evening routine structure | [#50](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/50) | Planned |
| Budget must constrain every recommended product | Validate samples and enforce a hard per-product cap | [#61](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/61) | Pending validation |
| A cleansing gel must not replace a cream | Restrict alternatives to the same category and add tests | [#62](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/62) | Planned |
| Explanations must stay clear and trustworthy | Finalize the prompt and evaluate it with the customer | [#63](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/63) | Planned |
| Customer takes over repository/deployment after defense | Prepare secure ownership and secrets transfer | [#64](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/64) | Planned |

These items were not hidden or described as complete in Week 6: they were the explicit
maintenance and transition scope for Sprint 5.

## Release and review evidence

- [Week 6 SemVer trial release v0.4.0](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v0.4.0)
- [CHANGELOG](../../CHANGELOG.md) · [release notes](release-notes.md)
- [Sprint Review summary](sprint-review-summary.md)
- [Detailed Sprint Review notes](sprint-review-notes.md); the identifying recording and
  exact timecodes are shared only through the private Moodle wrapper.
- [Customer feedback traceability](customer-feedback-traceability.md)
- [Reflection](reflection.md) · [Retrospective](retrospective.md) · [LLM usage](llm-report.md)

## Contribution traceability

| Member | Sprint 4 evidence | Review / verification | Primary contribution |
|---|---|---|---|
| Sergei Anisimov (`s.anisimov`) | #57–#60; [MR !80](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/80) | Backend tests, CI, VM deployment and release verification | Backend release candidate and deployed trial |
| Dmitrii Shestakov (`d.shestakov`) | #50 and frontend trial work in #60 | Design/customer-flow verification | Frontend integration and approved-design preparation |
| Anfisa Shestakova (`a.shestakova`) | Design work supporting #50 | Visual review with Dmitrii | Customer-facing UI direction and mockup review |
| Roman Korotkov (`r.korotkov`) | #51–#56; [MR !77](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/77) | Cross-review and release-note verification | UAT, changelog, release documentation |
| Radmir Iakupov (`r.iakupov`) | #51–#54; [MR !76](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/76) | Reviewed report and handover artifacts | Week 6 report, handover and transition evidence |

All five team members participated. The repository history and reviewed MRs remain the
source of truth where responsibility overlaps.

## Inspectable screenshots

![Sprint 4 milestone with completed work](images/sprint4-milestone.png)

![Week 6 trial release v0.4.0](images/trial-release.png)

![Reviewed issue-linked Week 6 merge request](images/reviewed-mr.png)

## Product status after Week 6

The v0.4.0 trial was stable and accessible, the design direction was settled, and the
remaining gaps were traceable. The final independent-use level had not yet been claimed.
Sprint 5 closed the trial feedback, transitioned the product, and released MVP v3; see
the [Week 7 submission index](../week7/README.md).
