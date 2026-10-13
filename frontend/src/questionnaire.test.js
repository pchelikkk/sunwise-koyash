import { describe, expect, it } from "vitest";

import {
  appendExclusiveCustomValue,
  buildRecommendationRequest,
  toggleExclusiveMulti,
  toggleExclusiveStructuredChoice,
  visibleQuestionnaireQuestions,
} from "./questionnaire.js";

describe("questionnaire helpers", () => {
  it("builds a clean request and removes neutral choices", () => {
    const payload = buildRecommendationRequest({
      skin_type: "unknown",
      diagnostic_after_cleansing: "slightly_tight",
      diagnostic_midday_shine: "t_zone",
      diagnostic_pore_visibility: "t_zone_visible",
      diagnostic_flaking: "sometimes",
      concerns: ["unknown"],
      primary_concern: "unknown",
      values: ["unknown"],
      restrictions: { selected: ["unknown", "fragrance"], custom: ["lanolin"] },
    });

    expect(payload.concerns).toEqual([]);
    expect(payload.primary_concern).toBeNull();
    expect(payload.values).toEqual([]);
    expect(payload.excluded_ingredients).toEqual(["fragrance"]);
    expect(payload.skin_diagnostic_answers).toEqual({
      after_cleansing: "slightly_tight",
      midday_shine: "t_zone",
      pore_visibility: "t_zone_visible",
      flaking: "sometimes",
    });
  });

  it("shows diagnostic questions only when skin type is unknown", () => {
    const questionnaire = {
      questions: [
        { id: "skin_type" },
        {
          id: "diagnostic_after_cleansing",
          visible_when_question_id: "skin_type",
          visible_when_values: ["unknown"],
        },
        { id: "concerns" },
        { id: "primary_concern" },
      ],
    };

    expect(
      visibleQuestionnaireQuestions(questionnaire, {
        skin_type: "oily",
        concerns: ["acne"],
      }).map((question) => question.id),
    ).toEqual(["skin_type", "concerns"]);
    expect(
      visibleQuestionnaireQuestions(questionnaire, {
        skin_type: "oily",
        concerns: ["acne", "sebum"],
      }).map((question) => question.id),
    ).toEqual(["skin_type", "concerns", "primary_concern"]);
    expect(
      buildRecommendationRequest({ skin_type: "oily", concerns: ["acne"] })
        .primary_concern,
    ).toBe("acne");
    expect(
      visibleQuestionnaireQuestions(questionnaire, {
        skin_type: "unknown",
        concerns: ["unknown"],
      }).map((question) => question.id),
    ).toEqual(["skin_type", "diagnostic_after_cleansing", "concerns"]);
  });

  it("keeps neutral multi-select choices exclusive and respects limits", () => {
    expect(toggleExclusiveMulti(["acne"], "unknown", 5)).toEqual(["unknown"]);
    expect(toggleExclusiveMulti(["unknown"], "dryness", 5)).toEqual(["dryness"]);
    expect(toggleExclusiveMulti(["acne", "dryness"], "sebum", 2)).toEqual([
      "acne",
      "dryness",
    ]);
  });

  it("keeps neutral restriction choices exclusive from presets and custom values", () => {
    expect(
      toggleExclusiveStructuredChoice(
        { selected: ["fragrance", "alcohol"], custom: ["ланолин"] },
        "none",
        10,
      ),
    ).toEqual({ selected: ["none"], custom: [] });

    expect(
      toggleExclusiveStructuredChoice(
        { selected: ["none"], custom: [] },
        "fragrance",
        10,
      ),
    ).toEqual({ selected: ["fragrance"], custom: [] });

    expect(
      appendExclusiveCustomValue(
        { selected: ["unknown"], custom: [] },
        "ланолин",
        10,
      ),
    ).toEqual({ selected: [], custom: ["ланолин"] });
  });
});
