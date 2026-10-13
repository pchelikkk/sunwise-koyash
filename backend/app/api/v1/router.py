from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_analytics,
    admin_catalog,
    analytics,
    auth,
    feedback,
    health,
    llm_explanations,
    products,
    questionnaire,
    recommendations,
    replacements,
    restrictions,
    skin_diagnosis,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(questionnaire.router)
api_router.include_router(restrictions.router)
api_router.include_router(skin_diagnosis.router)
api_router.include_router(products.router)
api_router.include_router(recommendations.router)
api_router.include_router(feedback.router)
api_router.include_router(replacements.router)
api_router.include_router(analytics.router)
api_router.include_router(admin_analytics.router)
api_router.include_router(admin_catalog.router)
api_router.include_router(llm_explanations.router)
