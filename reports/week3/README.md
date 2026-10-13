# Week 3 Report Index — Assignment 3

Project: **KOYASH**  
Team: **Sunwise (#12)**  
Repository: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash  
Figma prototype: https://www.figma.com/design/uxpVsoAX3HJROk0zSwKtG6/KOYASH-Prototype?node-id=0-1&t=vWmeQJ2OQlrMgiJ0-1

## 1. Project Summary

KOYASH is a web service for personalized skincare product recommendations. During Week 3, the team migrated user stories to GitLab issues, refined the Product Backlog, planned Sprint 1, prepared MVP v1 evidence, conducted a live customer review, created release `v0.1.0`, and documented the workflow through issue-linked merge requests.

License: [`../../LICENSE`](../../LICENSE)

## 2. Main Assignment 3 Links

| Artifact | Link |
|---|---|
| Repository | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash |
| Product Backlog view / all issues | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues?sort=created_date&state=all&first_page_size=100 |
| Sprint Backlog view / Sprint 1 issues | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues?sort=created_date&state=all&milestone_title=Sprint%201&first_page_size=100 |
| Sprint 1 milestone | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/milestones/1#tab-issues |
| MVP v1 filtered issues | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues?sort=created_date&state=all&label_name%5B%5D=mvp-v1&first_page_size=100 |
| Release `v0.1.0` | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v0.1.0 |
| Merged merge requests | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/?sort=created_date&state=merged&first_page_size=100 |
| Reviewed MR example | https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/21 |
| Demo video | https://drive.google.com/file/d/1xBSr558yg7xa-UMlsDiCpv1aRSThXUWV/view?usp=sharing |
| Customer review recording for private instructor assessment | https://drive.google.com/file/d/120FtRVPTmhgf-jCLWQXhfQFFRmXlhBRo/view?usp=sharing |

## 3. Repository Documents

| Requirement area | Evidence |
|---|---|
| Historical Week 2 user stories | [`../week2/user-stories.md`](../week2/user-stories.md) |
| Current user story index | [`../../docs/user-stories.md`](../../docs/user-stories.md) |
| Product Roadmap | [`../../docs/roadmap.md`](../../docs/roadmap.md) |
| Definition of Done | [`../../docs/definition-of-done.md`](../../docs/definition-of-done.md) |
| Customer Review Transcript | [`customer-review-transcript.md`](customer-review-transcript.md) |
| Customer Review Summary | [`customer-review-summary.md`](customer-review-summary.md) |
| Sprint Retrospective | [`retrospective.md`](retrospective.md) |
| Week 3 Reflection | [`reflection.md`](reflection.md) |
| LLM Usage Report | [`llm-report.md`](llm-report.md) |
| Design Feedback Evidence | [`design-feedback.md`](design-feedback.md) |
| Design Action Plan | [`design-action-plan.md`](design-action-plan.md) |
| Contrast Check | [`contrast-check.md`](contrast-check.md) |
| Backend Smoke Check | [`backend-smoke-check.md`](backend-smoke-check.md) |
| Changelog | [`../../CHANGELOG.md`](../../CHANGELOG.md) |
| MR Template | [`../../.gitlab/merge_request_templates/default.md`](../../.gitlab/merge_request_templates/default.md) |
| Issue Templates | [`../../.gitlab/issue_templates/`](../../.gitlab/issue_templates/) |

## 4. Product Backlog and Sprint Scope

The current Product Backlog is maintained through GitLab issues and indexed in [`../../docs/user-stories.md`](../../docs/user-stories.md).

Sprint 1 / MVP v1 contains the following user stories:

- US-01 Landing page trust
- US-02 Step-by-step questionnaire
- US-03 Budget selection
- US-04 Allergen constraints
- US-05 Rule-based recommendations
- US-06 Personal cosmetic bag / routine
- US-07 Product explanations
- US-14 Why-we-ask explanations
- US-15 Explanation-first cards

Total Sprint 1 estimate: **44 Story Points**.

Sprint 2 candidates:

- US-08 Product and consultation links
- US-09 Feedback on product
- US-10 View previous recommendations

Removed or excluded items remain listed in the user story index for traceability.

## 5. MVP v1 Access

MVP v1 is provided as a **local runnable artifact** in the repository. It is **not publicly deployed**.

To open the local prototype:

1. Clone or download the repository.
2. Open the following file in a browser:

​
docs/prototype/index.html

This local HTML artifact is the main MVP v1 access point for Assignment 3 evaluation.

The repository also contains the Docker-based technical foundation. If the reviewer wants to run the technical setup:

​
docker compose up -d --build

Frontend:

​
http://localhost:5173

Backend health endpoint:

​
http://localhost:8000/health

API documentation, if enabled:

​
http://localhost:8000/docs

## 6. Customer Review Result

A live Sprint Review was conducted with the customer, Diana. Recording permission was requested and granted before recording started.

The customer reviewed the MVP v1 direction and design prototype. Main feedback:

- continue with the approved palette, gradient, and light background;
- improve landing composition and move top elements lower;
- simplify the logo;
- check contrast and readability;
- avoid generic AI-template visual style;
- add a memorable hook or anchor;
- process comments on user stories.

Detailed evidence:

- [`customer-review-transcript.md`](customer-review-transcript.md)
- [`customer-review-summary.md`](customer-review-summary.md)

## 7. Release

The MVP v1 release is published as:

​
v0.1.0

Release link:

https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/releases/v0.1.0

The release is mapped to MVP v1 / Sprint 1 and includes the selected MVP v1 user stories.

Changelog:

[`../../CHANGELOG.md`](../../CHANGELOG.md)

## 8. Workflow Evidence

The team used GitLab issues, issue-linked branches, merge requests, reviews, approvals, and merge commits.

Evidence:

- Merged MRs: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/?sort=created_date&state=merged&first_page_size=100
- Reviewed MR example: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/21
- Product Backlog view: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues?sort=created_date&state=all&first_page_size=100
- Sprint Backlog view: https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/issues?sort=created_date&state=all&milestone_title=Sprint%201&first_page_size=100

## 9. Contribution Traceability

| Team member | Main contribution | Evidence |
|---|---|---|
| Sergei Anisimov | Backend / repository / smoke-check evidence / release support | Issue-linked MR and review activity in GitLab |
| Radmir Iakupov | Documentation updates, README/run instructions, Week 3 report support | Issue-linked MR and review activity in GitLab |
| Roman Korotkov | Sprint documentation, user story index, Week 3 documentation | Issue-linked MR and review activity in GitLab |
| Dmitrii Shestakov | Design implementation / landing layout feedback / review activity | Issue-linked MR and review activity in GitLab |
| Anfisa Shestakova | Design evidence, contrast/readability check, visual QA | Issue-linked MR and review activity in GitLab |

Full evidence is available in the merged merge requests list:

https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash/-/merge_requests/?sort=created_date&state=merged&first_page_size=100

## 10. Screenshots

Screenshots are stored in [`images/`](images/).

Expected evidence screenshots:

![Product Backlog view](images/product-backlog-view.png)

![Sprint Backlog view](images/sprint-backlog-view.png)

![Sprint 1 milestone](images/sprint-1-milestone.png)

![MVP v1 filtered view](images/mvp-v1-filtered-view.png)

![Release v0.1.0](images/release-v0.1.0.png)

![MVP v1 demo](images/mvp-v1-demo.png)

![Reviewed merge request](images/reviewed-merge-request.png)

If screenshot filenames differ, the repository filenames should be renamed or the links above should be updated before submission.

## 11. Current Product Status

MVP v1 is completed as a local prototype/artifact and release `v0.1.0` is created for Assignment 3. The customer accepted the overall direction and gave design-focused improvement points for the next iteration.

The main remaining product risks are:

- product dataset field coverage;
- stronger visual identity / hook;
- contrast and readability polish;
- future product feedback and recommendation history features.

## 12. Next Steps

Planned next steps for Sprint 2:

- refine US-08 Product and consultation links;
- refine US-09 Feedback on product;
- refine US-10 View previous recommendations;
- improve product data mapping;
- continue design polish based on customer feedback;
- prepare more complete recommendation evidence after MVP v1.
