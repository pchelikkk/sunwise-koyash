from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.product import ProductResponse
from app.schemas.skin_diagnosis import SkinDiagnosisResult, SkinDiagnosticAnswers


class RecommendationRequest(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str = Field(min_length=1, max_length=40)
    concerns: list[str] = Field(default_factory=list, max_length=5)
    primary_concern: str | None = Field(default=None, max_length=80)
    sensitivity_level: Literal["low", "medium", "high", "unknown"] = "unknown"
    budget: Literal["minimum", "balanced", "premium"] = "balanced"
    excluded_ingredients: list[str] = Field(default_factory=list, max_length=10)
    custom_restrictions: list[str] = Field(default_factory=list, max_length=10)
    experience: str = "beginner"
    routine_preference: Literal["minimal", "balanced", "complete"] = "balanced"
    texture_preference: Literal[
        "no_preference",
        "lightweight",
        "cream",
        "rich",
    ] = "no_preference"
    values: list[str] = Field(default_factory=list, max_length=8)
    skin_diagnostic_answers: SkinDiagnosticAnswers | None = None
    anonymous_id: str | None = Field(default=None, max_length=120)

    @field_validator(
        "concerns",
        "excluded_ingredients",
        "custom_restrictions",
        "values",
    )
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        result: list[str] = []

        for value in values:
            normalized = str(value).strip()
            if not normalized or normalized in result:
                continue
            if len(normalized) > 100:
                raise ValueError("List values must not exceed 100 characters")
            result.append(normalized)

        return result

    @model_validator(mode="after")
    def include_primary_concern(self) -> "RecommendationRequest":
        if self.primary_concern and self.primary_concern not in self.concerns:
            if len(self.concerns) >= 5:
                raise ValueError("primary_concern must be one of concerns")
            self.concerns.insert(0, self.primary_concern)
        if self.skin_type == "unknown" and self.skin_diagnostic_answers is None:
            raise ValueError("skin_diagnostic_answers are required when skin_type is unknown")
        return self


class ScoreBreakdown(BaseModel):
    routine_step_score: int = 0
    concern_score: int = 0
    primary_concern_score: int = 0
    skin_type_score: int = 0
    budget_score: int = 0
    experience_score: int = 0
    safety_score: int = 0
    sensitivity_score: int = 0
    texture_score: int = 0
    routine_preference_score: int = 0
    values_score: int = 0
    penalties: int = 0
    total: int = 0


class RecommendedProduct(BaseModel):
    routine_step: str
    product: ProductResponse
    score: int
    score_breakdown: ScoreBreakdown
    why_here: str
    matched_concerns: list[str] = Field(default_factory=list)
    budget_reason: str
    safety_note: str
    how_to_use: str
    explanation_source: Literal["deterministic", "llm"] = "deterministic"
    explanation_model: str | None = None
    llm_ready_context: dict[str, Any] = Field(default_factory=dict)


class RecommendationRoutine(BaseModel):
    morning: list[RecommendedProduct] = Field(default_factory=list)
    evening: list[RecommendedProduct] = Field(default_factory=list)


class RestrictionMatch(BaseModel):
    restriction: str
    matched_product_count: int = Field(ge=0)


class RestrictionCoverage(BaseModel):
    requested_restrictions: list[str] = Field(default_factory=list)
    matched_restrictions: list[str] = Field(default_factory=list)
    unmatched_restrictions: list[str] = Field(default_factory=list)
    matches: list[RestrictionMatch] = Field(default_factory=list)


class FilterSummary(BaseModel):
    total_products: int
    allowed_products: int
    filtered_out: int
    filter_reasons: dict[str, int] = Field(default_factory=dict)
    restriction_coverage: RestrictionCoverage = Field(
        default_factory=RestrictionCoverage,
    )


class RecommendationResponse(BaseModel):
    recommendation_id: str
    algorithm_version: str
    skin_profile: SkinDiagnosisResult | None = None
    routine: RecommendationRoutine
    filter_summary: FilterSummary
    total_price_rub: int
    created_at: datetime
