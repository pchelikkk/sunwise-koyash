# Week 2 Analysis

## Learning points

During Week 2, the team learned that the KOYASH product needs a narrow and clearly validated MVP scope. The initial product vision includes many possible directions, such as LLM-based explanations, personal history, monitoring, and more advanced personalization. However, for the course MVP, the team had to separate the core user value from later-stage features.

The main product learning is that the first version should focus on a simple and explainable skincare recommendation flow:

* landing page;
* step-by-step questionnaire;
* budget selection;
* allergy and ingredient exclusions;
* rule-based recommendation from a product database;
* personal cosmetic bag;
* clear explanations for every recommended product.

Writing user stories helped the team avoid vague feature descriptions and connect each feature to user value. MoSCoW prioritization helped separate the required MVP flow from useful but non-essential features, such as recommendation history, analytics, or photo-based skin analysis.

Prototyping also showed that the questionnaire must stay simple. Some inputs should be single-choice, such as skin type, budget, values, and skincare experience. Other inputs should allow multiple choices, such as skin concerns and ingredient exclusions. This distinction is important for both usability and future implementation.

The MVP v0 technical work confirmed that the selected stack is suitable for the project foundation. React with Vite works well for the frontend, FastAPI is sufficient for the backend API, and Docker Compose makes the project runnable in a reproducible way. The smoke check also confirmed that the frontend can communicate with the backend and display API data.

## Validated assumptions

The team validated several assumptions during Week 2:

1. **A rule-based MVP is more realistic than an LLM-first MVP.**
   The recommendation process should first be controlled by backend logic and product database filtering. LLM-based explanations can be considered later, but the MVP should not depend on an LLM to choose products.

2. **Allergy and ingredient exclusions must be treated as hard constraints.**
   The prototype and user stories reflect that selected allergens or unwanted ingredients should not be ignored during recommendation.

3. **The result page must explain recommendations.**
   A simple list of products is not enough for KOYASH. The core value is a personal cosmetic bag with explanations for why each product was selected.

4. **The MVP should focus on desktop-first web usage.**
   The current prototype and MVP v0 are optimized for a desktop web flow. Mobile polish is useful later, but not required for the first validated MVP scope.

5. **The selected technical foundation is sufficient for MVP v0.**
   The project can be run locally with Docker Compose. The frontend opens successfully, the backend health endpoint works, and the frontend can fetch sample product data from the backend.

6. **The Figma prototype is a useful validation artifact.**
   The interactive prototype helps demonstrate the planned product flow before implementing the full questionnaire and recommendation logic.

7. **Customer validation is still required for final confirmation.**
   A live meeting could not be scheduled before the deadline, so the customer was asked to review the artifacts asynchronously and provide written approval and feedback.

## Needs clarification

The following questions and risks still require clarification:

1. **Final customer approval.**
   The team is waiting for written customer confirmation of the user stories, MoSCoW priorities, initial MVP v1 scope, and Figma prototype feedback.

2. **Exact questionnaire fields.**
   The current prototype includes a reasonable questionnaire flow, but some questions may need refinement after customer feedback.

3. **Product data preparation.**
   The real product dataset must be cleaned and mapped to the recommendation logic. Some fields may require normalization before implementation.

4. **Recommendation rules.**
   The team still needs to define exact rule-based filtering and ranking logic for matching user answers to products.

5. **Budget logic.**
   The MVP should clarify whether budget is selected as a general segment or separately by routine/category.

6. **Consultation link behavior.**
   The prototype includes a consultation CTA, but the final destination and expected behavior need to be confirmed.

7. **Feedback handling.**
   Feedback is useful for later improvement, but the team needs to decide whether it belongs in MVP v1 or should remain a post-MVP feature.

8. **Public repository evidence.**
   Written consent for the public MIT-licensed development model must be preserved as evidence for the final Moodle PDF.

## Planned response

Based on Week 2 work, the team plans to continue with a focused MVP v1 implementation.

The next development steps are:

1. Implement the questionnaire flow in the React frontend.
2. Define structured answer data for the backend.
3. Add or prepare the product dataset.
4. Implement rule-based filtering and ranking in the backend.
5. Return recommended products with structured explanations.
6. Display a personal cosmetic bag in the frontend.
7. Keep allergy and ingredient exclusions as hard filters.
8. Keep LLM-based recommendation logic, user history, advanced analytics, and photo-based analysis out of MVP v1.

The planned MVP v1 scope remains focused on the Must Have stories:

* US-01: Understand the service from the landing page;
* US-02: Complete a step-by-step questionnaire;
* US-03: Select a comfortable budget;
* US-04: Exclude allergens and unwanted ingredients;
* US-05: Receive rule-based recommendations from the database;
* US-06: View a personal cosmetic bag;
* US-07: Understand why each product was recommended.

If the customer provides feedback that changes priorities or scope, the team will update `reports/week2/user-stories.md`, the prototype, and this analysis accordingly.
