from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import UserRole


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
    anonymous_id: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=120)
    anonymous_id: str | None = Field(default=None, max_length=120)


class QuestionnaireHistoryCreate(BaseModel):
    recommendation_id: str | None = Field(default=None, max_length=120)
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    primary_concern: str | None = None
    sensitivity_level: str | None = None
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    routine_preference: str | None = None
    texture_preference: str | None = None
    values: list[str] = Field(default_factory=list)
    total_price_rub: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    anonymous_id: str | None = None
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    primary_concern: str | None = None
    sensitivity_level: str | None = None
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    routine_preference: str | None = None
    texture_preference: str | None = None
    values: list[str] = Field(default_factory=list)
    questionnaire_history: list[dict[str, Any]] = Field(default_factory=list)
    feedback_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] | None = None
    primary_concern: str | None = None
    sensitivity_level: str | None = None
    budget: str | None = None
    excluded_ingredients: list[str] | None = None
    custom_restrictions: list[str] | None = None
    experience: str | None = None
    routine_preference: str | None = None
    texture_preference: str | None = None
    values: list[str] | None = None
