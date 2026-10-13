from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def ensure_requirement(requirement: str) -> None:
    path = ROOT / "backend/requirements.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    package = requirement.split(">=")[0].split("==")[0].strip().lower()

    existing = [
        line.split(">=")[0].split("==")[0].strip().lower()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]

    if package not in existing:
        lines.append(requirement)

    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def append_env_example_if_missing() -> None:
    path = ROOT / "backend/.env.example"
    text = path.read_text(encoding="utf-8")

    block = """

# LLM explanation layer
LLM_ENABLED=false
VSELLM_BASE_URL=https://api.vsellm.ru/v1
VSELLM_MODEL=openai/gpt-4o-mini
VSELLM_API_KEY=
"""

    if "VSELLM_API_KEY" not in text:
        path.write_text(text.rstrip() + block + "\n", encoding="utf-8")


ensure_requirement("openai>=1.50,<2.0")
append_env_example_if_missing()


write_file("backend/app/core/config.py", r'''
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="KOYASH API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    mongo_uri: str = Field(alias="MONGO_URI")
    mongo_db_name: str = Field(default="koyash", alias="MONGO_DB_NAME")

    cors_origins: str = Field(default="", alias="CORS_ORIGINS")

    jwt_secret_key: str = Field(default="change_me", alias="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    analytics_raw_event_ttl_days: int = Field(default=180, alias="ANALYTICS_RAW_EVENT_TTL_DAYS")

    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    vsellm_api_key: str | None = Field(default=None, alias="VSELLM_API_KEY")
    vsellm_base_url: str = Field(default="https://api.vsellm.ru/v1", alias="VSELLM_BASE_URL")
    vsellm_model: str = Field(default="openai/gpt-4o-mini", alias="VSELLM_MODEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
''')


write_file("backend/app/schemas/analytics.py", r'''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    anonymous_id: str | None = Field(default=None, max_length=120)
    user_id: str | None = Field(default=None, max_length=120)
    recommendation_id: str | None = Field(default=None, max_length=120)
    product_external_id: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsEventResponse(BaseModel):
    event_id: str
    status: str = "recorded"
    created_at: datetime


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    events_by_type: dict[str, int]
    top_products: list[dict[str, Any]]
    feedback_reasons: dict[str, int]
    recent_events: list[dict[str, Any]]
''')


write_file("backend/app/repositories/analytics_repository.py", r'''
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


class AnalyticsRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.database = database
        self.collection = database["analytics_events"]

    async def save_event(
        self,
        event_type: str,
        anonymous_id: str | None,
        user_id: str | None,
        recommendation_id: str | None,
        product_external_id: str | None,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        document = {
            "event_type": event_type,
            "anonymous_id": anonymous_id,
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "product_external_id": product_external_id,
            "metadata": metadata,
            "created_at": utc_now(),
        }

        result = await self.collection.insert_one(document)

        return {
            "event_id": str(result.inserted_id),
            **document,
        }

    async def count_events(self) -> int:
        return await self.collection.count_documents({})

    async def count_by_event_type(self) -> dict[str, int]:
        cursor = await self.collection.aggregate(
            [
                {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )

        result: dict[str, int] = {}

        async for item in cursor:
            if item["_id"] is not None:
                result[str(item["_id"])] = int(item["count"])

        return result

    async def top_products(self, limit: int = 5) -> list[dict[str, Any]]:
        cursor = await self.collection.aggregate(
            [
                {"$match": {"product_external_id": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$product_external_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit},
            ]
        )

        result: list[dict[str, Any]] = []

        async for item in cursor:
            result.append(
                {
                    "product_external_id": item["_id"],
                    "count": int(item["count"]),
                }
            )

        return result

    async def feedback_reasons(self) -> dict[str, int]:
        cursor = await self.database["feedback_events"].aggregate(
            [
                {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )

        result: dict[str, int] = {}

        async for item in cursor:
            if item["_id"] is not None:
                result[str(item["_id"])] = int(item["count"])

        return result

    async def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.collection.find({}).sort("created_at", DESCENDING).limit(limit)

        result: list[dict[str, Any]] = []

        async for document in cursor:
            document["event_id"] = str(document.pop("_id"))
            result.append(document)

        return result

    async def clear_event(self, event_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(event_id)})
        return result.deleted_count == 1
''')


write_file("backend/app/services/analytics_service.py", r'''
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    AnalyticsSummaryResponse,
)


class AnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository) -> None:
        self.analytics_repository = analytics_repository

    async def record_event(self, payload: AnalyticsEventCreate) -> AnalyticsEventResponse:
        document = await self.analytics_repository.save_event(
            event_type=payload.event_type,
            anonymous_id=payload.anonymous_id,
            user_id=payload.user_id,
            recommendation_id=payload.recommendation_id,
            product_external_id=payload.product_external_id,
            metadata=payload.metadata,
        )

        return AnalyticsEventResponse(
            event_id=document["event_id"],
            created_at=document["created_at"],
        )

    async def summary(self) -> AnalyticsSummaryResponse:
        total_events = await self.analytics_repository.count_events()
        events_by_type = await self.analytics_repository.count_by_event_type()
        top_products = await self.analytics_repository.top_products()
        feedback_reasons = await self.analytics_repository.feedback_reasons()
        recent_events = await self.analytics_repository.recent_events()

        return AnalyticsSummaryResponse(
            total_events=total_events,
            events_by_type=events_by_type,
            top_products=top_products,
            feedback_reasons=feedback_reasons,
            recent_events=recent_events,
        )
''')


write_file("backend/app/api/v1/endpoints/analytics.py", r'''
from fastapi import APIRouter, Depends, status

from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsEventCreate, AnalyticsEventResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(database=Depends(get_database)) -> AnalyticsService:
    return AnalyticsService(
        analytics_repository=AnalyticsRepository(database),
    )


@router.post(
    "/events",
    response_model=AnalyticsEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_event(
    payload: AnalyticsEventCreate,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsEventResponse:
    return await service.record_event(payload)
''')


write_file("backend/app/api/v1/endpoints/admin_analytics.py", r'''
from fastapi import APIRouter, Depends

from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["admin analytics"])


def get_analytics_service(database=Depends(get_database)) -> AnalyticsService:
    return AnalyticsService(
        analytics_repository=AnalyticsRepository(database),
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummaryResponse:
    return await service.summary()
''')


write_file("backend/app/schemas/llm.py", r'''
from pydantic import BaseModel, Field


class LLMExplanationPreviewRequest(BaseModel):
    skin_type: str
    concerns: list[str] = Field(default_factory=list)
    name: str
    brand: str
    step: str
    ingredients: list[str] = Field(default_factory=list)
    concern_match: int = Field(default=0, ge=0)
    use_llm: bool = False


class LLMExplanationPreviewResponse(BaseModel):
    used_llm: bool
    provider: str
    model: str
    explanation: str
    system_prompt: str
    user_prompt: str


class LLMDemoPayloadsResponse(BaseModel):
    payloads: list[LLMExplanationPreviewRequest]
''')


write_file("backend/app/llm/prompt_templates.py", r'''
KOYASH_EXPLANATION_SYSTEM_PROMPT = """Ты - часть Koyash, ИИ-помощника по подбору косметики. Твоя единственная задача -
короткое человеческое обоснование, почему движок положил этот продукт в косметичку.

ТОН: тепло, по-человечески, как заботливая бабушка - без сюсюканья, без
агрессивного маркетинга, без запугивания, без сложных терминов без пояснения.
Объясняй "почему", а не хвали.

=== ГЛАВНОЕ ОГРАНИЧЕНИЕ - ТЫ ПЕРЕВОДЧИК, НЕ ЭКСПЕРТ ===
Ты НЕ анализируешь состав и НЕ решаешь, подходит ли продукт. Это уже решил движок.
Ты только переупаковываешь готовые входные данные в теплую фразу. Любое твое
собственное суждение о пригодности - ошибка, даже если звучит красиво.

Используй ТОЛЬКО факты из входных данных: название продукта, шаг ухода, тип кожи,
concerns пользователя, concern_match, один-два ингредиента из поданного состава и
их общеизвестную неспецифичную функцию (увлажняет, успокаивает, очищает).
НЕ добавляй: механизм действия, совместимость веществ, дозировки, концентрации,
эффективность, если этого нет во входных данных.

=== ВЕТВЛЕНИЕ ПО concern_match - ОБЯЗАТЕЛЬНО, ПРОВЕРЯЙ ПЕРВЫМ ДЕЛОМ ===
ЕСЛИ concern_match = 0:
  Движок НЕ засчитал ни одной боли пользователя. Продукт стоит в косметичке
  только чтобы закрыть шаг ухода. ЗАПРЕЩЕНО:
  - связывать продукт с типом кожи пользователя,
  - связывать продукт с его concerns,
  - писать "подходит для вашей кожи", "полезно при [боль]", "поможет с [боль]",
    "важно для [тип кожи] кожи".
  Тип кожи и concerns в таком тексте НЕ упоминаются вообще.
  Объясняй ТОЛЬКО нейтральную функцию шага и общую функцию одного ингредиента.

ЕСЛИ concern_match > 0:
  Объясни связь ИМЕННО с той болью, что засчитал движок (поле concerns), через
  один ингредиент из состава. Другие боли не приписывай.

=== ГЛАГОЛЫ - СТРОГО ===
РАЗРЕШЕННЫЕ связки:
  "содержит X", "X - известный увлажняющий/успокаивающий/очищающий компонент",
  "X в уходе связывают с [функция]", "X используется для [функция]".
ЗАПРЕЩЕНО:
  "справляется с", "борется с", "избавляет от", "убирает", "устраняет", "лечит",
  "осветляет", "выравнивает", "контролирует [боль]", "решает проблему",
  "улучшает состояние при [боль]".

=== НИКАКИХ МЕДИЦИНСКИХ ЗАЯВЛЕНИЙ ===
Запрещено: "вылечит", "уберет", "гарантированно поможет", "устранит проблему".

=== ФОРМАТ ===
- 1-2 предложения, максимум 200 символов.
- Назови продукт или один ингредиент и его функцию - строго из входных данных.
- Никаких превосходных степеней: "лучший", "идеальный", "прекрасно", "отлично".
- Не выдумывай и не искажай название продукта - копируй как подано.
- Если данных мало - дай короткую нейтральную фразу, не компенсируй нехваткой
  собственными знаниями о химии.
"""


def build_user_prompt(
    skin_type: str,
    concerns: list[str],
    name: str,
    brand: str,
    step: str,
    ingredients: list[str],
    concern_match: int,
) -> str:
    return f"""Тип кожи пользователя: {skin_type}
Запрос пользователя (concerns): {concerns}

Продукт: {name} ({brand})
Шаг ухода: {step}
Состав (ключевые ингредиенты): {ingredients}
Совпадение с запросом (concern_match): {concern_match}

Напиши короткое обоснование строго по правилам системного промта.
Сначала проверь concern_match: если 0 - НЕ упоминай тип кожи и concerns,
объясни только функцию шага и одного ингредиента."""
''')


write_file("backend/app/services/llm_explanation_service.py", r'''
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.llm.prompt_templates import KOYASH_EXPLANATION_SYSTEM_PROMPT, build_user_prompt
from app.schemas.llm import LLMExplanationPreviewRequest, LLMExplanationPreviewResponse


FUNCTION_HINTS = {
    "глицерин": "увлажняющий",
    "glycerin": "увлажняющий",
    "пантенол": "успокаивающий",
    "panthenol": "успокаивающий",
    "ниацинамид": "себорегулирующий",
    "niacinamide": "себорегулирующий",
    "цинк": "себорегулирующий",
    "zinc": "себорегулирующий",
    "аминокислотные пав": "очищающий",
    "amino acid surfactants": "очищающий",
    "гиалуроновая кислота": "увлажняющий",
    "hyaluronic acid": "увлажняющий",
    "centella": "успокаивающий",
    "центелла": "успокаивающий",
}


class LLMExplanationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ingredient_function(self, ingredients: list[str]) -> tuple[str, str]:
        if not ingredients:
            return "состав", "базовой функцией ухода"

        first = ingredients[0]

        for ingredient in ingredients:
            key = ingredient.lower()
            for pattern, function in FUNCTION_HINTS.items():
                if pattern in key:
                    return ingredient, function

        return first, "базовой функцией ухода"

    def _fallback_explanation(self, payload: LLMExplanationPreviewRequest) -> str:
        ingredient, function = self._ingredient_function(payload.ingredients)

        if payload.concern_match <= 0:
            text = (
                f"{payload.name} закрывает шаг «{payload.step}». "
                f"{ingredient} в уходе связывают с {function} функцией."
            )
        else:
            text = (
                f"{payload.name} добавлен из-за совпадения с запросом. "
                f"{ingredient} - известный {function} компонент."
            )

        return text[:200]

    def _build_prompts(self, payload: LLMExplanationPreviewRequest) -> tuple[str, str]:
        user_prompt = build_user_prompt(
            skin_type=payload.skin_type,
            concerns=payload.concerns,
            name=payload.name,
            brand=payload.brand,
            step=payload.step,
            ingredients=payload.ingredients,
            concern_match=payload.concern_match,
        )

        return KOYASH_EXPLANATION_SYSTEM_PROMPT, user_prompt

    async def preview(
        self,
        payload: LLMExplanationPreviewRequest,
    ) -> LLMExplanationPreviewResponse:
        system_prompt, user_prompt = self._build_prompts(payload)

        if not payload.use_llm or not self.settings.llm_enabled or not self.settings.vsellm_api_key:
            return LLMExplanationPreviewResponse(
                used_llm=False,
                provider="deterministic-fallback",
                model=self.settings.vsellm_model,
                explanation=self._fallback_explanation(payload),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

        client = AsyncOpenAI(
            api_key=self.settings.vsellm_api_key,
            base_url=self.settings.vsellm_base_url,
        )

        response = await client.chat.completions.create(
            model=self.settings.vsellm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=120,
        )

        explanation = response.choices[0].message.content or ""

        return LLMExplanationPreviewResponse(
            used_llm=True,
            provider="vsellm",
            model=self.settings.vsellm_model,
            explanation=explanation.strip()[:300],
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def demo_payloads(self) -> list[LLMExplanationPreviewRequest]:
        return [
            LLMExplanationPreviewRequest(
                skin_type="combination",
                concerns=["acne", "sebum"],
                name="Gentle Balance Cleanser",
                brand="Koyash Sample",
                step="cleanser",
                ingredients=["amino acid surfactants", "glycerin", "panthenol"],
                concern_match=0,
                use_llm=False,
            ),
            LLMExplanationPreviewRequest(
                skin_type="oily",
                concerns=["sebum"],
                name="Sebum Calm Serum",
                brand="Koyash Sample",
                step="serum",
                ingredients=["niacinamide", "zinc", "glycerin"],
                concern_match=1,
                use_llm=False,
            ),
            LLMExplanationPreviewRequest(
                skin_type="sensitive",
                concerns=["sensitivity", "dryness"],
                name="Barrier Comfort Cream",
                brand="Koyash Sample",
                step="moisturizer",
                ingredients=["panthenol", "glycerin", "centella"],
                concern_match=2,
                use_llm=False,
            ),
        ]
''')


write_file("backend/app/api/v1/endpoints/llm_explanations.py", r'''
from fastapi import APIRouter

from app.schemas.llm import (
    LLMDemoPayloadsResponse,
    LLMExplanationPreviewRequest,
    LLMExplanationPreviewResponse,
)
from app.services.llm_explanation_service import LLMExplanationService

router = APIRouter(prefix="/llm/explanations", tags=["llm explanations"])


@router.get("/demo-payloads", response_model=LLMDemoPayloadsResponse)
async def demo_payloads() -> LLMDemoPayloadsResponse:
    service = LLMExplanationService()
    return LLMDemoPayloadsResponse(payloads=service.demo_payloads())


@router.post("/preview", response_model=LLMExplanationPreviewResponse)
async def preview_explanation(
    payload: LLMExplanationPreviewRequest,
) -> LLMExplanationPreviewResponse:
    service = LLMExplanationService()
    return await service.preview(payload)
''')


write_file("backend/app/db/indexes.py", r'''
from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure


async def ensure_index(collection, keys, name: str, **options) -> None:
    try:
        await collection.create_index(keys, name=name, **options)
    except OperationFailure as exc:
        if getattr(exc, "code", None) in {85, 86}:
            await collection.drop_index(name)
            await collection.create_index(keys, name=name, **options)
            return
        raise


async def create_indexes(database: AsyncDatabase, analytics_ttl_days: int) -> None:
    ttl_seconds = analytics_ttl_days * 24 * 60 * 60

    await ensure_index(database["users"], "email", name="email_1", unique=True, sparse=True)
    await ensure_index(database["users"], "anonymous_id", name="anonymous_id_1", sparse=True)

    await ensure_index(database["user_profiles"], "user_id", name="user_id_1", unique=True)
    await ensure_index(database["user_profiles"], "anonymous_id", name="anonymous_id_1", sparse=True)

    await ensure_index(database["products"], "external_id", name="external_id_1", unique=True)
    await ensure_index(database["products"], [("is_active", ASCENDING), ("routine_step", ASCENDING)], name="is_active_1_routine_step_1")
    await ensure_index(database["products"], [("category", ASCENDING), ("budget_segment", ASCENDING)], name="category_1_budget_segment_1")

    await ensure_index(database["ingredient_aliases"], "canonical_key", name="canonical_key_1", unique=True)
    await ensure_index(database["restriction_suggestions"], "canonical_key", name="canonical_key_1", unique=True)
    await ensure_index(
        database["restriction_suggestions"],
        [("status", ASCENDING), ("usage_count", DESCENDING)],
        name="status_1_usage_count_-1",
    )

    await ensure_index(database["custom_restriction_events"], "normalized_key", name="normalized_key_1")
    await ensure_index(database["custom_restriction_events"], "created_at", name="created_at_1")

    await ensure_index(database["recommendation_sessions"], "user_id", name="user_id_1")
    await ensure_index(database["recommendation_sessions"], "anonymous_id", name="anonymous_id_1")
    await ensure_index(database["recommendation_sessions"], "created_at", name="created_at_1")

    await ensure_index(database["feedback_events"], "recommendation_id", name="recommendation_id_1")
    await ensure_index(database["feedback_events"], "product_external_id", name="product_external_id_1")
    await ensure_index(database["feedback_events"], "reason", name="reason_1")
    await ensure_index(database["feedback_events"], "anonymous_id", name="anonymous_id_1")
    await ensure_index(database["feedback_events"], "user_id", name="user_id_1")

    await ensure_index(database["replacement_sessions"], "recommendation_id", name="recommendation_id_1")
    await ensure_index(database["replacement_sessions"], "feedback_id", name="feedback_id_1")

    await ensure_index(database["analytics_events"], "event_type", name="event_type_1")
    await ensure_index(
        database["analytics_events"],
        "created_at",
        name="created_at_1",
        expireAfterSeconds=ttl_seconds,
    )
    await ensure_index(
        database["analytics_events"],
        [("event_type", ASCENDING), ("created_at", DESCENDING)],
        name="event_type_1_created_at_-1",
    )
    await ensure_index(database["analytics_events"], "anonymous_id", name="anonymous_id_1")
    await ensure_index(database["analytics_events"], "user_id", name="user_id_1")

    await ensure_index(
        database["analytics_daily_metrics"],
        [("date", ASCENDING), ("metric", ASCENDING)],
        name="date_1_metric_1",
    )

    await ensure_index(database["llm_explanation_logs"], "recommendation_id", name="recommendation_id_1")
    await ensure_index(database["llm_explanation_logs"], "created_at", name="created_at_1")
''')


write_file("backend/app/api/v1/router.py", r'''
from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_analytics,
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
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(questionnaire.router)
api_router.include_router(restrictions.router)
api_router.include_router(products.router)
api_router.include_router(recommendations.router)
api_router.include_router(feedback.router)
api_router.include_router(replacements.router)
api_router.include_router(analytics.router)
api_router.include_router(admin_analytics.router)
api_router.include_router(llm_explanations.router)
''')


write_file("backend/Dockerfile", r'''
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''')


write_file("backend/scripts/db_smoke.py", r'''
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database


async def main() -> None:
    await connect_to_mongo()

    database = get_database()

    ping = await database.command("ping")
    product_count = await database["products"].count_documents({})
    restriction_count = await database["restriction_suggestions"].count_documents({})
    user_count = await database["users"].count_documents({})
    profile_count = await database["user_profiles"].count_documents({})

    print("Mongo ping:", ping)
    print("Database name:", database.name)
    print("Products:", product_count)
    print("Restriction suggestions:", restriction_count)
    print("Users:", user_count)
    print("User profiles:", profile_count)
    print("DB SMOKE OK")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
''')


write_file("backend/scripts/seed_demo_analytics.py", r'''
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.time import utc_now
from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database


async def main() -> None:
    await connect_to_mongo()

    database = get_database()

    events = [
        {
            "event_type": "questionnaire_opened",
            "anonymous_id": "demo",
            "user_id": None,
            "metadata": {"source": "demo_script"},
            "created_at": utc_now(),
        },
        {
            "event_type": "recommendation_created",
            "anonymous_id": "demo",
            "user_id": None,
            "metadata": {"skin_type": "combination", "concerns": ["acne", "sebum"]},
            "created_at": utc_now(),
        },
        {
            "event_type": "product_viewed",
            "anonymous_id": "demo",
            "user_id": None,
            "product_external_id": "cleanser_001",
            "metadata": {"source": "demo_script"},
            "created_at": utc_now(),
        },
        {
            "event_type": "feedback_submitted",
            "anonymous_id": "demo",
            "user_id": None,
            "metadata": {"reason": "too_expensive"},
            "created_at": utc_now(),
        },
    ]

    await database["analytics_events"].insert_many(events)

    print("Inserted demo analytics events:", len(events))
    print("DEMO ANALYTICS SEED OK")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
''')


write_file("backend/tests/test_analytics.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def test_analytics_event_can_be_recorded() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "product_viewed",
                "anonymous_id": "analytics-test",
                "product_external_id": "cleanser_001",
                "metadata": {
                    "source": "test",
                },
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "recorded"
    assert payload["event_id"]


def test_admin_analytics_summary_is_available() -> None:
    with TestClient(app) as client:
        client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "recommendation_created",
                "anonymous_id": "analytics-test",
                "metadata": {"source": "test"},
            },
        )

        response = client.get("/api/v1/admin/analytics/summary")

    assert response.status_code == 200
    payload = response.json()

    assert "total_events" in payload
    assert "events_by_type" in payload
    assert "recent_events" in payload
''')


write_file("backend/tests/test_llm_explanations.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def test_llm_demo_payloads_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/llm/explanations/demo-payloads")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["payloads"]) == 3
    assert payload["payloads"][0]["concern_match"] == 0


def test_llm_preview_fallback_does_not_call_external_api() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/llm/explanations/preview",
            json={
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "name": "Gentle Balance Cleanser",
                "brand": "Koyash Sample",
                "step": "cleanser",
                "ingredients": ["amino acid surfactants", "glycerin", "panthenol"],
                "concern_match": 0,
                "use_llm": False,
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["used_llm"] is False
    assert payload["explanation"]
    assert "system_prompt" in payload
    assert "user_prompt" in payload
    assert "Тип кожи пользователя" in payload["user_prompt"]
''')


write_file("frontend/public/koyash-demo.html", r'''
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title>KOYASH Demo Console</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #fff7f8;
      color: #2a1f24;
    }

    header {
      background: #f7d9df;
      padding: 24px 32px;
      border-bottom: 1px solid #e7bac5;
    }

    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }

    section {
      background: white;
      border: 1px solid #efd3da;
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 8px 20px rgba(100, 40, 60, 0.08);
    }

    button {
      background: #b85b72;
      color: white;
      border: none;
      border-radius: 12px;
      padding: 10px 14px;
      cursor: pointer;
      margin: 4px 4px 4px 0;
    }

    button.secondary {
      background: #7c6a70;
    }

    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #2a1f24;
      color: #fff;
      padding: 12px;
      border-radius: 12px;
      max-height: 420px;
      overflow: auto;
      font-size: 12px;
    }

    .full {
      grid-column: 1 / -1;
    }

    .muted {
      color: #6d5960;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <header>
    <h1>KOYASH Demo Console</h1>
    <p>Страница для проверки backend без Swagger: анкета, рекомендации, feedback, analytics и LLM-preview.</p>
  </header>

  <main>
    <section>
      <h2>1. Health</h2>
      <p class="muted">Проверка backend и MongoDB.</p>
      <button onclick="checkHealth()">Проверить health</button>
      <pre id="healthOutput">Нажми кнопку.</pre>
    </section>

    <section>
      <h2>2. Анкета</h2>
      <p class="muted">Backend отдаёт структуру вопросов.</p>
      <button onclick="loadQuestionnaire()">Загрузить анкету</button>
      <pre id="questionnaireOutput">Нажми кнопку.</pre>
    </section>

    <section>
      <h2>3. Рекомендации</h2>
      <p class="muted">Движок фильтрует продукты, считает score и собирает routine.</p>
      <button onclick="createRecommendation()">Получить рекомендации</button>
      <button class="secondary" onclick="sendFeedback()">Feedback по первому продукту</button>
      <pre id="recommendationOutput">Нажми кнопку.</pre>
    </section>

    <section>
      <h2>4. Analytics</h2>
      <p class="muted">События и summary для будущего dashboard.</p>
      <button onclick="recordDemoEvent()">Записать demo event</button>
      <button onclick="loadAnalytics()">Показать summary</button>
      <pre id="analyticsOutput">Нажми кнопку.</pre>
    </section>

    <section>
      <h2>5. LLM-preview</h2>
      <p class="muted">По умолчанию без расхода ключа: deterministic fallback.</p>
      <button onclick="loadLLMDemoPayloads()">3 тестовые косметички</button>
      <button onclick="runLLMPreview(false)">Preview без LLM</button>
      <pre id="llmOutput">Нажми кнопку.</pre>
    </section>

    <section class="full">
      <h2>Сценарий демо</h2>
      <ol>
        <li>Проверить health.</li>
        <li>Загрузить анкету.</li>
        <li>Получить рекомендации и показать score / why_here / filter_summary.</li>
        <li>Отправить feedback и показать replacement_candidates.</li>
        <li>Записать событие и показать analytics summary.</li>
        <li>Показать LLM payloads и preview без расхода ключа.</li>
      </ol>
      <p class="muted">Основной пользовательский frontend остаётся на <b>/</b>. Эта страница — технический demo console для команды и заказчицы.</p>
    </section>
  </main>

<script>
let lastRecommendation = null;

function show(id, data) {
  document.getElementById(id).textContent = JSON.stringify(data, null, 2);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();

  try {
    return JSON.parse(text);
  } catch {
    return { status: response.status, raw: text };
  }
}

async function checkHealth() {
  const data = await requestJson('/api/v1/health');
  show('healthOutput', data);
}

async function loadQuestionnaire() {
  const data = await requestJson('/api/v1/questionnaire');
  show('questionnaireOutput', data);
}

async function createRecommendation() {
  const body = {
    skin_type: "combination",
    concerns: ["acne", "sebum"],
    budget: "balanced",
    excluded_ingredients: ["fragrance"],
    custom_restrictions: [],
    experience: "beginner",
    values: ["comfort", "price_quality"],
    anonymous_id: "demo-ui"
  };

  lastRecommendation = await requestJson('/api/v1/recommendations', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });

  show('recommendationOutput', lastRecommendation);
}

function firstRecommendedProduct() {
  if (!lastRecommendation) return null;

  const morning = lastRecommendation.routine?.morning || [];
  const evening = lastRecommendation.routine?.evening || [];
  const all = [...morning, ...evening];

  if (!all.length) return null;

  return all[0].product?.external_id || all[0].external_id || null;
}

async function sendFeedback() {
  if (!lastRecommendation) {
    await createRecommendation();
  }

  const productId = firstRecommendedProduct();

  if (!productId) {
    show('recommendationOutput', { error: 'No product found in recommendation response', lastRecommendation });
    return;
  }

  const data = await requestJson(`/api/v1/recommendations/${lastRecommendation.recommendation_id}/feedback`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      product_external_id: productId,
      reason: "too_expensive",
      comment: "Демо: хочу дешевле",
      anonymous_id: "demo-ui"
    })
  });

  show('recommendationOutput', data);
}

async function recordDemoEvent() {
  const data = await requestJson('/api/v1/analytics/events', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      event_type: "demo_button_clicked",
      anonymous_id: "demo-ui",
      product_external_id: "cleanser_001",
      metadata: {
        source: "koyash-demo.html",
        action: "manual_click"
      }
    })
  });

  show('analyticsOutput', data);
}

async function loadAnalytics() {
  const data = await requestJson('/api/v1/admin/analytics/summary');
  show('analyticsOutput', data);
}

async function loadLLMDemoPayloads() {
  const data = await requestJson('/api/v1/llm/explanations/demo-payloads');
  show('llmOutput', data);
}

async function runLLMPreview(useLLM) {
  const body = {
    skin_type: "combination",
    concerns: ["acne", "sebum"],
    name: "Gentle Balance Cleanser",
    brand: "Koyash Sample",
    step: "cleanser",
    ingredients: ["amino acid surfactants", "glycerin", "panthenol"],
    concern_match: 0,
    use_llm: useLLM
  };

  const data = await requestJson('/api/v1/llm/explanations/preview', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });

  show('llmOutput', data);
}
</script>
</body>
</html>
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

    CORS_ORIGINS: "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    JWT_SECRET_KEY: "test_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: "60"
    ANALYTICS_RAW_EVENT_TTL_DAYS: "30"

    LLM_ENABLED: "false"
    VSELLM_BASE_URL: "https://api.vsellm.ru/v1"
    VSELLM_MODEL: "openai/gpt-4o-mini"
    VSELLM_API_KEY: ""

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
    - pytest tests/test_health.py tests/test_questionnaire.py tests/test_restrictions.py tests/test_products.py tests/test_recommendations.py tests/test_feedback_replacements.py tests/test_auth_users.py tests/test_recommendation_contract.py tests/test_analytics.py tests/test_llm_explanations.py
''')

print("Step 2.7 analytics, LLM hook and frontend demo console written successfully.")