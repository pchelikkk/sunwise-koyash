from app.algorithms.skin_diagnosis import diagnose_skin_type
from app.schemas.skin_diagnosis import SkinDiagnosisRequest, SkinDiagnosisResponse


class SkinDiagnosisService:
    def diagnose(self, payload: SkinDiagnosisRequest) -> SkinDiagnosisResponse:
        result = diagnose_skin_type(payload)
        return SkinDiagnosisResponse(**result.model_dump())
