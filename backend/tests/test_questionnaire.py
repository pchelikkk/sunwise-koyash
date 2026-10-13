from fastapi.testclient import TestClient

from app.main import app

EXPECTED_QUESTION_IDS = [
    "age",
    "skin_type",
    "diagnostic_after_cleansing",
    "diagnostic_midday_shine",
    "diagnostic_pore_visibility",
    "diagnostic_flaking",
    "concerns",
    "primary_concern",
    "sensitivity_level",
    "budget",
    "restrictions",
    "experience",
    "routine_preference",
    "texture_preference",
    "values",
]


def _questionnaire() -> dict:
    with TestClient(app) as client:
        response = client.get("/api/v1/questionnaire")

    assert response.status_code == 200
    return response.json()


def test_questionnaire_has_professional_adaptive_flow() -> None:
    payload = _questionnaire()

    assert payload["version"] == "professional-v4"
    assert len(payload["questions"]) == 15
    assert [question["id"] for question in payload["questions"]] == (EXPECTED_QUESTION_IDS)
    assert [question["step"] for question in payload["questions"]] == list(range(1, 16))
    assert {question["total_steps"] for question in payload["questions"]} == {15}


def test_questionnaire_exposes_validation_metadata() -> None:
    questions = {question["id"]: question for question in _questionnaire()["questions"]}

    assert questions["concerns"]["min_selections"] == 1
    assert questions["concerns"]["max_selections"] == 5
    assert questions["primary_concern"]["depends_on_question_id"] == "concerns"

    diagnostic_ids = [
        "diagnostic_after_cleansing",
        "diagnostic_midday_shine",
        "diagnostic_pore_visibility",
        "diagnostic_flaking",
    ]
    for question_id in diagnostic_ids:
        assert questions[question_id]["visible_when_question_id"] == "skin_type"
        assert questions[question_id]["visible_when_values"] == ["unknown"]

    restrictions = questions["restrictions"]
    assert restrictions["allows_custom"] is True
    assert restrictions["answer_type"] == "multi_with_custom"
    assert restrictions["custom_input_max_length"] == 100
    assert restrictions["max_selections"] == 10
    assert len(restrictions["popular_suggestions"]) >= 4

    assert questions["values"]["max_selections"] == 3
    assert questions["age"]["required"] is False
    assert questions["age"]["min_value"] == 12
    assert questions["age"]["max_value"] == 100


def test_questionnaire_options_match_supported_catalog_semantics() -> None:
    questions = {question["id"]: question for question in _questionnaire()["questions"]}

    skin_types = {option["value"] for option in questions["skin_type"]["options"]}
    assert {"normal", "oily", "dry", "combination", "sensitive"}.issubset(skin_types)

    concern_values = {option["value"] for option in questions["concerns"]["options"]}
    assert {
        "acne",
        "dehydration",
        "pigmentation",
        "reactivity",
    }.issubset(concern_values)
    assert "fast_result" not in concern_values

    value_values = {option["value"] for option in questions["values"]["options"]}
    assert {"vegan", "cruelty_free", "soft_formula", "price_quality"}.issubset(value_values)
    assert "quality" not in value_values
    assert "fast_result" not in value_values

    for question_id, question in questions.items():
        if question_id != "restrictions":
            assert question["popular_suggestions"] == []


def test_questionnaire_copy_is_written_for_people_not_for_the_scoring_engine() -> None:
    questions = _questionnaire()["questions"]
    copy = " ".join(
        [
            str(value)
            for question in questions
            for value in (
                question["title"],
                question["description"],
                question["why_we_ask"],
            )
        ]
    ).casefold()

    assert "score" not in copy
    assert "детерминирован" not in copy
    assert "движок" not in copy
    assert all(question["why_we_ask"].strip() for question in questions)
