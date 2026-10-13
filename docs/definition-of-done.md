# Definition of Done

A Product Backlog Item may be marked **Done** only when all criteria below are satisfied.

## All PBIs

- [ ] All acceptance criteria defined in the issue are verified.
- [ ] Code or documentation change is reviewed and approved by a team member who is not the author.
- [ ] Merge request is linked to the issue and merged into the default branch.
- [ ] No known blocking bugs are introduced by this change.
- [ ] `CHANGELOG.md` is updated for every user-visible change.
- [ ] Issue Work Status is updated to **Done** in the tracker.
- [ ] Issue is linked to the current sprint milestone.

## Frontend PBIs

- [ ] UI matches the agreed design direction or documented customer feedback.
- [ ] Manually tested in at least one browser.
- [ ] No console errors on the tested flow.
- [ ] Responsive layout verified for mobile and desktop when the affected UI is visible on both.
- [ ] Screenshots or short notes are added to the MR if the change is visual.

## Backend PBIs

- [ ] API endpoint returns the correct response schema.
- [ ] Hard exclusion rules are verified with seeded test data when relevant.
- [ ] Endpoint is accessible and documented in the API contract or README when relevant.
- [ ] Automated tests cover new or changed behavior, and CI passes.

## User Stories

- [ ] All linked supporting PBIs are marked Done.
- [ ] Acceptance criteria are verified manually or via automated test.
- [ ] Verification evidence is recorded in the MR description or QA checklist.
- [ ] Customer review feedback is considered when the story affects the user experience.

## Documentation PBIs

- [ ] Document is written in English.
- [ ] Document contains no private personal data, secrets, or confidential information.
- [ ] Links are relative where possible, or point to approved public course artifacts.
- [ ] The document is reviewed by another team member before merge.

## Sprint 3 / Assignment 5 quality gates

A work item is considered done only if:

- the work item is linked to a GitLab issue;
- changes are submitted through a merge request;
- the merge request has at least one review/approval from a non-author;
- relevant documentation is updated;
- tests or quality checks are added or updated where applicable;
- CI passes on the merge request or default branch;
- quality requirements are considered for user-facing changes;
- UAT impact is considered for user-facing changes;
- customer feedback is linked to follow-up work when relevant;
- release notes or the Week 5 report links are updated if the change affects the submitted increment;
- no private customer recording or sensitive information is committed to the public repository.

## Review checklist

Before merging, reviewers should check:

- the linked issue and its acceptance criteria;
- the changed files;
- consistency with the current MVP scope;
- documentation links;
- testing/CI impact;
- customer validation or UAT impact.