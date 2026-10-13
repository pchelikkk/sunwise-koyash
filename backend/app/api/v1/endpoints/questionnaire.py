from fastapi import APIRouter, Depends

from app.db.mongodb import get_database
from app.repositories.restriction_repository import RestrictionRepository
from app.schemas.questionnaire import QuestionnaireResponse
from app.services.questionnaire_service import QuestionnaireService
from app.services.restriction_service import RestrictionService

router = APIRouter(tags=["questionnaire"])


@router.get("/questionnaire", response_model=QuestionnaireResponse)
async def get_questionnaire(database=Depends(get_database)) -> QuestionnaireResponse:
    restriction_service = RestrictionService(RestrictionRepository(database))
    restriction_suggestions = await restriction_service.get_popular_suggestions()

    service = QuestionnaireService()
    return service.get_questionnaire(restriction_suggestions=restriction_suggestions)
