from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


write_file("backend/app/core/enums.py", r'''
from enum import StrEnum


class SkinType(StrEnum):
    OILY = "oily"
    DRY = "dry"
    COMBINATION = "combination"
    SENSITIVE = "sensitive"
    NORMAL = "normal"


class Concern(StrEnum):
    ACNE = "acne"
    SEBUM = "sebum"
    DRYNESS = "dryness"
    POST_ACNE = "post_acne"
    UNEVEN_TONE = "uneven_tone"
    SENSITIVITY = "sensitivity"
    AGE_CHANGES = "age_changes"
    UNKNOWN = "unknown"


class BudgetSegment(StrEnum):
    MINIMUM = "minimum"
    BALANCED = "balanced"
    PREMIUM = "premium"


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    BASIC = "basic"
    ADVANCED = "advanced"
    MINIMAL = "minimal"


class RoutineStep(StrEnum):
    CLEANSER = "cleanser"
    SERUM = "serum"
    TREATMENT = "treatment"
    MOISTURIZER = "moisturizer"
    SPF = "spf"


class RestrictionStatus(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    HIDDEN = "hidden"
    BLOCKED = "blocked"


class AnalyticsEventType(StrEnum):
    QUESTIONNAIRE_STARTED = "questionnaire_started"
    QUESTION_ANSWERED = "question_answered"
    QUESTIONNAIRE_COMPLETED = "questionnaire_completed"
    RECOMMENDATION_REQUESTED = "recommendation_requested"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RESULT_VIEWED = "result_viewed"
    PRODUCT_DETAILS_OPENED = "product_details_opened"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    REPLACEMENT_GENERATED = "replacement_generated"
    REPLACEMENT_SELECTED = "replacement_selected"
    REGISTRATION_COMPLETED = "registration_completed"
    PROFILE_SAVED = "profile_saved"
''')


write_file("backend/app/schemas/common.py", r'''
from pydantic import BaseModel, Field


class APIMessage(BaseModel):
    message: str = Field(..., examples=["ok"])


class ErrorResponse(BaseModel):
    detail: str
''')


write_file("backend/app/schemas/product.py", r'''
from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    external_id: str
    name: str
    brand: str
    category: str
    routine_step: str
    price_rub: int = Field(ge=0)
    budget_segment: str
    skin_types: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    ingredient_flags: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    texture: str | None = None
    description: str
    how_to_use: str
    source_url: str | None = None
    is_active: bool = True

    model_config = ConfigDict(extra="ignore")
''')


write_file("backend/app/schemas/restriction.py", r'''
from pydantic import BaseModel, ConfigDict, Field


class RestrictionSuggestionResponse(BaseModel):
    canonical_key: str
    display_name: str
    usage_count: int = 0
    status: str = "approved"
    is_popular: bool = True

    model_config = ConfigDict(extra="ignore")


class RestrictionSuggestionListResponse(BaseModel):
    suggestions: list[RestrictionSuggestionResponse]


class CustomRestrictionCreate(BaseModel):
    value: str = Field(min_length=1, max_length=80)
    anonymous_id: str | None = Field(default=None, max_length=120)


class CustomRestrictionResponse(BaseModel):
    raw_value: str
    normalized_key: str
    display_name: str
    status: str
    added_to_popular: bool
''')


write_file("backend/app/schemas/questionnaire.py", r'''
from pydantic import BaseModel, Field

from app.schemas.restriction import RestrictionSuggestionResponse


class QuestionOption(BaseModel):
    id: str
    label: str
    value: str
    description: str | None = None


class QuestionnaireQuestion(BaseModel):
    id: str
    step: int
    total_steps: int
    title: str
    description: str
    answer_type: str
    options: list[QuestionOption] = Field(default_factory=list)
    why_we_ask: str
    allows_custom: bool = False
    popular_suggestions: list[RestrictionSuggestionResponse] = Field(default_factory=list)


class QuestionnaireResponse(BaseModel):
    version: str
    questions: list[QuestionnaireQuestion]
''')


write_file("backend/app/repositories/product_repository.py", r'''
from typing import Any

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase


def _clean_document(document: dict[str, Any]) -> dict[str, Any]:
    document.pop("_id", None)
    return document


class ProductRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["products"]

    async def list_active_products(
        self,
        routine_step: str | None = None,
        budget_segment: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"is_active": True}

        if routine_step:
            query["routine_step"] = routine_step

        if budget_segment:
            query["budget_segment"] = budget_segment

        cursor = self.collection.find(query).sort(
            [("routine_step", ASCENDING), ("price_rub", ASCENDING), ("external_id", ASCENDING)]
        )

        return [_clean_document(document) async for document in cursor]

    async def find_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"external_id": external_id, "is_active": True})
        if document is None:
            return None
        return _clean_document(document)
''')


write_file("backend/app/repositories/restriction_repository.py", r'''
from typing import Any

from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_document(document: dict[str, Any]) -> dict[str, Any]:
    document.pop("_id", None)
    return document


class RestrictionRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.suggestions = database["restriction_suggestions"]
        self.aliases = database["ingredient_aliases"]
        self.custom_events = database["custom_restriction_events"]

    async def list_popular_suggestions(self, limit: int = 8) -> list[dict[str, Any]]:
        cursor = (
            self.suggestions.find(
                {
                    "status": "approved",
                    "is_popular": True,
                }
            )
            .sort("usage_count", DESCENDING)
            .limit(limit)
        )

        return [_clean_document(document) async for document in cursor]

    async def find_alias(self, raw_value: str) -> dict[str, Any] | None:
        normalized = raw_value.strip().lower()
        document = await self.aliases.find_one(
            {
                "aliases": normalized,
                "is_active": True,
            }
        )
        if document is None:
            return None
        return _clean_document(document)

    async def record_custom_restriction(
        self,
        raw_value: str,
        normalized_key: str,
        anonymous_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        await self.custom_events.insert_one(
            {
                "raw_value": raw_value,
                "normalized_key": normalized_key,
                "anonymous_id": anonymous_id,
                "user_id": user_id,
                "created_at": utc_now(),
            }
        )

    async def upsert_suggestion_usage(
        self,
        canonical_key: str,
        display_name: str,
        status: str,
        is_popular: bool,
    ) -> None:
        await self.suggestions.update_one(
            {"canonical_key": canonical_key},
            {
                "$set": {
                    "display_name": display_name,
                    "last_used_at": utc_now(),
                },
                "$setOnInsert": {
                    "canonical_key": canonical_key,
                    "status": status,
                    "is_popular": is_popular,
                    "source": "user" if status == "pending" else "system",
                    "created_at": utc_now(),
                },
                "$inc": {"usage_count": 1},
            },
            upsert=True,
        )
''')


write_file("backend/app/services/product_service.py", r'''
from app.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    async def list_products(
        self,
        routine_step: str | None = None,
        budget_segment: str | None = None,
    ) -> list[dict]:
        return await self.repository.list_active_products(
            routine_step=routine_step,
            budget_segment=budget_segment,
        )

    async def get_product(self, external_id: str) -> dict | None:
        return await self.repository.find_by_external_id(external_id)
''')


write_file("backend/app/services/restriction_service.py", r'''
from hashlib import sha1

from app.repositories.restriction_repository import RestrictionRepository
from app.schemas.restriction import (
    CustomRestrictionCreate,
    CustomRestrictionResponse,
    RestrictionSuggestionResponse,
)


class RestrictionService:
    def __init__(self, repository: RestrictionRepository) -> None:
        self.repository = repository

    async def get_popular_suggestions(self) -> list[RestrictionSuggestionResponse]:
        documents = await self.repository.list_popular_suggestions()
        return [RestrictionSuggestionResponse(**document) for document in documents]

    async def add_custom_restriction(
        self,
        payload: CustomRestrictionCreate,
    ) -> CustomRestrictionResponse:
        raw_value = payload.value.strip()
        normalized_input = raw_value.lower()

        alias = await self.repository.find_alias(normalized_input)

        if alias is not None:
            canonical_key = alias["canonical_key"]
            display_name = alias["display_name"]
            status = "approved"
            is_popular = True
        else:
            canonical_key = "custom_" + sha1(normalized_input.encode("utf-8")).hexdigest()[:12]
            display_name = raw_value
            status = "pending"
            is_popular = False

        await self.repository.record_custom_restriction(
            raw_value=raw_value,
            normalized_key=canonical_key,
            anonymous_id=payload.anonymous_id,
        )

        await self.repository.upsert_suggestion_usage(
            canonical_key=canonical_key,
            display_name=display_name,
            status=status,
            is_popular=is_popular,
        )

        return CustomRestrictionResponse(
            raw_value=raw_value,
            normalized_key=canonical_key,
            display_name=display_name,
            status=status,
            added_to_popular=is_popular,
        )
''')


write_file("backend/app/services/questionnaire_service.py", r'''
from app.schemas.questionnaire import QuestionOption, QuestionnaireQuestion, QuestionnaireResponse
from app.schemas.restriction import RestrictionSuggestionResponse


class QuestionnaireService:
    version = "product-foundation-v1"

    def get_questionnaire(
        self,
        restriction_suggestions: list[RestrictionSuggestionResponse],
    ) -> QuestionnaireResponse:
        total_steps = 6

        questions = [
            QuestionnaireQuestion(
                id="skin_type",
                step=1,
                total_steps=total_steps,
                title="Какая у тебя кожа?",
                description="Выбери один вариант. Если сложно определить точно, можно выбрать самый близкий.",
                answer_type="single",
                why_we_ask=(
                    "Так KOYASH не будет советовать слишком активные или неподходящие средства. "
                    "Сначала важно понять базовые особенности кожи."
                ),
                options=[
                    QuestionOption(id="oily", label="Жирная", value="oily"),
                    QuestionOption(id="dry", label="Сухая", value="dry"),
                    QuestionOption(id="combination", label="Комбинированная", value="combination"),
                    QuestionOption(id="sensitive", label="Чувствительная", value="sensitive"),
                ],
            ),
            QuestionnaireQuestion(
                id="concerns",
                step=2,
                total_steps=total_steps,
                title="Что хочется улучшить в первую очередь?",
                description="Можно выбрать несколько пунктов. Это помогает понять главные задачи ухода.",
                answer_type="multi",
                why_we_ask=(
                    "Уход строится вокруг конкретных задач. Например, подбор под жирный блеск "
                    "и подбор под сухость — это разные сценарии."
                ),
                options=[
                    QuestionOption(id="acne", label="Высыпания", value="acne"),
                    QuestionOption(id="sebum", label="Жирный блеск", value="sebum"),
                    QuestionOption(id="dryness", label="Сухость", value="dryness"),
                    QuestionOption(id="sensitivity", label="Чувствительность", value="sensitivity"),
                    QuestionOption(id="post_acne", label="Постакне", value="post_acne"),
                    QuestionOption(id="uneven_tone", label="Неровный тон", value="uneven_tone"),
                    QuestionOption(id="age_changes", label="Возрастные изменения", value="age_changes"),
                    QuestionOption(id="unknown", label="Пока не знаю", value="unknown"),
                ],
            ),
            QuestionnaireQuestion(
                id="budget",
                step=3,
                total_steps=total_steps,
                title="Какой бюджет тебе комфортен?",
                description="Это помогает подобрать реалистичную косметичку без лишнего давления.",
                answer_type="single",
                why_we_ask=(
                    "Один и тот же шаг рутины можно закрыть средствами из разных сегментов. "
                    "Бюджет помогает сразу показать подходящие варианты."
                ),
                options=[
                    QuestionOption(id="minimum", label="Минимум", value="minimum"),
                    QuestionOption(id="balanced", label="Баланс", value="balanced"),
                    QuestionOption(id="premium", label="Премиум", value="premium"),
                ],
            ),
            QuestionnaireQuestion(
                id="restrictions",
                step=4,
                total_steps=total_steps,
                title="Есть ли что-то, чего лучше избегать?",
                description=(
                    "Можно написать свой вариант или выбрать популярные ограничения снизу. "
                    "KOYASH исключит такие средства из подбора."
                ),
                answer_type="multi_with_custom",
                why_we_ask=(
                    "Это защитный фильтр. Если есть чувствительность, аллергии или нежелательные "
                    "ингредиенты, их важно учитывать до выдачи результата."
                ),
                allows_custom=True,
                popular_suggestions=restriction_suggestions,
                options=[],
            ),
            QuestionnaireQuestion(
                id="experience",
                step=5,
                total_steps=total_steps,
                title="Какой формат ухода тебе ближе?",
                description="Подберём рутину, которую реально удобно использовать каждый день.",
                answer_type="single",
                why_we_ask=(
                    "Даже хороший уход не сработает, если он слишком сложный. "
                    "Нам важно предложить реалистичную рутину."
                ),
                options=[
                    QuestionOption(id="beginner", label="Начинаю", value="beginner"),
                    QuestionOption(id="basic", label="Есть базовый уход", value="basic"),
                    QuestionOption(id="advanced", label="Люблю много шагов", value="advanced"),
                    QuestionOption(id="minimal", label="Минимум шагов", value="minimal"),
                ],
            ),
            QuestionnaireQuestion(
                id="values",
                step=6,
                total_steps=total_steps,
                title="Что для тебя особенно важно?",
                description="Выбери несколько приоритетов, чтобы итог был ближе к ожиданиям.",
                answer_type="multi",
                why_we_ask=(
                    "У двух людей с похожей кожей могут быть разные приоритеты: мягкость, "
                    "цена, понятность или короткая рутина."
                ),
                options=[
                    QuestionOption(id="comfort", label="Комфорт", value="comfort"),
                    QuestionOption(id="price_quality", label="Цена / качество", value="price_quality"),
                    QuestionOption(id="soft_formula", label="Мягкие составы", value="soft_formula"),
                    QuestionOption(id="minimal_steps", label="Минимум шагов", value="minimal_steps"),
                ],
            ),
        ]

        return QuestionnaireResponse(version=self.version, questions=questions)
''')


write_file("backend/app/seed/seed_ingredient_aliases.py", r'''
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase


ALIASES = [
    {
        "canonical_key": "fragrance",
        "display_name": "Отдушки",
        "aliases": ["отдушка", "отдушки", "ароматизатор", "ароматизаторы", "fragrance", "parfum", "perfume"],
        "kind": "restriction",
        "is_active": True,
    },
    {
        "canonical_key": "alcohol",
        "display_name": "Спирт",
        "aliases": ["спирт", "алкоголь", "alcohol", "ethanol", "этанол", "ethyl alcohol"],
        "kind": "restriction",
        "is_active": True,
    },
    {
        "canonical_key": "essential_oils",
        "display_name": "Эфирные масла",
        "aliases": ["эфирные масла", "эфирное масло", "essential oils", "essential oil"],
        "kind": "restriction",
        "is_active": True,
    },
    {
        "canonical_key": "none",
        "display_name": "Нет ограничений",
        "aliases": ["нет ограничений", "ничего", "no restrictions", "none"],
        "kind": "restriction",
        "is_active": True,
    },
]


async def seed_ingredient_aliases(database: AsyncDatabase[Any]) -> None:
    collection = database["ingredient_aliases"]

    for alias in ALIASES:
        await collection.update_one(
            {"canonical_key": alias["canonical_key"]},
            {"$set": alias},
            upsert=True,
        )
''')


write_file("backend/app/seed/seed_restrictions.py", r'''
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


RESTRICTIONS = [
    {
        "canonical_key": "fragrance",
        "display_name": "Отдушки",
        "usage_count": 64,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "alcohol",
        "display_name": "Спирт",
        "usage_count": 51,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "essential_oils",
        "display_name": "Эфирные масла",
        "usage_count": 38,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "none",
        "display_name": "Нет ограничений",
        "usage_count": 32,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
]


async def seed_restrictions(database: AsyncDatabase[Any]) -> None:
    collection = database["restriction_suggestions"]

    for restriction in RESTRICTIONS:
        await collection.update_one(
            {"canonical_key": restriction["canonical_key"]},
            {
                "$set": {
                    **restriction,
                    "updated_at": utc_now(),
                },
                "$setOnInsert": {
                    "created_at": utc_now(),
                },
            },
            upsert=True,
        )
''')


write_file("backend/app/seed/seed_products.py", r'''
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


PRODUCTS = [
    {
        "external_id": "cleanser_001",
        "name": "Gentle Balance Cleanser",
        "brand": "Koyash Sample",
        "category": "cleanser",
        "routine_step": "cleanser",
        "price_rub": 750,
        "budget_segment": "balanced",
        "skin_types": ["combination", "oily", "sensitive"],
        "concerns": ["acne", "sebum", "sensitivity"],
        "ingredients": ["glycerin", "panthenol", "coco-betaine"],
        "ingredient_flags": ["fragrance_free", "alcohol_free"],
        "risk_flags": [],
        "texture": "gel",
        "description": "Мягкое очищение для ежедневного базового ухода.",
        "how_to_use": "Нанести на влажную кожу, мягко помассировать и смыть водой.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "cleanser_002",
        "name": "Calm Cream Cleanser",
        "brand": "Soft Lab",
        "category": "cleanser",
        "routine_step": "cleanser",
        "price_rub": 590,
        "budget_segment": "minimum",
        "skin_types": ["dry", "sensitive", "normal"],
        "concerns": ["dryness", "sensitivity"],
        "ingredients": ["glycerin", "allantoin"],
        "ingredient_flags": ["fragrance_free", "alcohol_free"],
        "risk_flags": [],
        "texture": "cream",
        "description": "Кремовое очищение для сухой и чувствительной кожи.",
        "how_to_use": "Использовать утром или вечером, избегая области вокруг глаз.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "serum_001",
        "name": "Barrier Support Serum",
        "brand": "Koyash Sample",
        "category": "serum",
        "routine_step": "serum",
        "price_rub": 980,
        "budget_segment": "balanced",
        "skin_types": ["combination", "dry", "sensitive"],
        "concerns": ["dryness", "sensitivity", "uneven_tone"],
        "ingredients": ["niacinamide", "panthenol", "betaine"],
        "ingredient_flags": ["fragrance_free"],
        "risk_flags": [],
        "texture": "light serum",
        "description": "Сыворотка для поддержки кожного барьера и комфорта.",
        "how_to_use": "Нанести 2–3 капли после очищения перед кремом.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "serum_002",
        "name": "Sebum Care Serum",
        "brand": "Clear Skin",
        "category": "serum",
        "routine_step": "serum",
        "price_rub": 860,
        "budget_segment": "balanced",
        "skin_types": ["oily", "combination"],
        "concerns": ["acne", "sebum", "post_acne"],
        "ingredients": ["niacinamide", "zinc pca"],
        "ingredient_flags": ["fragrance_free"],
        "risk_flags": ["active_formula"],
        "texture": "light gel serum",
        "description": "Лёгкая сыворотка для жирного блеска и высыпаний.",
        "how_to_use": "Использовать вечером 3–4 раза в неделю, затем нанести крем.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "moisturizer_001",
        "name": "Comfort Moisturizer",
        "brand": "Soft Lab",
        "category": "moisturizer",
        "routine_step": "moisturizer",
        "price_rub": 820,
        "budget_segment": "balanced",
        "skin_types": ["dry", "combination", "sensitive", "normal"],
        "concerns": ["dryness", "sensitivity"],
        "ingredients": ["ceramide np", "glycerin", "squalane"],
        "ingredient_flags": ["fragrance_free", "alcohol_free"],
        "risk_flags": [],
        "texture": "cream",
        "description": "Крем для комфорта и восстановления базового ухода.",
        "how_to_use": "Нанести небольшое количество после сыворотки или самостоятельно.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "spf_001",
        "name": "Daily Soft SPF 50",
        "brand": "Koyash Sample",
        "category": "spf",
        "routine_step": "spf",
        "price_rub": 890,
        "budget_segment": "balanced",
        "skin_types": ["combination", "oily", "sensitive", "normal"],
        "concerns": ["post_acne", "uneven_tone", "age_changes"],
        "ingredients": ["zinc oxide", "glycerin"],
        "ingredient_flags": ["fragrance_free"],
        "risk_flags": [],
        "texture": "light cream",
        "description": "Ежедневная защита SPF для утренней рутины.",
        "how_to_use": "Нанести последним шагом утром и обновлять при необходимости.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "spf_002",
        "name": "Budget Daily SPF 30",
        "brand": "Sun Basic",
        "category": "spf",
        "routine_step": "spf",
        "price_rub": 520,
        "budget_segment": "minimum",
        "skin_types": ["normal", "combination", "oily"],
        "concerns": ["uneven_tone", "post_acne"],
        "ingredients": ["octocrylene", "glycerin", "fragrance"],
        "ingredient_flags": [],
        "risk_flags": ["contains_fragrance"],
        "texture": "fluid",
        "description": "Доступный SPF для базовой утренней защиты.",
        "how_to_use": "Нанести утром последним шагом ухода.",
        "source_url": None,
        "is_active": True,
    },
    {
        "external_id": "treatment_001",
        "name": "Gentle Night Treatment",
        "brand": "Clear Skin",
        "category": "treatment",
        "routine_step": "treatment",
        "price_rub": 1050,
        "budget_segment": "balanced",
        "skin_types": ["oily", "combination"],
        "concerns": ["acne", "post_acne", "uneven_tone"],
        "ingredients": ["azelaic acid", "panthenol"],
        "ingredient_flags": ["fragrance_free"],
        "risk_flags": ["active_formula"],
        "texture": "cream-gel",
        "description": "Активный вечерний уход для высыпаний и постакне.",
        "how_to_use": "Использовать вечером 2–3 раза в неделю, постепенно повышая частоту.",
        "source_url": None,
        "is_active": True,
    },
]


async def seed_products(database: AsyncDatabase[Any]) -> None:
    collection = database["products"]

    for product in PRODUCTS:
        await collection.update_one(
            {"external_id": product["external_id"]},
            {
                "$set": {
                    **product,
                    "updated_at": utc_now(),
                },
                "$setOnInsert": {
                    "created_at": utc_now(),
                },
            },
            upsert=True,
        )
''')


write_file("backend/app/seed/__init__.py", r'''
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.seed.seed_ingredient_aliases import seed_ingredient_aliases
from app.seed.seed_products import seed_products
from app.seed.seed_restrictions import seed_restrictions


async def seed_initial_data(database: AsyncDatabase[Any]) -> None:
    await seed_ingredient_aliases(database)
    await seed_restrictions(database)
    await seed_products(database)
''')


write_file("backend/app/api/v1/endpoints/questionnaire.py", r'''
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
''')


write_file("backend/app/api/v1/endpoints/restrictions.py", r'''
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
async def get_restriction_suggestions(database=Depends(get_database)) -> RestrictionSuggestionListResponse:
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
''')


write_file("backend/app/api/v1/endpoints/products.py", r'''
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.mongodb import get_database
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    routine_step: str | None = Query(default=None),
    budget_segment: str | None = Query(default=None),
    database=Depends(get_database),
) -> list[ProductResponse]:
    service = ProductService(ProductRepository(database))
    products = await service.list_products(
        routine_step=routine_step,
        budget_segment=budget_segment,
    )
    return [ProductResponse(**product) for product in products]


@router.get("/{external_id}", response_model=ProductResponse)
async def get_product(
    external_id: str,
    database=Depends(get_database),
) -> ProductResponse:
    service = ProductService(ProductRepository(database))
    product = await service.get_product(external_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse(**product)
''')


write_file("backend/app/api/v1/router.py", r'''
from fastapi import APIRouter

from app.api.v1.endpoints import health, products, questionnaire, restrictions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(questionnaire.router)
api_router.include_router(restrictions.router)
api_router.include_router(products.router)
''')


write_file("backend/app/main.py", r'''
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database
from app.seed import seed_initial_data


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await connect_to_mongo()
    await seed_initial_data(get_database())
    try:
        yield
    finally:
        await close_mongo_connection()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Product-ready backend foundation for KOYASH skincare recommendations.",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def root_health_check() -> dict[str, object]:
    database = get_database()
    ping = await database.command("ping")

    return {
        "status": "ok",
        "service": settings.app_name,
        "database": "ok" if ping.get("ok") == 1 else "unknown",
    }
''')


write_file("backend/tests/test_questionnaire.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def test_questionnaire_contains_only_restriction_popular_suggestions() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/questionnaire")

    assert response.status_code == 200
    payload = response.json()

    assert payload["version"] == "product-foundation-v1"
    assert len(payload["questions"]) == 6

    questions = {question["id"]: question for question in payload["questions"]}

    assert questions["restrictions"]["allows_custom"] is True
    assert questions["restrictions"]["answer_type"] == "multi_with_custom"
    assert len(questions["restrictions"]["popular_suggestions"]) >= 4

    for question_id, question in questions.items():
        if question_id != "restrictions":
            assert question["popular_suggestions"] == []
''')


write_file("backend/tests/test_restrictions.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def test_restriction_suggestions_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/restrictions/suggestions")

    assert response.status_code == 200
    payload = response.json()

    keys = {item["canonical_key"] for item in payload["suggestions"]}
    assert "fragrance" in keys
    assert "alcohol" in keys
    assert "essential_oils" in keys
    assert "none" in keys


def test_custom_restriction_normalizes_known_alias() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/restrictions/custom",
            json={"value": "спирт", "anonymous_id": "test-anon"},
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["raw_value"] == "спирт"
    assert payload["normalized_key"] == "alcohol"
    assert payload["display_name"] == "Спирт"
    assert payload["status"] == "approved"
    assert payload["added_to_popular"] is True


def test_custom_restriction_unknown_value_is_pending() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/restrictions/custom",
            json={"value": "мой редкий ингредиент", "anonymous_id": "test-anon"},
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["normalized_key"].startswith("custom_")
    assert payload["status"] == "pending"
    assert payload["added_to_popular"] is False
''')


write_file("backend/tests/test_products.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def test_products_are_seeded_and_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) >= 8
    assert all(product["external_id"] for product in payload)
    assert all(product["is_active"] is True for product in payload)


def test_product_can_be_loaded_by_external_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products/cleanser_001")

    assert response.status_code == 200
    payload = response.json()

    assert payload["external_id"] == "cleanser_001"
    assert payload["routine_step"] == "cleanser"


def test_unknown_product_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products/unknown_product")

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
    - pytest tests/test_health.py tests/test_questionnaire.py tests/test_restrictions.py tests/test_products.py
''')

print("Step 2.3 files written successfully.")