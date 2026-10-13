# KOYASH Figma Prototype Specification

## Language and tone

The prototype must be in Russian because the KOYASH interface is intended to be Russian-language.

Tone:
- warm;
- caring;
- clear;
- not childish;
- not medical-looking;
- not aggressive marketing.

## Main flow

1. Landing page
2. Questionnaire welcome
3. Age
4. Skin type
5. Skin concerns
6. Allergies and exclusions
7. Budget
8. Values / strategy
9. Skincare experience
10. Answer summary
11. Loading
12. Personal cosmetic bag
13. Product details
14. Feedback
15. Thank you

## Important interaction rules

Single choice:
- skin type;
- budget;
- values / strategy;
- skincare experience;
- feedback reason.

Multiple choice:
- skin concerns;
- exclusions / ingredients to avoid.

Exclusive option:
- in exclusions, “Не знаю” should clear other selected exclusions.

## MVP constraints reflected in prototype

- no LLM recommendations in MVP;
- rule-based filtering from product database;
- allergies and exclusions are hard constraints;
- desktop-first layout;
- informational disclaimer, not medical advice;
- result page includes product, category, price, explanation, routine order, consultation CTA, and feedback option.

## Screens covered by stable user story IDs

- US-01: Landing page
- US-02: Step-by-step questionnaire
- US-03: Budget selection
- US-04: Allergies and exclusions
- US-05: Rule-based recommendation concept
- US-06: Personal cosmetic bag
- US-07: Product explanations
- US-09: Feedback when product does not fit
