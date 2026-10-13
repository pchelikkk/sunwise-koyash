from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ResolvedSkinType = Literal["normal", "oily", "dry", "combination"]


class SkinDiagnosticAnswers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    after_cleansing: Literal["comfortable", "slightly_tight", "very_tight"]
    midday_shine: Literal["none", "t_zone", "all_over"]
    pore_visibility: Literal["barely_visible", "t_zone_visible", "widely_visible"]
    flaking: Literal["never", "sometimes", "often"]


class SkinDiagnosisResult(BaseModel):
    method: Literal["guided_diagnostic", "self_reported"]
    submitted_skin_type: str
    resolved_skin_type: str
    confidence: Literal["low", "medium", "high"]
    confidence_percent: int = Field(ge=0, le=100)
    scores: dict[str, int] = Field(default_factory=dict)
    signals: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Оценка помогает настроить косметический уход и не является медицинской "
        "диагностикой. При стойком дискомфорте стоит обратиться к дерматологу."
    )


class SkinDiagnosisRequest(SkinDiagnosticAnswers):
    pass


class SkinDiagnosisResponse(SkinDiagnosisResult):
    pass
