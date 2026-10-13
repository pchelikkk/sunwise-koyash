# Sprint Review Notes — Week 6

Project: KOYASH  
Team: Sunwise  
Assignment: 6  
Sprint: 4  
Release: v0.4.0  
Customer: Diana

## Session

- Type: facilitated customer trial + UAT + Sprint Review.
- Attendees: customer (Diana) and the Sunwise team.
- Format: the team demonstrated a working backend with the current frontend; the
  customer interacted with the flow and gave feedback. Session recorded (audio).
- Recording: shared privately via Moodle (audio)

## Agenda

1. Design walkthrough against the designer mockups.
2. Live trial of the questionnaire → recommendation → routine flow.
3. Budget filtering behavior.
4. Product replacement behavior.
5. Questionnaire content.
6. Next steps, deployment, and handover.

## Notes

### Design

- The team walked the customer through the mockups.
- The customer approved the design **with minor edits** as the final MVP v3 direction.
- Requested: explicit morning/evening labeling of the recommended routine.

### Budget filtering

- Confirmed that filtering should apply **per product** across the recommendation set,
  not only to the total.
- The customer will validate this herself on 3–5 sample runs that the team sends the
  same day.

### Product replacement

- Bug identified: a replacement suggestion must remain in the same product category.
  A cleansing gel must not be offered as a replacement for a cream.

### Questionnaire

- Agreed to trim the questionnaire from 7 to 6 steps to remove redundancy.

### Deployment and handover

- The trial is deployed on the university VM and published as `v0.4.0`.
- Repository access and secrets will be handed over after the course defense.
- README review agreed; the team keeps documentation current.
- The product is not yet ready for fully independent customer use; this session is a
  guided trial.

## UAT outcome

| ID | Scenario | Result |
|---|---|---|
| UAT-01 | Complete the questionnaire end to end | Passed |
| UAT-02 | Receive an explainable recommendation | Passed |
| UAT-03 | Account / profile / history | Passed |
| UAT-04 | Product feedback flow | Passed |
| UAT-05 | Design matches approved direction | Partial (minor edits) |
| UAT-06 | Per-product budget filtering | Pending customer validation (#61) |
| UAT-07 | Independent use without facilitation | To verify after follow-ups |

## Decisions and action items

- Deploy the trial on the university VM; publish `v0.4.0`.
- Send 3–5 sample recommendation runs to the customer the same day (#61).
- Validate/fix per-product filtering (#61); fix replacement category (#62).
- Trim questionnaire to 6 steps + morning/evening labeling (#50).
- LLM prompt update + joint evaluation (#63); repo/secrets handover after defense (#64).
