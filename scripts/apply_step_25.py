from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


write_file("backend/app/schemas/feedback.py", r'''
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.replacement import ReplacementCandidate


FeedbackReason = Literal[
    "too_expensive",
    "dislikes_brand",
    "composition_concern",
    "texture_not_suitable",
    "too_many_steps",
    "other",
]


class FeedbackCreate(BaseModel):
    product_external_id: str = Field(min_length=1)
    reason: FeedbackReason
    comment: str | None = Field(default=None, max_length=500)
    anonymous_id: str | None = Field(default=None, max_length=120)


class FeedbackResponse(BaseModel):
    feedback_id: str
    recommendation_id: str
    product_external_id: str
    routine_step: str
    reason: str
    comment: str | None = None
    created_at: datetime


class FeedbackWithReplacementsResponse(BaseModel):
    feedback: FeedbackResponse
    replacement_session_id: str
    replacement_strategy: str
    replacement_candidates: list[ReplacementCandidate]
''')


write_file("backend/app/schemas/replacement.py", r'''
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class ReplacementCandidate(BaseModel):
    product: ProductResponse
    score: int
    why_better: str
    strategy_reason: str


class ReplacementSessionResponse(BaseModel):
    replacement_session_id: str
    recommendation_id: str
    feedback_id: str
    original_product_external_id: str
    strategy: str
    candidates: list[ReplacementCandidate] = Field(default_factory=list)
    selected_product_external_id: str | None = None
    created_at: datetime


class ReplacementSessionListResponse(BaseModel):
    replacements: list[ReplacementSessionResponse]


class ReplacementSelectRequest(BaseModel):
    product_external_id: str


class ReplacementSelectionResponse(BaseModel):
    replacement_session_id: str
    selected_product_external_id: str
    status: str = "selected"
''')


write_file("backend/app/repositories/feedback_repository.py", r'''
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


class FeedbackRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["feedback_events"]

    async def save_feedback(
        self,
        recommendation_id: str,
        product_external_id: str,
        routine_step: str,
        reason: str,
        comment: str | None,
        anonymous_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        created_at = utc_now()

        document = {
            "recommendation_id": recommendation_id,
            "product_external_id": product_external_id,
            "routine_step": routine_step,
            "reason": reason,
            "comment": comment,
            "anonymous_id": anonymous_id,
            "user_id": user_id,
            "created_at": created_at,
        }

        result = await self.collection.insert_one(document)

        return {
            "feedback_id": str(result.inserted_id),
            **document,
        }

    async def find_by_id(self, feedback_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"_id": ObjectId(feedback_id)})

        if document is None:
            return None

        document["feedback_id"] = str(document.pop("_id"))
        return document
''')


write_file("backend/app/repositories/replacement_repository.py", r'''
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


class ReplacementRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["replacement_sessions"]

    async def save_replacement_session(
        self,
        feedback_id: str,
        recommendation_id: str,
        original_product_external_id: str,
        strategy: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        created_at = utc_now()

        document = {
            "feedback_id": feedback_id,
            "recommendation_id": recommendation_id,
            "original_product_external_id": original_product_external_id,
            "strategy": strategy,
            "candidates": candidates,
            "selected_product_external_id": None,
            "created_at": created_at,
        }

        result = await self.collection.insert_one(document)

        return {
            "replacement_session_id": str(result.inserted_id),
            **document,
        }

    async def list_by_recommendation_id(self, recommendation_id: str) -> list[dict[str, Any]]:
        cursor = (
            self.collection.find({"recommendation_id": recommendation_id})
            .sort("created_at", DESCENDING)
        )

        sessions: list[dict[str, Any]] = []

        async for document in cursor:
            document["replacement_session_id"] = str(document.pop("_id"))
            sessions.append(document)

        return sessions

    async def find_by_id(self, replacement_session_id: str) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(replacement_session_id)
        except InvalidId:
            return None

        document = await self.collection.find_one({"_id": object_id})

        if document is None:
            return None

        document["replacement_session_id"] = str(document.pop("_id"))
        return document

    async def select_candidate(
        self,
        replacement_session_id: str,
        product_external_id: str,
    ) -> bool:
        try:
            object_id = ObjectId(replacement_session_id)
        except InvalidId:
            return False

        result = await self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "selected_product_external_id": product_external_id,
                    "selected_at": utc_now(),
                }
            },
        )

        return result.modified_count == 1
''')


write_file("backend/app/algorithms/replacement_strategy.py", r'''
from app.algorithms.filters import apply_hard_filters
from app.algorithms.scoring import ScoredProduct, score_products
from app.algorithms.sorting import sort_scored_products
from app.schemas.recommendation import RecommendationRequest


STRATEGY_BY_REASON = {
    "too_expensive": "cheaper_same_step",
    "dislikes_brand": "different_brand_same_step",
    "composition_concern": "safer_formula_same_step",
    "texture_not_suitable": "different_texture_same_step",
    "too_many_steps": "routine_simplification",
    "other": "best_alternative_same_step",
}


def strategy_for_reason(reason: str) -> str:
    return STRATEGY_BY_REASON.get(reason, "best_alternative_same_step")


def _same_step_candidates(
    products: list[dict],
    original_product: dict,
) -> list[dict]:
    original_external_id = original_product.get("external_id")
    original_step = original_product.get("routine_step")

    return [
        product
        for product in products
        if product.get("external_id") != original_external_id
        and product.get("routine_step") == original_step
    ]


def _filter_by_reason(
    candidates: list[dict],
    original_product: dict,
    reason: str,
) -> list[dict]:
    if reason == "too_expensive":
        cheaper = [
            product
            for product in candidates
            if product.get("price_rub", 0) < original_product.get("price_rub", 0)
        ]
        return cheaper or candidates

    if reason == "dislikes_brand":
        different_brand = [
            product
            for product in candidates
            if product.get("brand") != original_product.get("brand")
        ]
        return different_brand or candidates

    if reason == "composition_concern":
        safer = [
            product
            for product in candidates
            if not product.get("risk_flags")
            and (
                "fragrance_free" in product.get("ingredient_flags", [])
                or "alcohol_free" in product.get("ingredient_flags", [])
            )
        ]
        return safer or candidates

    if reason == "texture_not_suitable":
        different_texture = [
            product
            for product in candidates
            if product.get("texture") != original_product.get("texture")
        ]
        return different_texture or candidates

    if reason == "too_many_steps":
        return []

    return candidates


def _why_better(
    candidate: dict,
    original_product: dict,
    reason: str,
) -> str:
    if reason == "too_expensive":
        if candidate.get("price_rub", 0) < original_product.get("price_rub", 0):
            return "Эта замена закрывает тот же шаг рутины, но стоит дешевле."
        return "Это ближайшая альтернатива для того же шага рутины."

    if reason == "dislikes_brand":
        return "Это средство закрывает тот же шаг рутины, но относится к другому бренду."

    if reason == "composition_concern":
        return "Это более мягкая альтернатива с меньшим количеством риск-флагов."

    if reason == "texture_not_suitable":
        return "Это средство закрывает тот же шаг рутины, но имеет другую текстуру."

    if reason == "too_many_steps":
        return "Для этой причины лучше не заменять продукт, а упростить рутину."

    return "Это ближайшая подходящая альтернатива для того же шага рутины."


def _strategy_reason(reason: str) -> str:
    if reason == "too_expensive":
        return "Пользователь отметил цену, поэтому приоритет — более доступные средства."
    if reason == "dislikes_brand":
        return "Пользователь отметил бренд, поэтому приоритет — альтернативный бренд."
    if reason == "composition_concern":
        return "Пользователь сомневается в составе, поэтому приоритет — более мягкая формула."
    if reason == "texture_not_suitable":
        return "Пользователь отметил текстуру, поэтому приоритет — другая текстура."
    if reason == "too_many_steps":
        return "Пользователь отметил сложность, поэтому нужна не замена продукта, а сокращение рутины."
    return "Подбирается лучшая доступная альтернатива по тому же шагу рутины."


def build_replacement_candidates(
    products: list[dict],
    original_product: dict,
    request: RecommendationRequest,
    reason: str,
    limit: int = 3,
) -> list[dict]:
    filter_result = apply_hard_filters(products=products, request=request)

    candidates = _same_step_candidates(
        products=filter_result.allowed_products,
        original_product=original_product,
    )
    candidates = _filter_by_reason(
        candidates=candidates,
        original_product=original_product,
        reason=reason,
    )

    scored = score_products(candidates, request)
    sorted_candidates = sort_scored_products(scored)

    result: list[dict] = []

    for item in sorted_candidates[:limit]:
        result.append(
            {
                "product": item.product,
                "score": item.score.total,
                "why_better": _why_better(
                    candidate=item.product,
                    original_product=original_product,
                    reason=reason,
                ),
                "strategy_reason": _strategy_reason(reason),
            }
        )

    return result
''')


write_file("backend/app/services/replacement_service.py", r'''
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.replacement import (
    ReplacementCandidate,
    ReplacementSelectionResponse,
    ReplacementSessionListResponse,
    ReplacementSessionResponse,
)


class ReplacementService:
    def __init__(self, replacement_repository: ReplacementRepository) -> None:
        self.replacement_repository = replacement_repository

    async def list_replacements(
        self,
        recommendation_id: str,
    ) -> ReplacementSessionListResponse:
        documents = await self.replacement_repository.list_by_recommendation_id(recommendation_id)

        return ReplacementSessionListResponse(
            replacements=[
                ReplacementSessionResponse(
                    replacement_session_id=document["replacement_session_id"],
                    recommendation_id=document["recommendation_id"],
                    feedback_id=document["feedback_id"],
                    original_product_external_id=document["original_product_external_id"],
                    strategy=document["strategy"],
                    candidates=[
                        ReplacementCandidate(**candidate)
                        for candidate in document.get("candidates", [])
                    ],
                    selected_product_external_id=document.get("selected_product_external_id"),
                    created_at=document["created_at"],
                )
                for document in documents
            ]
        )

    async def select_replacement(
        self,
        replacement_session_id: str,
        product_external_id: str,
    ) -> ReplacementSelectionResponse | None:
        session = await self.replacement_repository.find_by_id(replacement_session_id)

        if session is None:
            return None

        candidate_ids = {
            candidate["product"]["external_id"]
            for candidate in session.get("candidates", [])
        }

        if product_external_id not in candidate_ids:
            return None

        selected = await self.replacement_repository.select_candidate(
            replacement_session_id=replacement_session_id,
            product_external_id=product_external_id,
        )

        if not selected:
            return None

        return ReplacementSelectionResponse(
            replacement_session_id=replacement_session_id,
            selected_product_external_id=product_external_id,
        )
''')


write_file("backend/app/services/feedback_service.py", r'''
from app.algorithms.normalizer import normalized_request
from app.algorithms.replacement_strategy import (
    build_replacement_candidates,
    strategy_for_reason,
)
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackWithReplacementsResponse,
)
from app.schemas.recommendation import RecommendationRequest
from app.schemas.replacement import ReplacementCandidate


class FeedbackService:
    def __init__(
        self,
        feedback_repository: FeedbackRepository,
        replacement_repository: ReplacementRepository,
        recommendation_repository: RecommendationRepository,
        product_repository: ProductRepository,
    ) -> None:
        self.feedback_repository = feedback_repository
        self.replacement_repository = replacement_repository
        self.recommendation_repository = recommendation_repository
        self.product_repository = product_repository

    async def submit_feedback(
        self,
        recommendation_id: str,
        payload: FeedbackCreate,
    ) -> FeedbackWithReplacementsResponse | None:
        recommendation = await self.recommendation_repository.find_by_id(recommendation_id)

        if recommendation is None:
            return None

        original_product = await self.product_repository.find_by_external_id(
            payload.product_external_id
        )

        if original_product is None:
            return None

        request = normalized_request(RecommendationRequest(**recommendation["request"]))
        products = await self.product_repository.list_active_products()

        feedback = await self.feedback_repository.save_feedback(
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            routine_step=original_product.get("routine_step", ""),
            reason=payload.reason,
            comment=payload.comment,
            anonymous_id=payload.anonymous_id or request.anonymous_id,
        )

        replacement_strategy = strategy_for_reason(payload.reason)

        candidate_documents = build_replacement_candidates(
            products=products,
            original_product=original_product,
            request=request,
            reason=payload.reason,
        )

        replacement_session = await self.replacement_repository.save_replacement_session(
            feedback_id=feedback["feedback_id"],
            recommendation_id=recommendation_id,
            original_product_external_id=payload.product_external_id,
            strategy=replacement_strategy,
            candidates=candidate_documents,
        )

        return FeedbackWithReplacementsResponse(
            feedback=FeedbackResponse(**feedback),
            replacement_session_id=replacement_session["replacement_session_id"],
            replacement_strategy=replacement_strategy,
            replacement_candidates=[
                ReplacementCandidate(**candidate)
                for candidate in candidate_documents
            ],
        )
''')


write_file("backend/app/api/v1/endpoints/feedback.py", r'''
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.mongodb import get_database
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.feedback import FeedbackCreate, FeedbackWithReplacementsResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(tags=["feedback"])


def get_feedback_service(database=Depends(get_database)) -> FeedbackService:
    return FeedbackService(
        feedback_repository=FeedbackRepository(database),
        replacement_repository=ReplacementRepository(database),
        recommendation_repository=RecommendationRepository(database),
        product_repository=ProductRepository(database),
    )


@router.post(
    "/recommendations/{recommendation_id}/feedback",
    response_model=FeedbackWithReplacementsResponse,
)
async def submit_feedback(
    recommendation_id: str,
    payload: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackWithReplacementsResponse:
    result = await service.submit_feedback(
        recommendation_id=recommendation_id,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation or product not found",
        )

    return result
''')


write_file("backend/app/api/v1/endpoints/replacements.py", r'''
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.mongodb import get_database
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.replacement import (
    ReplacementSelectRequest,
    ReplacementSelectionResponse,
    ReplacementSessionListResponse,
)
from app.services.replacement_service import ReplacementService

router = APIRouter(tags=["replacements"])


def get_replacement_service(database=Depends(get_database)) -> ReplacementService:
    return ReplacementService(
        replacement_repository=ReplacementRepository(database),
    )


@router.get(
    "/recommendations/{recommendation_id}/replacements",
    response_model=ReplacementSessionListResponse,
)
async def list_replacements(
    recommendation_id: str,
    service: ReplacementService = Depends(get_replacement_service),
) -> ReplacementSessionListResponse:
    return await service.list_replacements(recommendation_id=recommendation_id)


@router.post(
    "/recommendations/{recommendation_id}/replacements/{replacement_session_id}/select",
    response_model=ReplacementSelectionResponse,
)
async def select_replacement(
    recommendation_id: str,
    replacement_session_id: str,
    payload: ReplacementSelectRequest,
    service: ReplacementService = Depends(get_replacement_service),
) -> ReplacementSelectionResponse:
    result = await service.select_replacement(
        replacement_session_id=replacement_session_id,
        product_external_id=payload.product_external_id,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replacement session or candidate not found",
        )

    return result
''')


write_file("backend/app/api/v1/router.py", r'''
from fastapi import APIRouter

from app.api.v1.endpoints import (
    feedback,
    health,
    products,
    questionnaire,
    recommendations,
    replacements,
    restrictions,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(questionnaire.router)
api_router.include_router(restrictions.router)
api_router.include_router(products.router)
api_router.include_router(recommendations.router)
api_router.include_router(feedback.router)
api_router.include_router(replacements.router)
''')


write_file("backend/tests/test_feedback_replacements.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def _recommendation_payload() -> dict:
    return {
        "skin_type": "combination",
        "concerns": ["acne", "sebum"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "basic",
        "values": ["comfort", "price_quality"],
        "anonymous_id": "test-feedback-anon",
    }


def _create_recommendation(client: TestClient) -> str:
    response = client.post("/api/v1/recommendations", json=_recommendation_payload())
    assert response.status_code == 200
    return response.json()["recommendation_id"]


def test_feedback_returns_replacement_candidates() -> None:
    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)

        response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
                "comment": "Хочу дешевле",
                "anonymous_id": "test-feedback-anon",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["feedback"]["recommendation_id"] == recommendation_id
    assert payload["feedback"]["product_external_id"] == "cleanser_001"
    assert payload["feedback"]["reason"] == "too_expensive"
    assert payload["replacement_strategy"] == "cheaper_same_step"
    assert payload["replacement_session_id"]
    assert payload["replacement_candidates"]

    first_candidate = payload["replacement_candidates"][0]
    assert first_candidate["product"]["routine_step"] == "cleanser"
    assert first_candidate["product"]["external_id"] != "cleanser_001"
    assert first_candidate["why_better"]
    assert first_candidate["strategy_reason"]


def test_replacements_can_be_listed_after_feedback() -> None:
    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)

        feedback_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
            },
        )
        assert feedback_response.status_code == 200

        list_response = client.get(
            f"/api/v1/recommendations/{recommendation_id}/replacements"
        )

    assert list_response.status_code == 200

    payload = list_response.json()
    assert payload["replacements"]
    assert payload["replacements"][0]["recommendation_id"] == recommendation_id
    assert payload["replacements"][0]["candidates"]


def test_replacement_candidate_can_be_selected() -> None:
    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)

        feedback_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
            },
        )
        assert feedback_response.status_code == 200

        feedback_payload = feedback_response.json()
        replacement_session_id = feedback_payload["replacement_session_id"]
        candidate_id = feedback_payload["replacement_candidates"][0]["product"]["external_id"]

        select_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/replacements/{replacement_session_id}/select",
            json={"product_external_id": candidate_id},
        )

    assert select_response.status_code == 200

    payload = select_response.json()
    assert payload["replacement_session_id"] == replacement_session_id
    assert payload["selected_product_external_id"] == candidate_id
    assert payload["status"] == "selected"


def test_feedback_unknown_recommendation_returns_404() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations/000000000000000000000000/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
            },
        )

    assert response.status_code == 404
''')


write_file(".gitlab-ci.yml", r'''
stages:
  - test

backend-tests:
  stage: test
  image: python:3.12-slim

  services:
    - name: mongo:7
      alias: mongo
      command: ["--quiet"]

  variables:
    APP_NAME: "KOYASH API"
    APP_ENV: "test"
    API_V1_PREFIX: "/api/v1"

    MONGO_INITDB_ROOT_USERNAME: "koyash"
    MONGO_INITDB_ROOT_PASSWORD: "koyash_dev_password"
    MONGO_INITDB_DATABASE: "koyash_test"

    MONGO_URI: "mongodb://koyash:koyash_dev_password@mongo:27017/?authSource=admin"
    MONGO_DB_NAME: "koyash_test"

    CORS_ORIGINS: "http://localhost:5173,http://127.0.0.1:5173"
    JWT_SECRET_KEY: "test_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: "60"
    ANALYTICS_RAW_EVENT_TTL_DAYS: "30"

    PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
    PIP_DISABLE_PIP_VERSION_CHECK: "1"

  cache:
    paths:
      - .cache/pip

  before_script:
    - cd backend
    - python --version
    - python -m pip --version
    - python -m pip install --no-cache-dir -r requirements.txt

  script:
    - pytest tests/test_health.py tests/test_questionnaire.py tests/test_restrictions.py tests/test_products.py tests/test_recommendations.py tests/test_feedback_replacements.py
''')


write_file("docs/feedback-replacement-flow.md", r'''
# KOYASH Feedback and Replacement Flow

## Purpose

The feedback flow is not just a form. It is a product loop:

1. The user marks a recommended product as unsuitable.
2. The backend stores feedback.
3. The backend interprets the reason.
4. The backend generates replacement candidates.
5. The user can select a replacement.
6. The data can later be used for analytics and dashboard charts.

## Feedback reasons

- `too_expensive`
- `dislikes_brand`
- `composition_concern`
- `texture_not_suitable`
- `too_many_steps`
- `other`

## Replacement strategies

| Reason | Strategy |
|---|---|
| `too_expensive` | cheaper same-step product |
| `dislikes_brand` | same-step product from another brand |
| `composition_concern` | safer or softer formula |
| `texture_not_suitable` | same-step product with another texture |
| `too_many_steps` | future routine simplification |
| `other` | best alternative for the same routine step |

## API

```text
POST /api/v1/recommendations/{recommendation_id}/feedback
GET  /api/v1/recommendations/{recommendation_id}/replacements
POST /api/v1/recommendations/{recommendation_id}/replacements/{replacement_session_id}/select
''')

print("Step 2.5 feedback-aware replacements files written successfully.")