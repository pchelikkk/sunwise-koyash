export function buildRecommendationRequest(answers) {
  const restrictions =
    answers.restrictions && typeof answers.restrictions === "object"
      ? answers.restrictions
      : { selected: [], custom: [] };
  const age = answers.age ? Number.parseInt(String(answers.age), 10) : null;
  const concerns = (answers.concerns || []).filter(
    (value) => value !== "unknown",
  );
  const primaryConcern =
    concerns.length === 1
      ? concerns[0]
      : concerns.includes(answers.primary_concern)
        ? answers.primary_concern
        : null;

  return {
    age: Number.isFinite(age) ? age : null,
    skin_type: answers.skin_type,
    concerns,
    primary_concern: primaryConcern,
    sensitivity_level: answers.sensitivity_level || "unknown",
    budget: answers.budget || "balanced",
    excluded_ingredients: (restrictions.selected || []).filter(
      (value) => value !== "none" && value !== "unknown",
    ),
    custom_restrictions: restrictions.custom || [],
    experience: answers.experience || "beginner",
    routine_preference: answers.routine_preference || "balanced",
    texture_preference: answers.texture_preference || "no_preference",
    values: (answers.values || []).filter((value) => value !== "unknown"),
    skin_diagnostic_answers:
      answers.skin_type === "unknown"
        ? {
            after_cleansing: answers.diagnostic_after_cleansing,
            midday_shine: answers.diagnostic_midday_shine,
            pore_visibility: answers.diagnostic_pore_visibility,
            flaking: answers.diagnostic_flaking,
          }
        : null,
  };
}

export function visibleQuestionnaireQuestions(questionnaire, answers) {
  return (questionnaire ? questionnaire.questions : []).filter((question) => {
    if (question.id === "primary_concern") {
      const concerns = (answers.concerns || []).filter(
        (value) => value !== "unknown",
      );
      return concerns.length > 1;
    }
    if (!question.visible_when_question_id) return true;
    return (question.visible_when_values || []).includes(
      answers[question.visible_when_question_id],
    );
  });
}

export function toggleExclusiveMulti(current, value, maxSelections) {
  const selected = Array.isArray(current) ? current : [];
  if (value === "unknown" || value === "none") {
    return selected.includes(value) ? [] : [value];
  }

  const withoutExclusive = selected.filter(
    (item) => item !== "unknown" && item !== "none",
  );
  if (withoutExclusive.includes(value)) {
    return withoutExclusive.filter((item) => item !== value);
  }
  if (maxSelections && withoutExclusive.length >= maxSelections) {
    return withoutExclusive;
  }
  return [...withoutExclusive, value];
}

const EXCLUSIVE_MULTI_VALUES = new Set(["unknown", "none"]);

export function toggleExclusiveStructuredChoice(
  current,
  value,
  maxSelections,
) {
  const selected = Array.isArray(current?.selected) ? current.selected : [];
  const custom = Array.isArray(current?.custom) ? current.custom : [];

  if (EXCLUSIVE_MULTI_VALUES.has(value)) {
    const isOnlySelection =
      selected.length === 1 && selected[0] === value && custom.length === 0;
    return isOnlySelection
      ? { selected: [], custom: [] }
      : { selected: [value], custom: [] };
  }

  const withoutExclusive = selected.filter(
    (item) => !EXCLUSIVE_MULTI_VALUES.has(item),
  );
  if (withoutExclusive.includes(value)) {
    return {
      selected: withoutExclusive.filter((item) => item !== value),
      custom,
    };
  }
  if (
    maxSelections &&
    withoutExclusive.length + custom.length >= maxSelections
  ) {
    return { selected: withoutExclusive, custom };
  }
  return { selected: [...withoutExclusive, value], custom };
}

export function appendExclusiveCustomValue(current, value, maxSelections) {
  const normalizedValue = String(value || "").trim();
  const selected = Array.isArray(current?.selected)
    ? current.selected.filter((item) => !EXCLUSIVE_MULTI_VALUES.has(item))
    : [];
  const custom = Array.isArray(current?.custom) ? current.custom : [];

  if (!normalizedValue || custom.includes(normalizedValue)) {
    return { selected, custom };
  }
  if (maxSelections && selected.length + custom.length >= maxSelections) {
    return { selected, custom };
  }
  return { selected, custom: [...custom, normalizedValue] };
}
