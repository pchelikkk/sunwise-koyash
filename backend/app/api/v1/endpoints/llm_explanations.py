from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.llm import (
    LLMDemoPayloadsResponse,
    LLMExplanationPreviewRequest,
    LLMExplanationPreviewResponse,
)
from app.services.event_tracking_service import EventTrackingService
from app.services.llm_explanation_service import LLMExplanationService

router = APIRouter(prefix="/llm/explanations", tags=["llm explanations"])


def get_llm_explanation_service(database=Depends(get_database)) -> LLMExplanationService:
    return LLMExplanationService(
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
    )


@router.get("/demo-payloads", response_model=LLMDemoPayloadsResponse)
async def demo_payloads() -> LLMDemoPayloadsResponse:
    service = LLMExplanationService()
    return LLMDemoPayloadsResponse(payloads=service.demo_payloads())


@router.post("/preview", response_model=LLMExplanationPreviewResponse)
async def preview_explanation(
    payload: LLMExplanationPreviewRequest,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    service: Annotated[LLMExplanationService, Depends(get_llm_explanation_service)],
) -> LLMExplanationPreviewResponse:
    return await service.preview(
        payload,
        user_id=current_user["user_id"] if current_user is not None else None,
        anonymous_id=(
            current_user.get("anonymous_id") if current_user is not None else None
        ),
    )
