# Week 2 Report — KOYASH

## Project

**Project name:** KOYASH
**Team name:** Sunwise
**Repository:** https://gitlab.pg.innopolis.university/s.anisimov/sunwise-koyash.git

KOYASH is a web service for personalized skincare product recommendations. The MVP focuses on a rule-based recommendation flow based on questionnaire answers, budget, allergies/exclusions, and product database filtering.

## Repository setup

* License: [MIT License](../../LICENSE)
* Root README with local setup: [README](../../README.md)
* Merge request template: [.gitlab/merge_request_templates/default.md](../../.gitlab/merge_request_templates/default.md)
* GitLab CI configuration: [.gitlab-ci.yml](../../.gitlab-ci.yml)
* Lychee configuration: [lychee.toml](../../lychee.toml)
* Lychee ignored links: [.lycheeignore](../../.lycheeignore)

## User stories and MVP scope

* User stories, personas, MoSCoW priorities, and MVP v1 scope: [user-stories.md](user-stories.md)

Initial MVP v1 scope:

* US-01
* US-02
* US-03
* US-04
* US-05
* US-06
* US-07

## Prototype

* Figma prototype: https://www.figma.com/design/uxpVsoAX3HJROk0zSwKtG6/KOYASH-Prototype?node-id=0-1&t=vWmeQJ2OQlrMgiJ0-1
* Prototype screenshot: [images/prototype.png](images/prototype.png)

The prototype covers the main external user interface for the selected MVP v1 scope: landing page, questionnaire, budget selection, allergies/exclusions, answer summary, recommendation result, product details, and feedback.

## MVP v0

* MVP v0 report: [mvp-v0-report.md](mvp-v0-report.md)
* MVP v0 demo video: https://drive.google.com/file/d/1p6ZeusoUYIeFc3152ZiSlrldobR33cX-/view?usp=sharing

MVP v0 demonstrates the runnable technical foundation:

* React/Vite frontend;
* FastAPI backend;
* Docker Compose setup;
* backend health endpoint;
* sample products API;
* frontend-to-backend data flow.

Evidence screenshots:

* [MVP v0 frontend smoke check](images/mvp-v0-frontend.png)
* [Backend health endpoint](images/mvp-v0-health.jpg)
* [Sample products endpoint](images/mvp-v0-sample-products.png)

## Workflow evidence

* Reviewed merge request screenshot: [images/reviewed-mr.png](images/reviewed-mr.png)
* Protected branch screenshot: [images/protected-branch.png](images/protected-branch.png)
* Successful Lychee pipeline screenshot: [images/lychee-success.png](images/lychee-success.png)

## Customer review

A live customer meeting could not be scheduled before the deadline. The customer reviewed the artifacts asynchronously via chat and provided structured written feedback.

* Customer review notes: [customer-meeting-notes.md](customer-meeting-notes.md)
* Customer review summary: [customer-meeting-summary.md](customer-meeting-summary.md)
* Transcript note: [customer-meeting-transcript.md](customer-meeting-transcript.md)

Original written customer evidence is preserved for instructors and included in the Moodle PDF in sanitized form.

## Analysis and LLM usage

* Week 2 analysis: [analysis.md](analysis.md)
* LLM usage report: [llm-report.md](llm-report.md)

## Coverage

| Required artifact             | Status              |
| ----------------------------- | ------------------- |
| Product repository            | Done                |
| MIT License                   | Done                |
| User stories                  | Done                |
| MoSCoW priorities             | Done                |
| Initial MVP v1 scope          | Done                |
| Interface prototype           | Done                |
| MVP v0 runnable foundation    | Done                |
| MVP v0 demo video             | Done                |
| Customer review               | Done asynchronously |
| Customer review notes/summary | Done                |
| Lychee link checking          | Done                |
| LLM usage report              | Done                |
