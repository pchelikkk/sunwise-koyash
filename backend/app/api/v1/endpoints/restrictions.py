from fastapi import APIRouter, Depends

from app.db.mongodb import get_database
from app.repositories.restriction_repository import RestrictionRepository
from app.schemas.restriction import (
    CustomRestrictionCreate,
    CustomRestrictionResponse,
    RestrictionSuggestionListResponse,
)
from app.services.restriction_service import RestrictionService

router = APIRouter(prefix="/restrictions", tags=["restrictions"])


@router.get("/suggestions", response_model=RestrictionSuggestionListResponse)
async def get_restriction_suggestions(
    database=Depends(get_database),
) -> RestrictionSuggestionListResponse:
    service = RestrictionService(RestrictionRepository(database))
    suggestions = await service.get_popular_suggestions()
    return RestrictionSuggestionListResponse(suggestions=suggestions)


@router.post("/custom", response_model=CustomRestrictionResponse)
async def add_custom_restriction(
    payload: CustomRestrictionCreate,
    database=Depends(get_database),
) -> CustomRestrictionResponse:
    service = RestrictionService(RestrictionRepository(database))
    return await service.add_custom_restriction(payload)
