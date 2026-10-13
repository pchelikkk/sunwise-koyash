# Customer Review Meeting Plan

## Goal

The goal of this meeting is to review the current Week 2 artifacts with the customer and receive feedback and approval for:

- documented user stories;
- MoSCoW priorities;
- initial proposed MVP v1 scope;
- prototype direction.

The meeting is also used to confirm permissions related to recording, transcript sharing, and the public MIT-licensed repository model.

---

## 1. Recording and transcript permission

Before recording starts, ask:

> Can we record this meeting for course assessment?

Explain:

> The recording will be shared privately only with the course instructors. We will also prepare a sanitized English transcript without personal names, private contacts, or confidential details.

Then ask separately:

> Can we publish the sanitized English transcript in the repository, or should we keep it only in the private Moodle submission?

Record the answer in the meeting summary.

---

## 2. Public repository and MIT License confirmation

Ask:

> We also want to confirm that the project code can be available online during the course and that the repository can use the MIT License for educational purposes. Is this still okay?

Clarify:

> We will not publish private data, secrets, API keys, personal contacts, or confidential business information.

Record the answer in the meeting summary.

---

## 3. User stories review

Show `reports/week2/user-stories.md`.

Explain:

> We prepared user stories with stable IDs, requirement status, and MoSCoW priorities. These stories describe the product from the user point of view and help us define the MVP scope.

Ask:

1. Do these user stories correctly describe KOYASH from your point of view?
2. Are there any stories that feel wrong, unnecessary, or duplicated?
3. Are we missing an important story for the first course version?
4. Do you agree that the admin panel is removed from MVP scope?

Expected approval:

> Do you approve the current user stories after our discussion?

---

## 4. MoSCoW priorities review

Explain:

> We marked the core recommendation flow as Must Have. Future features such as history, analytics, and photo-based skin analysis are lower priority or excluded from the course scope.

Ask:

1. Do you agree with these MoSCoW priorities?
2. Is anything marked as Must Have that should be lower priority?
3. Is anything marked as Should Have or Could Have that should become Must Have?
4. Is anything excluded that should not be excluded?

Expected approval:

> Do you approve the MoSCoW priorities?

---

## 5. Initial proposed MVP v1 scope review

Show the selected MVP v1 scope:

- US-01: Understand the service from the landing page
- US-02: Complete a step-by-step questionnaire
- US-03: Select a comfortable budget
- US-04: Exclude allergens and unwanted ingredients
- US-05: Receive rule-based recommendations from the product database
- US-06: View a personal cosmetic bag
- US-07: Understand why each product was recommended

Explain:

> We selected a small MVP v1 scope around the main KOYASH journey: landing page, questionnaire, rule-based filtering, cosmetic bag, and explanations.

Ask:

1. Is this scope small enough for the course but still useful for KOYASH?
2. If we deliver this first, would it feel like a meaningful first version?
3. Should feedback about unsuitable products be inside MVP v1 or after MVP v1?

Expected approval:

> Do you approve this initial proposed MVP v1 scope?

---

## 6. Prototype review

Show the Figma prototype or prototype board.

Explain the flow:

> The prototype follows the path: landing page → questionnaire → loading → personal cosmetic bag → product details → feedback.

Ask:

1. Does this flow feel close to what you imagined for KOYASH?
2. Does the questionnaire feel warm and understandable, or still too dry?
3. Are any screens unnecessary or confusing?
4. Does the result page show the right information: product, price, explanation, link, and consultation option?
5. Are the explanations useful enough for a user?
6. Is the tone close to KOYASH: warm, caring, but not childish?

Prototype approval is not required, but feedback should be recorded.

---

## 7. MVP v0 explanation

Explain:

> For the course, MVP v0 is not the final product. It is only a technical foundation: frontend, backend, sample API call, and a smoke check.

Ask:

1. Is it okay that MVP v0 uses placeholders and sample product data?
2. Is there anything we should avoid showing in the public MVP v0 demo?

---

## 8. Open questions

Ask if time allows:

1. Should routine order be mandatory in MVP, for example cleanser, serum, moisturizer, SPF?
2. Are product images mandatory in MVP, or can we use placeholders at first?
3. If fewer than 5 suitable products are found, should we show fewer products or relax soft filters?
4. Which filters must never be relaxed?
5. Should budget be Budget / Medium / High, or a slider with fixed steps?
6. Should the consultation link be visible immediately in MVP?
7. Should “this product did not fit” feedback be included in MVP v1 or later?

---

## 9. Final confirmation

Before ending the meeting, ask directly:

1. Do you approve the updated user stories?
2. Do you approve the MoSCoW priorities?
3. Do you approve the initial proposed MVP v1 scope?
4. Can we continue with this prototype direction and update it based on your feedback?

---

## Action points after meeting

After the meeting, the team should:

1. update `user-stories.md` if the customer changes anything;
2. update prototype if needed;
3. write `customer-meeting-summary.md`;
4. prepare sanitized English transcript or detailed notes;
5. update Week 2 README;
6. include approval evidence in Moodle PDF.