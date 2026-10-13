from pydantic import BaseModel, Field, field_validator, model_validator


class LLMExplanationPreviewRequest(BaseModel):
    skin_type: str
    concerns: list[str] = Field(default_factory=list, max_length=5)
    matched_concerns: list[str] = Field(default_factory=list, max_length=5)
    name: str
    brand: str
    step: str
    ingredients: list[str] = Field(default_factory=list)
    concern_match: int = Field(default=0, ge=0)
    use_llm: bool = False

    @field_validator("concerns", "matched_concerns", "ingredients")
    @classmethod
    def normalize_list_values(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            cleaned = str(value).strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    @model_validator(mode="after")
    def validate_matched_concern_count(self) -> "LLMExplanationPreviewRequest":
        if self.concern_match != len(self.matched_concerns):
            raise ValueError("concern_match must equal len(matched_concerns)")
        return self


class LLMExplanationPreviewResponse(BaseModel):
    used_llm: bool
    provider: str
    model: str
    explanation: str
    system_prompt: str
    user_prompt: str


class LLMDemoPayloadsResponse(BaseModel):
    payloads: list[LLMExplanationPreviewRequest]
