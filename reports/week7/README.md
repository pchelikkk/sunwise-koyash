# Week 7 Report — KOYASH

**Project:** KOYASH, an explainable skincare recommendation service<br>
**Team:** Sunwise (#12) · **Assignment:** 6 · **Sprint:** 5<br>
**Final release:** [v1.0.1 — MVP v3 patch](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v1.0.1)<br>
**Transition outcome:** `Ready for independent use` · `Accepted with follow-up items`

This is the final Assignment 6 public submission index. The [Week 6 report](../week6/README.md)
contains the trial-release and transition-readiness evidence; this report focuses on
Sprint 5 maintenance, final delivery, and transition.

## Sprint 5 at a glance

| Item | Evidence |
|---|---|
| Sprint Goal | Deliver MVP v3 by applying the approved redesign and customer-trial follow-ups, fixing the remaining recommendation issues, completing transition documentation, publishing the final release, and preparing Demo Day. |
| Dates | 13–19 July 2026 |
| Product Backlog | [GitLab board](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/boards) |
| Sprint Backlog | [Sprint 5 issues](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/?milestone_title=Sprint%205) |
| Milestone | [Sprint 5](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/milestones/5) — 15 completed items |
| Story Points | Not estimated. This is recorded as a process deviation; no estimate was fabricated after delivery. |

## Week 7 maintenance and final MVP v3

- Shipped the approved responsive product experience and simplified the concept around
  a ready routine (#50, #65).
- Displayed the guided skin-diagnosis result and preserved a guest routine after sign-in
  (#66, #67).
- Enforced hard per-product budget caps and same-category replacement with automated
  regression coverage (#61, #62).
- Integrated the customer-authored explanation prompt. The LLM only rephrases facts
  selected by the deterministic engine; runtime policy checks and fallback protect the
  product boundary (#63).
- Kept the protected administrator workspace as a first-class surface for analytics,
  feedback, replacements, product quality, and controlled catalog import.
- Published v1.0.0 and the audited [v1.0.1 patch](release-notes-v1.0.1.md), then verified
  the university VM deployment.

## Product and maintained documentation

- **Final product:** [http://10.93.26.208:8080/](http://10.93.26.208:8080/)
- **Run and access instructions:** [root README](../../README.md#run-the-full-stack)
- **Hosted documentation:** [KOYASH documentation site](https://s-anisimov.gitlab.pg.innopolis.university/sunwise-koyash/)
- [README](../../README.md) · [CONTRIBUTING](../../CONTRIBUTING.md) · [AGENTS](../../AGENTS.md)
- [Customer handover](../../docs/customer-handover.md) · [Roadmap](../../docs/roadmap.md)
- [Architecture and ADRs](../../docs/architecture/README.md)
- [Quality requirements](../../docs/quality-requirements.md) · [Testing](../../docs/testing.md)
- [Development process](../../docs/development-process.md) · [UAT](../../docs/user-acceptance-tests.md)

## Final transition outcome

**Handover level:** `Ready for independent use`. The customer can complete the public
questionnaire and recommendation journey without team facilitation on the deployed VM.

**Customer confirmation:** `Accepted with follow-up items`. The customer accepted the
product as final and confirmed the team was ready for the defense. The administrator
analytics panel was identified as a strong differentiator and a priority for the demo.

Made available during transition:

- deployed React + FastAPI + MongoDB stack on the university VM;
- current run, health-check, Docker, recovery, and verification instructions;
- configuration templates and a secrets-handling baseline with no production secret in
  the repository;
- maintained product, architecture, testing, UAT, contributor, agent, and handover docs;
- a secure post-defense plan for repository ownership, production secrets, and database
  access.

The remaining follow-up is the owner-side repository and secrets transfer (#64). It is
external to the functional MVP v3 and intentionally uses a secure channel. Until that
transfer, the university VM remains the accepted evaluation and independent-use access
point. The full scope and support expectations are in the
[customer handover](../../docs/customer-handover.md).

## Customer feedback response

| Customer feedback | Delivered response | Issue | Result |
|---|---|---|---|
| Public catalog/favorites make KOYASH look like a shop | Removed them from the primary product concept | [#65](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/65) | Done |
| Show the detected skin type | Added the resolved profile to the result | [#66](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/66) | Done |
| Preserve a guest cosmetic bag after authentication | Migrated the current routine on sign-in/registration | [#67](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/67) | Done |
| Budget must constrain every product | Enforced a hard per-product price cap | [#61](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/61) | Done |
| Replacements must stay in category | Return only genuinely available same-category alternatives | [#62](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/62) | Done |
| Explanations must stay factual and safe | Integrated customer prompt, policy checks, and deterministic fallback | [#63](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/63) | Done |
| Support one-action admin dataset updates | Kept protected validated CSV/XLSX catalog import | [customer review summary](customer-review-summary.md) | Done |
| Transfer ownership after the defense | Prepared secure repository/secrets handover | [#64](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues/64) | Follow-up prepared |

The detailed chain from customer statement to implementation and evidence is in
[customer feedback traceability](customer-feedback-traceability.md). The customer-review
sample contract is preserved in
[koyash-cosmetic-bags-samples.json](../../docs/customer-review/koyash-cosmetic-bags-samples.json).

## UAT and independent-use evidence

| ID | Customer-critical scenario | Result |
|---|---|---|
| UAT-01–04 | Landing, questionnaire, recommendation, account/history | Passed |
| UAT-05 | Product feedback and in-category replacement | Passed |
| UAT-06 | Per-product budget filtering | Passed; validated with customer context |
| UAT-07 | Independent use without team facilitation | Passed |
| UAT-08 | Detected skin type shown in the result | Passed |
| UAT-09 | Guest routine preserved after authentication | Passed |

The complete steps, expected results, and execution record are maintained in
[user acceptance tests](../../docs/user-acceptance-tests.md). No open functional blocker
remained for the released MVP v3.

## Release, review, and Demo Day evidence

- [Final SemVer release v1.0.1](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v1.0.1)
- [CHANGELOG](../../CHANGELOG.md) · [v1.0.1 patch notes](release-notes-v1.0.1.md)
- [Public sanitized demo video](https://drive.google.com/drive/folders/1oT0mSEMmlGJWGsdO9V_DbxgnTE3d6uI0?usp=drive_link)
- [Sprint Review summary](sprint-review-summary.md)
- [Detailed Sprint Review notes](sprint-review-notes.md); the identifying recording and
  exact timecodes are shared only through the private Moodle wrapper.
- [Reflection](reflection.md) · [Retrospective](retrospective.md) · [LLM usage](llm-report.md)

Demo Day preparation used the required narrative: context, final requirements and MVP
roadmap, a sub-two-minute product demonstration, transition status, engineering and
quality evidence, team contribution, reflection, and product/repository links. The
Week 7 rehearsal preparation was completed with a timed speaking plan assigning at
least one slide to every team member.

## Reviewed delivery chain

| Merge request | Purpose | Outcome |
|---|---|---|
| [!90](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/90) | Week 7 documentation and transition evidence | Merged into protected `main` |
| [!91](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/91) | Final MVP v3 release v1.0.0 | Merged into protected `main` |
| [!92](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/92) | Customer LLM prompt and Demo Day evidence | Merged into protected `main` |
| [!93](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/93) | Audited v1.0.1 patch release | Reviewed by Roman Korotkov; pipeline passed; merged into `main` |

## Contribution traceability

| Member | Issues / MR evidence | Review and verification | Sprint 5 contribution | Demo Day preparation |
|---|---|---|---|---|
| Sergei Anisimov (`s.anisimov`) | #61, #62, #63, #67, #72; backend/final patch work represented in !92–!93 | Frontend/release review, backend tests, VM verification | Backend and frontend fixes, guarded LLM integration, deployment and patch release | Technical narrative and product verification |
| Dmitrii Shestakov (`d.shestakov`) | #50, #65, #66, #73 | Reviewed documentation/customer-flow changes | Frontend redesign and trial follow-ups | Demo flow preparation |
| Anfisa Shestakova (`a.shestakova`) | #66 and design work supporting #50 | Visual design review | Skin-type UI and final visual direction with Dmitrii | Slide visuals |
| Roman Korotkov (`r.korotkov`) | #70, #72, #73; release review in !91 and !93 | Cross-review, release and acceptance evidence verification | Changelog, releases, UAT/transition coordination | Presentation coordination |
| Radmir Iakupov (`r.iakupov`) | #64, #68, #69, #71, #74; [!90](https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/90) | Documentation and backend cross-review | Week 7 report set, handover, UAT, customer evidence | Deck structure and rehearsal plan |

All five team members participated. The issue and MR histories are authoritative where
implementation, review, and release responsibilities overlap.

## Inspectable screenshots

![Sprint 5 milestone](images/sprint5-milestone.png)

![Final release v1.0.1](images/final-release.png)

![Deployed MVP v3 on the university VM](images/deploy-vm.png)

![Reviewed issue-linked merge request](images/reviewed-mr.png)

![Protected administrator analytics dashboard](images/admin-dashboard.png)

## Final product status

KOYASH MVP v3 is complete, deployed, and released as v1.0.1 from protected `main`.
The maintained handover, quality, architecture, testing, UAT, and contribution evidence
are linked above. The current transition level is `Ready for independent use`; the
accepted post-defense ownership/secrets transfer remains the only follow-up action.
