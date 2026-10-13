from pydantic import BaseModel, ConfigDict, Field


class RestrictionSuggestionResponse(BaseModel):
    canonical_key: str
    display_name: str
    usage_count: int = 0
    status: str = "approved"
    is_popular: bool = True

    model_config = ConfigDict(extra="ignore")


class RestrictionSuggestionListResponse(BaseModel):
    suggestions: list[RestrictionSuggestionResponse]


class CustomRestrictionCreate(BaseModel):
    value: str = Field(min_length=1, max_length=80)
    anonymous_id: str | None = Field(default=None, max_length=120)


class CustomRestrictionResponse(BaseModel):
    raw_value: str
    normalized_key: str
    display_name: str
    status: str
    added_to_popular: bool
