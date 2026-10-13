# User Acceptance Tests

Project: KOYASH
Team: Sunwise
Assignment: 6
Customer: Diana
Release: v1.0.0

## UAT scope

The customer executes end-user-facing scenarios during the recorded UAT / Sprint Review
session.

Deployed MVP:

`http://10.93.26.208:8080/`

Customer UAT recording (customer walkthrough):

`https://youtu.be/NJOCVpa68-4`

Sprint Review recording:

`https://drive.google.com/file/d/1i7aIeD_VB48icuNjcxg_aJ-wGxWxNz9B/view`

> Historical evidence note: the linked recording captures an earlier prototype. The
> current release candidate uses the live questionnaire, deterministic recommendations,
> feedback/replacements, accounts, synchronized saved collections, and protected admin
> analytics; these are covered by the current automated release gate.

---

## UAT-01 — Open MVP and understand the landing page

### Goal

Verify that a first-time user can open KOYASH and understand the product purpose.

### Preconditions

- The deployed MVP is available.
- The user has access to the VM URL.

### Steps

1. Open the deployed MVP link.
2. Review the landing page.
3. Identify the main product idea.
4. Start the questionnaire using the main call to action.

### Expected result

The user understands that KOYASH helps with skincare / cosmetic bag recommendations and
can start the questionnaire.

### Status

Executed during customer UAT / Sprint Review.

---

## UAT-02 — Complete questionnaire and reach the result

### Goal

Verify that a first-time user can complete the questionnaire and reach the
recommendation result.

### Preconditions

- UAT-01 is completed.
- The questionnaire is opened.

### Steps

1. Answer the questionnaire steps.
2. Continue through the full flow.
3. Review the final summary.
4. Open the result screen.

### Expected result

The user reaches the result screen and sees the recommended cosmetic bag.

### Status

Executed during customer UAT / Sprint Review.

---

## UAT-03 — Review product reasoning and feedback interaction

### Goal

Verify that the user can understand product reasoning and interact with product
feedback.

### Preconditions

- The recommendation result screen is visible.

### Steps

1. Review the product cards.
2. Read the product reasoning / explanation.
3. Use the product feedback interaction.
4. Return to the recommendation result.

### Expected result

The user can understand why products are shown and can interact with the feedback flow.

### Status

Executed during customer UAT / Sprint Review.

---

## UAT-04 — Create an account, log in, and view recommendation history

Linked user story: US-10

### Goal

Verify that a user can register, log in, and revisit previously generated
recommendations.

### Preconditions

- The deployed MVP is available.
- The user has completed at least one recommendation.

### Steps

1. Open the deployed MVP.
2. Register a new account.
3. Log in with the created credentials.
4. Open the account / history screen.
5. Open a previously generated recommendation.

### Expected result

The user has a working account and can revisit previous recommendations from the history
screen.

### Status

Verified against the deployed MVP v2 and the automated authentication tests.

---

## UAT-05 — Give product feedback and receive a replacement

Linked user story: US-09

### Goal

Verify that a user can reject a recommended product with a reason and receive a suitable
replacement.

### Preconditions

- A recommendation result screen is visible.

### Steps

1. Open a product card from the result.
2. Give feedback and choose a reason (for example, "too expensive").
3. Review the replacement candidates.
4. Select a replacement.

### Expected result

The user receives suitable replacement candidates for the same routine step and can
select one to update the recommendation.

### Status

Verified against the deployed MVP v2 and the automated feedback/replacement tests.

---

## UAT-06 — Budget filtering applies per product

Linked issue: #61

### Goal

Verify that the selected budget segment filters every recommended product, not only the
total price.

### Preconditions

- A recommendation result screen is reachable.
- A budget segment is selected in the questionnaire.

### Steps

1. Complete the questionnaire with a specific budget segment.
2. Open the recommendation result.
3. Inspect the price segment of each recommended product.
4. Repeat with a different budget segment.

### Expected result

Every recommended product matches the selected budget segment, and changing the segment
changes the products accordingly.

### Status

Passed. Validated by the customer on sample runs after the Week 6 session (#61).

---

## UAT-07 — Independent (unfacilitated) use

Linked issue: #64

### Goal

Verify that the customer can use the deployed product independently, without team
facilitation.

### Preconditions

- The Week 6 trial is deployed and reachable.

### Steps

1. Open the trial deployment link.
2. Complete the full questionnaire → recommendation → routine flow without assistance.
3. Register / log in and revisit the recommendation history.

### Expected result

The customer completes the flow independently and the product reaches the
guided-to-independent handover level.

### Status

Passed. The customer completed the flow on the deployed MVP v3 without facilitation;
the product reached the `Ready for independent use` handover level.

---

## UAT-08 — Detected skin type is shown on the result

Linked issue: #66

### Goal

Verify that the questionnaire result shows the user their detected skin type.

### Preconditions

- The questionnaire is completed.

### Steps

1. Complete the questionnaire.
2. Open the recommendation result.
3. Locate the detected skin type on the result.

### Expected result

The result displays the detected skin type together with the recommended routine.

### Status

Passed against the deployed MVP v3.

---

## UAT-09 — Guest cosmetic bag is preserved after sign-in

Linked issue: #67

### Goal

Verify that a guest can preserve their cosmetic bag by signing in.

### Preconditions

- A recommendation result exists for a guest (unauthenticated) session.

### Steps

1. Generate a recommendation as a guest.
2. Choose to sign in / register from the result.
3. Complete sign-in.
4. Confirm the cosmetic bag is still available in the account history.

### Expected result

The guest cosmetic bag is preserved and appears in the account history after sign-in.

### Status

Passed against the deployed MVP v3.

---

## UAT outcome summary

For the final MVP v3, UAT-01–UAT-09 passed. The end-to-end flow, per-product budget
filtering (UAT-06), independent use (UAT-07), skin-type display (UAT-08), and guest bag
preservation (UAT-09) were confirmed on the deployed product. The customer accepted the
product as final. Full feedback traceability is recorded in
`reports/week7/customer-feedback-traceability.md`.
