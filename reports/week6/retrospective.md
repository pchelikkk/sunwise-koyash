# Retrospective

Project: KOYASH  
Team: Sunwise  
Assignment: 6  
Release: v0.4.0

## Sprint goal

Deliver an integrated Week 6 trial (MVP v3 candidate) with a working backend, run a
facilitated customer trial / UAT / Sprint Review, get the design approved, and package
the increment with documentation and the v0.4.0 release.

## What went well

- The backend covered the full end-to-end flow and was demonstrated live.
- The design was approved (with minor edits) as the final MVP v3 direction.
- Clear, actionable feedback was captured (filtering, replacement, questionnaire).
- Documentation was split into small, cross-reviewed merge requests.
- The v0.4.0 trial was deployed on the university VM.

## What did not go well

- The frontend was not ready for fully independent customer use, so the trial was
  facilitated.
- A replacement-category bug (gel offered for a cream) reached the customer session.
- Some evidence links (deploy, recording, demo) were still pending at packaging time.

## What we will improve

- Keep the frontend deployable and self-serviceable earlier in the sprint.
- Add category-aware rules and tests for recommendation replacement.
- Collect deploy/recording/demo links immediately after each activity.
- Continue continuous documentation instead of end-of-sprint consolidation.

## Action items

- Send 3–5 sample recommendation runs to the customer (#61).
- Validate/fix per-product budget filtering (#61); fix replacement category (#62).
- Apply approved design 1:1 + morning/evening labeling (#50).
- LLM prompt update + joint evaluation (#63).
- Fill the v0.4.0 release link after deploy; verify all Week 6 links are accessible.
- Repository and secrets handover after the defense (#64).
​