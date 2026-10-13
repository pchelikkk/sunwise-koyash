from fastapi import APIRouter

from app.schemas.skin_diagnosis import SkinDiagnosisRequest, SkinDiagnosisResponse
from app.services.skin_diagnosis_service import SkinDiagnosisService

router = APIRouter(prefix="/skin-diagnosis", tags=["skin diagnosis"])


@router.post("", response_model=SkinDiagnosisResponse)
async def diagnose_skin(payload: SkinDiagnosisRequest) -> SkinDiagnosisResponse:
    return SkinDiagnosisService().diagnose(payload)
