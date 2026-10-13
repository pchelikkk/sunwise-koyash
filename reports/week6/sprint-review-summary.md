# Sprint Review Summary — Week 6

Project: KOYASH  
Team: Sunwise  
Assignment: 6  
Sprint: 4  
Release: v0.4.0  
Customer: Diana

## Context

Unlike the previous review, the customer did not test the product fully independently
this week. The team ran a facilitated trial: a working backend plus the current
frontend. The customer interacted with the flow and gave live feedback. The session was
recorded (audio).

## Outcome

- Design walkthrough completed and the mockups **approved with minor edits** as the
  final MVP v3 direction.
- Budget filtering accepted as applying **per product** across the result set; the
  customer will validate it herself on 3–5 sample runs sent the same day.
- Questionnaire agreed to be trimmed from 7 to 6 steps.
- A replacement-category bug was found: a replacement suggestion must stay in the same
  product category (a cleansing gel must not replace a cream).
- Morning/evening labeling of the routine requested.
- README review agreed; repository and secrets handover to happen after the defense.

## Handover status

- Handover level: `Ready for guided trial`.
- Customer confirmation status: `Accepted with follow-up items`.
- The product is not yet ready for fully independent customer use.

## Decisions

- Publish the Week 6 trial as `v0.4.0` and deploy it on the university VM.
- Keep the approved design as the target for the final MVP v3 (Week 7).
- Track all follow-ups as issues #50 and #61–#64.

## Action items

- Send the customer 3–5 sample recommendation runs the same day (#61).
- Validate and fix per-product budget filtering (#61).
- Fix replacement category matching (#62).
- Trim the questionnaire to 6 steps and add morning/evening labeling (part of #50).
- Prepare LLM prompt update + joint evaluation (#63).
- Plan repository and secrets handover after the defense (#64).
