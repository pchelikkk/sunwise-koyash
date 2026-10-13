from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


write_file("backend/app/schemas/recommendation.py", r'''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class RecommendationRequest(BaseModel):
    skin_type: str
    concerns: list[str] = Field(default_factory=list)
    budget: str = "balanced"
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str = "beginner"
    values: list[str] = Field(default_factory=list)
    anonymous_id: str | None = None


class ScoreBreakdown(BaseModel):
    routine_step_score: int = 0
    concern_score: int = 0
    skin_type_score: int = 0
    budget_score: int = 0
    experience_score: int = 0
    safety_score: int = 0
    values_score: int = 0
    penalties: int = 0
    total: int = 0


class RecommendedProduct(BaseModel):
    routine_step: str
    product: ProductResponse
    score: int
    score_breakdown: ScoreBreakdown
    why_here: str
    matched_concerns: list[str] = Field(default_factory=list)
    budget_reason: str
    safety_note: str
    how_to_use: str
    llm_ready_context: dict[str, Any] = Field(default_factory=dict)


class RecommendationRoutine(BaseModel):
    morning: list[RecommendedProduct] = Field(default_factory=list)
    evening: list[RecommendedProduct] = Field(default_factory=list)


class FilterSummary(BaseModel):
    total_products: int
    allowed_products: int
    filtered_out: int
    filter_reasons: dict[str, int] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    recommendation_id: str
    algorithm_version: str
    routine: RecommendationRoutine
    filter_summary: FilterSummary
    total_price_rub: int
    created_at: datetime
''')


write_file("backend/app/algorithms/normalizer.py", r'''
from app.schemas.recommendation import RecommendationRequest


RESTRICTION_ALIASES = {
    "отдушка": "fragrance",
    "отдушки": "fragrance",
    "ароматизатор": "fragrance",
    "ароматизаторы": "fragrance",
    "fragrance": "fragrance",
    "parfum": "fragrance",
    "perfume": "fragrance",
    "спирт": "alcohol",
    "алкоголь": "alcohol",
    "alcohol": "alcohol",
    "ethanol": "alcohol",
    "этанол": "alcohol",
    "ethyl alcohol": "alcohol",
    "эфирные масла": "essential_oils",
    "эфирное масло": "essential_oils",
    "essential oils": "essential_oils",
    "essential oil": "essential_oils",
    "нет ограничений": "none",
    "ничего": "none",
    "none": "none",
    "no restrictions": "none",
}


def normalize_text(value: str) -> str:
    return value.strip().lower().replace("ё", "е")


def normalize_restriction(value: str) -> str:
    normalized = normalize_text(value)
    return RESTRICTION_ALIASES.get(normalized, normalized)


def normalize_values(values: list[str]) -> list[str]:
    result = []
    for value in values:
        normalized = normalize_text(value)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def normalize_restrictions(values: list[str]) -> list[str]:
    result = []
    for value in values:
        normalized = normalize_restriction(value)
        if normalized and normalized != "none" and normalized not in result:
            result.append(normalized)
    return result


def normalized_request(request: RecommendationRequest) -> RecommendationRequest:
    return RecommendationRequest(
        skin_type=normalize_text(request.skin_type),
        concerns=normalize_values(request.concerns),
        budget=normalize_text(request.budget),
        excluded_ingredients=normalize_restrictions(request.excluded_ingredients),
        custom_restrictions=normalize_restrictions(request.custom_restrictions),
        experience=normalize_text(request.experience),
        values=normalize_values(request.values),
        anonymous_id=request.anonymous_id,
    )


def product_tokens(product: dict) -> set[str]:
    values: list[str] = []

    for key in ["ingredients", "ingredient_flags", "risk_flags"]:
        values.extend(product.get(key, []))

    values.extend(
        [
            product.get("category", ""),
            product.get("routine_step", ""),
            product.get("texture", "") or "",
        ]
    )

    return {normalize_restriction(value) for value in values if value}
''')


write_file("backend/app/algorithms/filters.py", r'''
from collections import Counter
from dataclasses import dataclass

from app.algorithms.normalizer import product_tokens
from app.schemas.recommendation import RecommendationRequest


@dataclass(frozen=True)
class FilterResult:
    allowed_products: list[dict]
    filter_reasons: dict[str, int]


def _matches_restriction(restriction: str, product: dict, tokens: set[str]) -> bool:
    ingredients = {item.strip().lower() for item in product.get("ingredients", [])}
    risk_flags = {item.strip().lower() for item in product.get("risk_flags", [])}

    if restriction in tokens:
        return True

    if restriction == "fragrance":
        return "fragrance" in ingredients or "parfum" in ingredients or "contains_fragrance" in risk_flags

    if restriction == "alcohol":
        return "alcohol" in ingredients or "ethanol" in ingredients or "ethyl alcohol" in ingredients

    if restriction == "essential_oils":
        return "essential oil" in ingredients or "essential oils" in ingredients

    return False


def apply_hard_filters(
    products: list[dict],
    request: RecommendationRequest,
) -> FilterResult:
    allowed: list[dict] = []
    reasons: Counter[str] = Counter()

    restrictions = set(request.excluded_ingredients + request.custom_restrictions)

    for product in products:
        if not product.get("is_active", True):
            reasons["inactive"] += 1
            continue

        tokens = product_tokens(product)

        if any(_matches_restriction(restriction, product, tokens) for restriction in restrictions):
            reasons["excluded_ingredient"] += 1
            continue

        risk_flags = set(product.get("risk_flags", []))

        if request.skin_type == "sensitive" and risk_flags:
            reasons["sensitive_risk"] += 1
            continue

        if request.experience in {"beginner", "minimal"} and "active_formula" in risk_flags:
            reasons["beginner_safety"] += 1
            continue

        if request.budget == "minimum" and product.get("price_rub", 0) > 1200:
            reasons["budget_hard_cap"] += 1
            continue

        allowed.append(product)

    return FilterResult(allowed_products=allowed, filter_reasons=dict(reasons))
''')


write_file("backend/app/algorithms/scoring.py", r'''
from dataclasses import dataclass

from app.schemas.recommendation import RecommendationRequest, ScoreBreakdown


@dataclass(frozen=True)
class ScoredProduct:
    product: dict
    score: ScoreBreakdown


def _budget_score(user_budget: str, product_budget: str) -> tuple[int, int]:
    if user_budget == product_budget:
        return 15, 3

    if user_budget == "balanced" and product_budget in {"minimum", "balanced"}:
        return 12, 2

    if user_budget == "premium" and product_budget in {"balanced", "premium"}:
        return 10, 1

    if user_budget == "minimum" and product_budget == "balanced":
        return 5, 0

    return 0, -1


def score_product(product: dict, request: RecommendationRequest) -> ScoreBreakdown:
    product_concerns = set(product.get("concerns", []))
    user_concerns = set(request.concerns)

    matched_concerns = product_concerns.intersection(user_concerns)

    routine_step_score = 30
    concern_score = min(25, len(matched_concerns) * 12)
    skin_type_score = 20 if request.skin_type in product.get("skin_types", []) else 0

    budget_score, budget_match_score = _budget_score(
        user_budget=request.budget,
        product_budget=product.get("budget_segment", ""),
    )

    risk_flags = set(product.get("risk_flags", []))
    ingredient_flags = set(product.get("ingredient_flags", []))

    experience_score = 0
    penalties = 0

    if request.experience in {"beginner", "minimal"}:
        if not risk_flags:
            experience_score += 10
        else:
            penalties -= 20

    if request.experience == "advanced" and product.get("routine_step") == "treatment":
        experience_score += 8

    safety_score = 0
    if "fragrance_free" in ingredient_flags:
        safety_score += 5
    if "alcohol_free" in ingredient_flags:
        safety_score += 5
    if request.skin_type == "sensitive" and not risk_flags:
        safety_score += 8

    values_score = 0
    if "soft_formula" in request.values and not risk_flags:
        values_score += 5
    if "price_quality" in request.values and product.get("budget_segment") in {"minimum", "balanced"}:
        values_score += 5
    if "comfort" in request.values and product.get("texture") in {"cream", "light cream", "gel", "light serum"}:
        values_score += 3

    if request.budget == "minimum" and product.get("budget_segment") == "premium":
        penalties -= 20

    total = (
        routine_step_score
        + concern_score
        + skin_type_score
        + budget_score
        + experience_score
        + safety_score
        + values_score
        + penalties
    )

    return ScoreBreakdown(
        routine_step_score=routine_step_score,
        concern_score=concern_score,
        skin_type_score=skin_type_score,
        budget_score=budget_score,
        experience_score=experience_score,
        safety_score=safety_score,
        values_score=values_score,
        penalties=penalties,
        total=total,
    )


def score_products(products: list[dict], request: RecommendationRequest) -> list[ScoredProduct]:
    return [
        ScoredProduct(product=product, score=score_product(product, request))
        for product in products
    ]
''')


write_file("backend/app/algorithms/sorting.py", r'''
from app.algorithms.scoring import ScoredProduct


def sort_scored_products(products: list[ScoredProduct]) -> list[ScoredProduct]:
    return sorted(
        products,
        key=lambda item: (
            -item.score.total,
            -item.score.budget_score,
            item.product.get("price_rub", 0),
            item.product.get("external_id", ""),
        ),
    )
''')


write_file("backend/app/algorithms/explanation_context.py", r'''
from typing import Any

from app.algorithms.scoring import ScoredProduct
from app.schemas.recommendation import RecommendationRequest


CONCERN_LABELS = {
    "acne": "высыпания",
    "sebum": "жирный блеск",
    "dryness": "сухость",
    "post_acne": "постакне",
    "uneven_tone": "неровный тон",
    "sensitivity": "чувствительность",
    "age_changes": "возрастные изменения",
    "unknown": "пока не знаю",
}


def matched_concern_labels(product: dict, request: RecommendationRequest) -> list[str]:
    matched = set(product.get("concerns", [])).intersection(set(request.concerns))
    return [CONCERN_LABELS.get(item, item) for item in sorted(matched)]


def build_llm_context(
    item: ScoredProduct,
    request: RecommendationRequest,
    why_here: str,
    safety_note: str,
) -> dict[str, Any]:
    product = item.product

    return {
        "tone": "warm, caring, simple, KOYASH voice: бабушка + ИИ",
        "instruction": "Rewrite only the explanation text. Do not change product facts or safety filters.",
        "user_profile": {
            "skin_type": request.skin_type,
            "concerns": request.concerns,
            "budget": request.budget,
            "experience": request.experience,
            "values": request.values,
            "excluded_ingredients": request.excluded_ingredients + request.custom_restrictions,
        },
        "product_facts": {
            "external_id": product.get("external_id"),
            "name": product.get("name"),
            "brand": product.get("brand"),
            "routine_step": product.get("routine_step"),
            "price_rub": product.get("price_rub"),
            "ingredients": product.get("ingredients", []),
            "ingredient_flags": product.get("ingredient_flags", []),
            "risk_flags": product.get("risk_flags", []),
        },
        "deterministic_explanation": {
            "why_here": why_here,
            "safety_note": safety_note,
            "score_breakdown": item.score.model_dump(),
        },
    }
''')


write_file("backend/app/services/explanation_service.py", r'''
from app.algorithms.explanation_context import build_llm_context, matched_concern_labels
from app.algorithms.scoring import ScoredProduct
from app.schemas.product import ProductResponse
from app.schemas.recommendation import RecommendationRequest, RecommendedProduct


ROUTINE_STEP_LABELS = {
    "cleanser": "очищение",
    "serum": "сыворотка",
    "treatment": "активный уход",
    "moisturizer": "крем",
    "spf": "SPF",
}


class ExplanationService:
    def build_recommended_product(
        self,
        item: ScoredProduct,
        request: RecommendationRequest,
    ) -> RecommendedProduct:
        product = item.product
        matched_concerns = matched_concern_labels(product, request)
        routine_step_label = ROUTINE_STEP_LABELS.get(product.get("routine_step"), product.get("routine_step"))

        if matched_concerns:
            concerns_text = ", ".join(matched_concerns)
            why_here = (
                f"Это средство закрывает шаг «{routine_step_label}» и подходит под задачи: "
                f"{concerns_text}."
            )
        else:
            why_here = (
                f"Это средство закрывает базовый шаг «{routine_step_label}» и помогает собрать "
                "полную, понятную рутину без лишней сложности."
            )

        if request.budget == product.get("budget_segment"):
            budget_reason = "Средство попадает в выбранный бюджетный сегмент."
        elif request.budget == "balanced" and product.get("budget_segment") == "minimum":
            budget_reason = "Средство немного доступнее выбранного бюджета, поэтому помогает не перегрузить косметичку."
        else:
            budget_reason = "Средство не идеально совпадает с бюджетом, но прошло фильтры и набрало высокий score."

        risk_flags = product.get("risk_flags", [])
        ingredient_flags = product.get("ingredient_flags", [])

        if not risk_flags:
            safety_note = "В карточке нет явных риск-флагов для выбранного профиля."
        elif "active_formula" in risk_flags:
            safety_note = "Это активная формула, её лучше вводить постепенно и отслеживать реакцию кожи."
        else:
            safety_note = "Есть особенности состава, поэтому средство стоит вводить аккуратно."

        if "fragrance_free" in ingredient_flags:
            safety_note += " Отмечено как средство без отдушек."
        if "alcohol_free" in ingredient_flags:
            safety_note += " Отмечено как средство без спирта."

        llm_ready_context = build_llm_context(
            item=item,
            request=request,
            why_here=why_here,
            safety_note=safety_note,
        )

        return RecommendedProduct(
            routine_step=product["routine_step"],
            product=ProductResponse(**product),
            score=item.score.total,
            score_breakdown=item.score,
            why_here=why_here,
            matched_concerns=matched_concerns,
            budget_reason=budget_reason,
            safety_note=safety_note,
            how_to_use=product.get("how_to_use", ""),
            llm_ready_context=llm_ready_context,
        )
''')


write_file("backend/app/algorithms/routine_builder.py", r'''
from app.algorithms.scoring import ScoredProduct


def _best_by_step(products: list[ScoredProduct], step: str) -> ScoredProduct | None:
    for product in products:
        if product.product.get("routine_step") == step:
            return product
    return None


def build_routine(products: list[ScoredProduct], experience: str) -> dict[str, list[ScoredProduct]]:
    cleanser = _best_by_step(products, "cleanser")
    serum = _best_by_step(products, "serum")
    treatment = _best_by_step(products, "treatment")
    moisturizer = _best_by_step(products, "moisturizer")
    spf = _best_by_step(products, "spf")

    morning: list[ScoredProduct] = []
    evening: list[ScoredProduct] = []

    if cleanser is not None:
        morning.append(cleanser)
        evening.append(cleanser)

    if spf is not None:
        morning.append(spf)

    if experience in {"advanced", "basic"} and treatment is not None:
        evening.append(treatment)
    elif serum is not None:
        evening.append(serum)
    elif treatment is not None:
        evening.append(treatment)

    if moisturizer is not None:
        evening.append(moisturizer)

    return {
        "morning": morning,
        "evening": evening,
    }
''')


write_file("backend/app/repositories/recommendation_repository.py", r'''
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


class RecommendationRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["recommendation_sessions"]

    async def save_session(
        self,
        request: dict[str, Any],
        result: dict[str, Any],
        algorithm_version: str,
        anonymous_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        document = {
            "request": request,
            "result": result,
            "algorithm_version": algorithm_version,
            "anonymous_id": anonymous_id,
            "user_id": user_id,
            "created_at": utc_now(),
        }

        insert_result = await self.collection.insert_one(document)
        return str(insert_result.inserted_id)

    async def find_by_id(self, recommendation_id: str) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(recommendation_id)
        except InvalidId:
            return None

        document = await self.collection.find_one({"_id": object_id})
        if document is None:
            return None

        document["recommendation_id"] = str(document.pop("_id"))
        return document
''')


write_file("backend/app/services/recommendation_service.py", r'''
from app.algorithms.filters import apply_hard_filters
from app.algorithms.normalizer import normalized_request
from app.algorithms.routine_builder import build_routine
from app.algorithms.scoring import score_products
from app.algorithms.sorting import sort_scored_products
from app.core.time import utc_now
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import (
    FilterSummary,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationRoutine,
)
from app.services.explanation_service import ExplanationService


class RecommendationService:
    algorithm_version = "rule-based-v1"

    def __init__(
        self,
        product_repository: ProductRepository,
        recommendation_repository: RecommendationRepository,
        explanation_service: ExplanationService,
    ) -> None:
        self.product_repository = product_repository
        self.recommendation_repository = recommendation_repository
        self.explanation_service = explanation_service

    async def create_recommendation(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        normalized = normalized_request(request)

        products = await self.product_repository.list_active_products()
        filter_result = apply_hard_filters(products=products, request=normalized)

        scored = score_products(filter_result.allowed_products, normalized)
        sorted_products = sort_scored_products(scored)

        routine_source = build_routine(
            products=sorted_products,
            experience=normalized.experience,
        )

        routine = RecommendationRoutine(
            morning=[
                self.explanation_service.build_recommended_product(item, normalized)
                for item in routine_source["morning"]
            ],
            evening=[
                self.explanation_service.build_recommended_product(item, normalized)
                for item in routine_source["evening"]
            ],
        )

        unique_products = {
            item.product.external_id: item.product
            for item in [*routine.morning, *routine.evening]
        }

        total_price_rub = sum(product.price_rub for product in unique_products.values())

        filter_summary = FilterSummary(
            total_products=len(products),
            allowed_products=len(filter_result.allowed_products),
            filtered_out=len(products) - len(filter_result.allowed_products),
            filter_reasons=filter_result.filter_reasons,
        )

        result_payload = {
            "algorithm_version": self.algorithm_version,
            "routine": routine.model_dump(),
            "filter_summary": filter_summary.model_dump(),
            "total_price_rub": total_price_rub,
            "created_at": utc_now(),
        }

        recommendation_id = await self.recommendation_repository.save_session(
            request=normalized.model_dump(),
            result=result_payload,
            algorithm_version=self.algorithm_version,
            anonymous_id=normalized.anonymous_id,
        )

        return RecommendationResponse(
            recommendation_id=recommendation_id,
            **result_payload,
        )

    async def get_recommendation(self, recommendation_id: str) -> RecommendationResponse | None:
        document = await self.recommendation_repository.find_by_id(recommendation_id)

        if document is None:
            return None

        return RecommendationResponse(
            recommendation_id=document["recommendation_id"],
            **document["result"],
        )
''')


write_file("backend/app/api/v1/endpoints/recommendations.py", r'''
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.mongodb import get_database
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.explanation_service import ExplanationService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service(database=Depends(get_database)) -> RecommendationService:
    return RecommendationService(
        product_repository=ProductRepository(database),
        recommendation_repository=RecommendationRepository(database),
        explanation_service=ExplanationService(),
    )


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(
    payload: RecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    return await service.create_recommendation(payload)


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    recommendation = await service.get_recommendation(recommendation_id)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    return recommendation
''')


write_file("backend/app/api/v1/router.py", r'''
from fastapi import APIRouter

from app.api.v1.endpoints import health, products, questionnaire, recommendations, restrictions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(questionnaire.router)
api_router.include_router(restrictions.router)
api_router.include_router(products.router)
api_router.include_router(recommendations.router)
''')


write_file("backend/tests/test_recommendations.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def _payload() -> dict:
    return {
        "skin_type": "combination",
        "concerns": ["acne", "sebum"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "beginner",
        "values": ["comfort", "price_quality"],
        "anonymous_id": "test-anon",
    }


def test_recommendation_can_be_created() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=_payload())

    assert response.status_code == 200

    payload = response.json()
    assert payload["recommendation_id"]
    assert payload["algorithm_version"] == "rule-based-v1"
    assert payload["routine"]["morning"]
    assert payload["routine"]["evening"]
    assert payload["total_price_rub"] > 0
    assert payload["filter_summary"]["total_products"] >= 8


def test_recommendation_items_have_explanations_and_scores() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=_payload())

    assert response.status_code == 200

    payload = response.json()
    items = payload["routine"]["morning"] + payload["routine"]["evening"]

    assert items

    for item in items:
        assert item["score"] > 0
        assert item["why_here"]
        assert item["budget_reason"]
        assert item["safety_note"]
        assert item["how_to_use"]
        assert item["score_breakdown"]["total"] == item["score"]
        assert item["llm_ready_context"]["tone"]


def test_recommendation_excludes_fragrance_product() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=_payload())

    assert response.status_code == 200

    payload = response.json()
    items = payload["routine"]["morning"] + payload["routine"]["evening"]
    external_ids = {item["product"]["external_id"] for item in items}

    assert "spf_002" not in external_ids
    assert payload["filter_summary"]["filter_reasons"]["excluded_ingredient"] >= 1


def test_recommendation_can_be_loaded_by_id() -> None:
    with TestClient(app) as client:
        create_response = client.post("/api/v1/recommendations", json=_payload())

    assert create_response.status_code == 200
    recommendation_id = create_response.json()["recommendation_id"]

    with TestClient(app) as client:
        get_response = client.get(f"/api/v1/recommendations/{recommendation_id}")

    assert get_response.status_code == 200
    payload = get_response.json()

    assert payload["recommendation_id"] == recommendation_id
    assert payload["routine"]["morning"]
    assert payload["routine"]["evening"]


def test_unknown_recommendation_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/recommendations/000000000000000000000000")

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
    - pytest tests/test_health.py tests/test_questionnaire.py tests/test_restrictions.py tests/test_products.py tests/test_recommendations.py
''')

print("Step 2.4 recommendation engine files written successfully.")