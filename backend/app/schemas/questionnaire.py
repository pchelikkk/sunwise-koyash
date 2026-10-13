from pydantic import BaseModel, Field

from app.schemas.restriction import RestrictionSuggestionResponse


class QuestionOption(BaseModel):
    id: str
    label: str
    value: str
    description: str | None = None


class QuestionnaireQuestion(BaseModel):
    id: str
    step: int
    total_steps: int
    title: str
    description: str
    answer_type: str
    options: list[QuestionOption] = Field(default_factory=list)
    why_we_ask: str
    allows_custom: bool = False
    popular_suggestions: list[RestrictionSuggestionResponse] = Field(default_factory=list)
    input_placeholder: str | None = None
    min_value: int | None = None
    max_value: int | None = None
    unit: str | None = None
    required: bool = True
    min_selections: int | None = None
    max_selections: int | None = None
    depends_on_question_id: str | None = None
    visible_when_question_id: str | None = None
    visible_when_values: list[str] = Field(default_factory=list)
    custom_input_max_length: int | None = None


class QuestionnaireResponse(BaseModel):
    version: str
    questions: list[QuestionnaireQuestion]
