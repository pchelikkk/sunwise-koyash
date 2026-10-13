# User Stories

## Personas and roles

### Primary user: skincare customer

A person who wants to choose skincare products but does not want to spend too much time comparing many products, reading ingredient lists, or guessing what is suitable.

### Customer / product owner

The project customer who defines the product vision, approves the MVP scope, and provides feedback about the recommendation logic and interface direction.

### Returning user

A future user who may come back later to review previous recommendations, give feedback, or track skin reaction. This role is important for future versions but is not the core of the first MVP scope.

---

## Initial proposed MVP v1 scope

The initial proposed MVP v1 scope includes only active `Must Have` stories that are small enough to prototype, discuss with the customer, and implement during the course.

Selected stable IDs:

- US-01
- US-02
- US-03
- US-04
- US-05
- US-06
- US-07

This scope focuses on the main KOYASH journey:

Landing page → questionnaire → rule-based filtering → personal cosmetic bag → product explanations.

---

## US-01: Understand the service from the landing page

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want to understand what KOYASH does from the landing page,  
so that I can decide whether I want to start the recommendation process.

### Notes and constraints

The landing page should explain that KOYASH is an independent skincare recommendation service, not a cosmetics manufacturer or marketplace. The tone should be warm, clear, and trustworthy. The page should include a clear call-to-action to start the questionnaire.

---

## US-02: Complete a step-by-step questionnaire

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want to answer a step-by-step skincare questionnaire,  
so that KOYASH can understand my basic needs before recommending products.

### Notes and constraints

The questionnaire should not feel like a dry registration form. It should feel simple, warm, and easy to complete. The MVP questionnaire should include age, skin type, skin concerns, allergies or exclusions, budget, values, and skincare experience.

---

## US-03: Select a comfortable budget

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want to choose a comfortable budget range,  
so that KOYASH does not recommend products that are unrealistic for me to buy.

### Notes and constraints

Budget should be handled using clear segments such as Budget, Medium, and High, or a controlled slider with steps. Free arbitrary input should be avoided because it can make filtering harder and less predictable.

---

## US-04: Exclude allergens and unwanted ingredients

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want to specify ingredients or product features that I want to avoid,  
so that KOYASH does not recommend products that may be unsuitable for me.

### Notes and constraints

Allergies and exclusions should be treated as hard constraints. If there are not enough matching products, the system may relax soft filters, but it should not ignore allergy-related exclusions.

---

## US-05: Receive rule-based recommendations from the product database

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want KOYASH to filter products from a verified product database,  
so that my recommendation is based on structured product information instead of random or hallucinated suggestions.

### Notes and constraints

The MVP should not use an LLM for recommendations. Product selection should be based on rule-based filtering and scoring using available product fields such as category, price segment, issues, main actives, allergens, vegan status, cruelty-free status, and product status.

---

## US-06: View a personal cosmetic bag

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want to receive a personal cosmetic bag with several recommended products,  
so that I can see a complete first version of a suitable skincare routine.

### Notes and constraints

The cosmetic bag should contain approximately 5–10 products when possible. The average target is around 7 products. For the first demo, it is acceptable to focus on budget and medium products because the current dataset has fewer high-segment products.

---

## US-07: Understand why each product was recommended

**Requirement status:** Active  
**MoSCoW priority:** Must Have

As a skincare customer,  
I want to see an explanation for each recommended product,  
so that I can understand why it fits my answers and make a more confident decision.

### Notes and constraints

Each product card should include a short explanation based on structured data, not a generic marketing phrase. The explanation may mention matched skin concerns, routine role, budget fit, main actives, and avoided allergens where relevant.

---

## US-08: Open product and consultation links

**Requirement status:** Active  
**MoSCoW priority:** Should Have

As a skincare customer,  
I want to open product links and a consultation link from the result page,  
so that I can continue from the recommendation to the next practical step.

### Notes and constraints

Product links can be placeholders during early MVP v0 work if the final dataset links are not fully ready. The consultation link should be visible on the result page or near the final recommendation summary.

---

## US-09: Give feedback when a product does not fit

**Requirement status:** Active  
**MoSCoW priority:** Should Have

As a skincare customer,  
I want to mark that a recommended product did not fit me,  
so that KOYASH can collect feedback for future improvements.

### Notes and constraints

Feedback can be simple in the first version. Possible reasons include price, brand dislike, ingredient concern, texture, already tried, or other. This story may be implemented after the core recommendation flow if time is limited.

---

## US-10: View previous recommendations

**Requirement status:** Active  
**MoSCoW priority:** Could Have

As a returning user,  
I want to view my previous cosmetic bags,  
so that I can compare recommendations and remember what was suggested before.

### Notes and constraints

This is useful for the future product vision, especially for monitoring skin reaction and progress. However, it requires user identity, storage of recommendation history, and possibly authentication, so it is not part of the initial MVP v1 scope.

---

## US-11: See product analytics and recommendation statistics

**Requirement status:** Active  
**MoSCoW priority:** Could Have

As the product owner,  
I want to see basic statistics about common skin concerns, budgets, and recommended products,  
so that I can understand user needs and improve the service later.

### Notes and constraints

This can be valuable in future versions, but it is not required for the first MVP. The team may still design the database in a way that does not block future analytics.

---

## US-12: Use photo-based skin analysis

**Requirement status:** Active  
**MoSCoW priority:** Won't Have

As a skincare customer,  
I want to upload a face photo for automatic skin analysis,  
so that KOYASH can detect my skin condition visually.

### Notes and constraints

This story is excluded from the course scope. Photo-based analysis adds privacy, accuracy, medical, and technical risks. It is also outside the current MVP vision, which focuses on questionnaire-based recommendation and explainable filtering from a product database.

---

## US-13: Manage products through an admin panel

**Requirement status:** Removed  
**Previous MoSCoW priority:** Could Have

As an admin,  
I want to add and edit products through a web admin panel,  
so that the product database can be managed from the website.

**Reason:** This story was removed after customer clarification. The MVP does not need an admin panel or admin/editor roles on the user-facing site. Product data can be imported or maintained separately from the public product interface.