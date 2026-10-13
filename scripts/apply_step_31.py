from pathlib import Path
import re

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def replace_regex(relative_path: str, pattern: str, replacement: str) -> None:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement.lstrip("\n"), text, count=1, flags=re.S)

    if count == 0:
        raise RuntimeError(f"Pattern not found in {relative_path}: {pattern[:80]}")

    path.write_text(new_text, encoding="utf-8")


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
    input_placeholder: str | None = None
    min_value: int | None = None
    max_value: int | None = None
    unit: str | None = None


class QuestionnaireResponse(BaseModel):
    version: str
    questions: list[QuestionnaireQuestion]
''')


write_file("backend/app/services/questionnaire_service.py", r'''
from app.schemas.questionnaire import QuestionOption, QuestionnaireQuestion, QuestionnaireResponse
from app.schemas.restriction import RestrictionSuggestionResponse


class QuestionnaireService:
    version = "design-aligned-v1"

    def get_questionnaire(
        self,
        restriction_suggestions: list[RestrictionSuggestionResponse],
    ) -> QuestionnaireResponse:
        total_steps = 7

        questions = [
            QuestionnaireQuestion(
                id="age",
                step=1,
                total_steps=total_steps,
                title="Сколько тебе лет?",
                description="Напиши возраст числом. Это не будет жёстким фильтром, но поможет точнее понимать профиль и аналитику.",
                answer_type="number",
                input_placeholder="например 19",
                min_value=12,
                max_value=100,
                unit="лет",
                why_we_ask=(
                    "Возраст помогает аккуратнее описывать профиль и позже улучшить рекомендации. "
                    "Сейчас он не используется как жёсткое ограничение для выбора средств."
                ),
            ),
            QuestionnaireQuestion(
                id="skin_type",
                step=2,
                total_steps=total_steps,
                title="Какая у тебя кожа?",
                description="Выбери один вариант. Если сложно определить точно, выбери самый близкий.",
                answer_type="single",
                why_we_ask=(
                    "Тип кожи помогает не советовать слишком тяжёлые или слишком активные средства "
                    "там, где лучше начать мягче."
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
                step=3,
                total_steps=total_steps,
                title="Что волнует больше всего?",
                description="Можно выбрать несколько пунктов. Это главные задачи, под которые движок будет искать совпадения.",
                answer_type="multi",
                why_we_ask=(
                    "KOYASH подбирает не просто красивые продукты, а средства под конкретные задачи: "
                    "высыпания, сухость, жирный блеск, постакне и другие запросы."
                ),
                options=[
                    QuestionOption(id="acne", label="Высыпания", value="acne"),
                    QuestionOption(id="sebum", label="Жирный блеск", value="sebum"),
                    QuestionOption(id="dryness", label="Сухость", value="dryness"),
                    QuestionOption(id="reactivity", label="Реактивность", value="reactivity"),
                    QuestionOption(id="post_acne", label="Постакне", value="post_acne"),
                    QuestionOption(id="uneven_tone", label="Неровный тон", value="uneven_tone"),
                    QuestionOption(id="age_changes", label="Возрастные изменения", value="age_changes"),
                    QuestionOption(id="unknown", label="Затрудняюсь ответить", value="unknown"),
                ],
            ),
            QuestionnaireQuestion(
                id="budget",
                step=4,
                total_steps=total_steps,
                title="Какой ориентир по бюджету?",
                description="Выбери комфортный сегмент, чтобы косметичка получилась реалистичной.",
                answer_type="single",
                why_we_ask=(
                    "Один и тот же шаг ухода можно закрыть средствами из разных сегментов. "
                    "Бюджет помогает не перегружать итоговый подбор."
                ),
                options=[
                    QuestionOption(id="minimum", label="Бюджет", value="minimum"),
                    QuestionOption(id="balanced", label="Баланс", value="balanced"),
                    QuestionOption(id="premium", label="Люкс", value="premium"),
                ],
            ),
            QuestionnaireQuestion(
                id="restrictions",
                step=5,
                total_steps=total_steps,
                title="Есть ли ограничения?",
                description="Можно выбрать популярные варианты или написать свой. Эти ответы работают как защитный фильтр.",
                answer_type="multi_with_custom",
                why_we_ask=(
                    "Если есть ингредиенты или группы компонентов, которых лучше избегать, "
                    "их важно исключить до выдачи результата."
                ),
                allows_custom=True,
                popular_suggestions=restriction_suggestions,
                options=[],
            ),
            QuestionnaireQuestion(
                id="experience",
                step=6,
                total_steps=total_steps,
                title="Какой формат ухода тебе ближе?",
                description="Выбери формат, который реально удобно повторять каждый день.",
                answer_type="single",
                why_we_ask=(
                    "Хорошая рекомендация должна быть не только подходящей, но и выполнимой. "
                    "Этот ответ помогает не собрать слишком сложную рутину."
                ),
                options=[
                    QuestionOption(id="minimal", label="Минимально", value="minimal"),
                    QuestionOption(id="basic", label="Знаю базовый уход", value="basic"),
                    QuestionOption(id="advanced", label="Продвинутые знания", value="advanced"),
                    QuestionOption(id="guided", label="Хочу заботливый шаговый уход", value="guided"),
                ],
            ),
            QuestionnaireQuestion(
                id="values",
                step=7,
                total_steps=total_steps,
                title="Что для тебя особенно важно?",
                description="Можно выбрать несколько приоритетов — они помогут отсортировать подходящие продукты.",
                answer_type="multi",
                why_we_ask=(
                    "У людей с похожими задачами могут быть разные ожидания: цена, мягкость, "
                    "простота рутины или ощущение комфорта."
                ),
                options=[
                    QuestionOption(id="comfort", label="Комфорт", value="comfort"),
                    QuestionOption(id="price", label="Цена", value="price"),
                    QuestionOption(id="quality", label="Качество", value="quality"),
                    QuestionOption(id="soft_formula", label="Мягкие составы", value="soft_formula"),
                    QuestionOption(id="fast_result", label="Быстрый результат", value="fast_result"),
                    QuestionOption(id="simple_routine", label="Простая рутина", value="simple_routine"),
                    QuestionOption(id="age_changes", label="Возрастные изменения", value="age_changes"),
                    QuestionOption(id="unknown", label="Затрудняюсь ответить", value="unknown"),
                ],
            ),
        ]

        return QuestionnaireResponse(version=self.version, questions=questions)
''')


write_file("backend/app/schemas/recommendation.py", r'''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class RecommendationRequest(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
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


write_file("backend/app/schemas/user.py", r'''
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
    anonymous_id: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    anonymous_id: str | None = Field(default=None, max_length=120)


class UserProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    anonymous_id: str | None = None
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    values: list[str] = Field(default_factory=list)
    questionnaire_history: list[dict] = Field(default_factory=list)
    feedback_history: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] | None = None
    budget: str | None = None
    excluded_ingredients: list[str] | None = None
    custom_restrictions: list[str] | None = None
    experience: str | None = None
    values: list[str] | None = None
''')


write_file("backend/app/repositories/profile_repository.py", r'''
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_profile(document: dict[str, Any]) -> dict[str, Any]:
    document["profile_id"] = str(document.pop("_id"))
    return document


class ProfileRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["user_profiles"]

    async def create_default_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "user_id": user_id,
            "anonymous_id": anonymous_id,
            "age": None,
            "skin_type": None,
            "concerns": [],
            "budget": None,
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": None,
            "values": [],
            "questionnaire_history": [],
            "feedback_history": [],
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean_profile(document)

    async def find_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"user_id": user_id})

        if document is None:
            return None

        return _clean_profile(document)

    async def ensure_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        profile = await self.find_by_user_id(user_id)

        if profile is not None:
            return profile

        return await self.create_default_profile(
            user_id=user_id,
            anonymous_id=anonymous_id,
        )

    async def update_profile(
        self,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_fields = {
            "age",
            "skin_type",
            "concerns",
            "budget",
            "excluded_ingredients",
            "custom_restrictions",
            "experience",
            "values",
        }

        update = {
            key: value
            for key, value in payload.items()
            if key in allowed_fields and value is not None
        }

        update["updated_at"] = utc_now()

        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update},
        )

        return await self.find_by_user_id(user_id)

    async def sync_anonymous_id(
        self,
        user_id: str,
        anonymous_id: str | None,
    ) -> None:
        if anonymous_id is None:
            return

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "anonymous_id": anonymous_id,
                    "updated_at": utc_now(),
                }
            },
        )
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
    "затрудняюсь ответить": "unknown",
    "unknown": "unknown",
}

CONCERN_ALIASES = {
    "reactivity": "sensitivity",
    "реактивность": "sensitivity",
    "чувствительность": "sensitivity",
    "unknown": "unknown",
    "затрудняюсь ответить": "unknown",
    "пока не знаю": "unknown",
}

VALUE_ALIASES = {
    "price": "price_quality",
    "quality": "price_quality",
    "simple_routine": "minimal_steps",
    "minimal_steps": "minimal_steps",
    "unknown": "unknown",
    "затрудняюсь ответить": "unknown",
}


EXPERIENCE_ALIASES = {
    "guided": "guided",
    "beginner": "beginner",
    "basic": "basic",
    "advanced": "advanced",
    "minimal": "minimal",
}


def normalize_text(value: str) -> str:
    return value.strip().lower().replace("ё", "е")


def _unique_without_empty(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def normalize_restriction(value: str) -> str:
    normalized = normalize_text(value)
    return RESTRICTION_ALIASES.get(normalized, normalized)


def normalize_values(values: list[str], aliases: dict[str, str] | None = None) -> list[str]:
    aliases = aliases or {}
    normalized_values = []

    for value in values:
        normalized = normalize_text(value)
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"", "unknown"}:
            normalized_values.append(normalized)

    return _unique_without_empty(normalized_values)


def normalize_restrictions(values: list[str]) -> list[str]:
    result = []
    for value in values:
        normalized = normalize_restriction(value)
        if normalized and normalized not in {"none", "unknown"} and normalized not in result:
            result.append(normalized)
    return result


def normalize_experience(value: str) -> str:
    normalized = normalize_text(value)
    return EXPERIENCE_ALIASES.get(normalized, normalized)


def normalized_request(request: RecommendationRequest) -> RecommendationRequest:
    return RecommendationRequest(
        age=request.age,
        skin_type=normalize_text(request.skin_type),
        concerns=normalize_values(request.concerns, CONCERN_ALIASES),
        budget=normalize_text(request.budget),
        excluded_ingredients=normalize_restrictions(request.excluded_ingredients),
        custom_restrictions=normalize_restrictions(request.custom_restrictions),
        experience=normalize_experience(request.experience),
        values=normalize_values(request.values, VALUE_ALIASES),
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

    if request.experience in {"beginner", "minimal", "guided"}:
        if not risk_flags:
            experience_score += 10
        else:
            penalties -= 20

    if request.experience == "advanced" and product.get("routine_step") == "treatment":
        experience_score += 8

    if request.experience == "guided" and product.get("routine_step") in {"cleanser", "moisturizer", "spf"}:
        experience_score += 3

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
    if "minimal_steps" in request.values and product.get("routine_step") in {"cleanser", "moisturizer", "spf"}:
        values_score += 3
    if "age_changes" in request.values and "age_changes" in product_concerns:
        values_score += 4

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
    "sensitivity": "реактивность / чувствительность",
    "reactivity": "реактивность",
    "age_changes": "возрастные изменения",
    "unknown": "затрудняюсь ответить",
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
            "age": request.age,
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
    {
        "canonical_key": "unknown",
        "display_name": "Затрудняюсь ответить",
        "usage_count": 20,
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


replace_regex(
    "frontend/src/main.jsx",
    r"function buildRecommendationRequest\(answers\) \{.*?\n\}\n\n// Flatten morning",
    r'''
function buildRecommendationRequest(answers) {
  const restrictions =
    answers.restrictions && typeof answers.restrictions === "object"
      ? answers.restrictions
      : { selected: [], custom: [] };

  const age = answers.age ? Number.parseInt(String(answers.age), 10) : null;

  return {
    age: Number.isFinite(age) ? age : null,
    skin_type: answers.skin_type,
    concerns: answers.concerns || [],
    budget: answers.budget || "balanced",
    excluded_ingredients: (restrictions.selected || []).filter(
      (value) => value !== "none" && value !== "unknown",
    ),
    custom_restrictions: restrictions.custom || [],
    experience: answers.experience || "guided",
    values: answers.values || [],
  };
}

// Flatten morning'''
)


replace_regex(
    "frontend/src/main.jsx",
    r"function Quiz\(\{ go, questionnaire, answers, setAnswers \}\) \{.*?\n\}\n\nfunction Review",
    r'''
function Quiz({ go, questionnaire, answers, setAnswers }) {
  const questions = questionnaire ? questionnaire.questions : [];
  const [i, setI] = React.useState(0);
  const [customText, setCustomText] = React.useState("");

  if (!questions.length) return <CenterInfo text="Загружаем вопросы…" />;

  const q = questions[i];
  const cur = answers[q.id];
  const pct = Math.round(((i + 1) / questions.length) * 100);
  const isMulti = q.answer_type === "multi";
  const isCustom = q.answer_type === "multi_with_custom";
  const isNumber = q.answer_type === "number";
  const custom =
    cur && typeof cur === "object" ? cur : { selected: [], custom: [] };

  const pickSingle = (v) => setAnswers({ ...answers, [q.id]: v });
  const setNumber = (v) => setAnswers({ ...answers, [q.id]: v });
  const toggleMulti = (v) => {
    const arr = Array.isArray(cur) ? cur : [];
    const nextArr = arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
    setAnswers({ ...answers, [q.id]: nextArr });
  };
  const toggleSuggestion = (key) => {
    const sel = custom.selected.includes(key)
      ? custom.selected.filter((x) => x !== key)
      : [...custom.selected, key];
    setAnswers({
      ...answers,
      [q.id]: { selected: sel, custom: custom.custom },
    });
  };
  const addCustom = () => {
    const value = customText.trim();
    if (!value) return;
    setAnswers({
      ...answers,
      [q.id]: { selected: custom.selected, custom: [...custom.custom, value] },
    });
    setCustomText("");
  };
  const removeCustom = (value) =>
    setAnswers({
      ...answers,
      [q.id]: {
        selected: custom.selected,
        custom: custom.custom.filter((x) => x !== value),
      },
    });

  const numberValue = isNumber ? Number.parseInt(String(cur || ""), 10) : null;
  const numberFilled =
    isNumber &&
    Number.isFinite(numberValue) &&
    (q.min_value == null || numberValue >= q.min_value) &&
    (q.max_value == null || numberValue <= q.max_value);

  const filled = isMulti
    ? Array.isArray(cur) && cur.length > 0
    : isCustom
      ? true
      : isNumber
        ? numberFilled
        : !!cur;

  const next = () => {
    if (i < questions.length - 1) setI(i + 1);
    else go("review");
  };
  const back = () => {
    if (i > 0) setI(i - 1);
    else go("home");
  };

  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <Logo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={() => go("home")}>
          на главную
        </button>
      </header>
      <div className="stepMeta">
        Шаг {i + 1} из {questions.length}
      </div>
      <div className="progress">
        <span style={{ width: pct + "%" }} />
      </div>
      <div className="quizGrid">
        <div className="quizMain">
          <h1>{q.title}</h1>
          <p className="qsub">{q.description}</p>

          {isNumber ? (
            <div className="field ageField">
              <label>{q.unit ? "Возраст, " + q.unit : "Ответ"}</label>
              <input
                type="number"
                inputMode="numeric"
                min={q.min_value || undefined}
                max={q.max_value || undefined}
                placeholder={q.input_placeholder || "Введите число"}
                value={cur || ""}
                onChange={(e) => setNumber(e.target.value)}
              />
              {cur && !numberFilled ? (
                <p className="qsub smallWarn">
                  Укажи число от {q.min_value || 0} до {q.max_value || 120}.
                </p>
              ) : null}
            </div>
          ) : isCustom ? (
            <div className="opts three">
              {(q.popular_suggestions || []).map((s) => {
                const on = custom.selected.includes(s.canonical_key);
                return (
                  <button
                    key={s.canonical_key}
                    className={"opt" + (on ? " sel" : "")}
                    onClick={() => toggleSuggestion(s.canonical_key)}
                  >
                    <span className="optHead">
                      {s.display_name}
                      {on ? <span className="check">✓</span> : null}
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <div
              className={
                "opts " +
                (q.options && q.options.length > 4
                  ? "four"
                  : q.options && q.options.length === 3
                    ? "three"
                    : "two")
              }
            >
              {(q.options || []).map((o) => {
                const on = isMulti
                  ? Array.isArray(cur) && cur.includes(o.value)
                  : cur === o.value;
                return (
                  <button
                    key={o.value}
                    className={"opt" + (on ? " sel" : "")}
                    onClick={() =>
                      isMulti ? toggleMulti(o.value) : pickSingle(o.value)
                    }
                  >
                    <span className="optHead">
                      {o.label}
                      {on ? <span className="check">✓</span> : null}
                    </span>
                    {o.description ? (
                      <span className="optDesc">{o.description}</span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          )}

          {isCustom ? (
            <div className="field" style={{ marginTop: 14 }}>
              <label>Свой вариант</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  placeholder="например, отдушки…"
                  value={customText}
                  onChange={(e) => setCustomText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") addCustom();
                  }}
                />
                <button className="btn ghost" onClick={addCustom}>
                  Добавить
                </button>
              </div>
              {custom.custom.length ? (
                <div
                  className="chipRow"
                  style={{
                    marginTop: 10,
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 8,
                  }}
                >
                  {custom.custom.map((c) => (
                    <button
                      key={c}
                      className="opt sel"
                      style={{ padding: "6px 12px" }}
                      onClick={() => removeCustom(c)}
                    >
                      {c} <span className="check">×</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="navRow">
            <button className="btn ghost" onClick={back}>
              Назад
            </button>
            <button
              className="btn solid"
              onClick={next}
              disabled={!filled}
              style={{ opacity: filled ? 1 : 0.5 }}
            >
              {i < questions.length - 1 ? "Далее" : "К результатам"}
            </button>
          </div>
        </div>
        <aside className="quizSide">
          <div className="whyBox">
            <h4>Зачем мы спрашиваем</h4>
            <p>{q.why_we_ask}</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Review'''
)


replace_regex(
    "frontend/src/main.jsx",
    r"function Review\(\{ go, questionnaire, answers \}\) \{.*?\n\}\n\nfunction Loading",
    r'''
function Review({ go, questionnaire, answers }) {
  const questions = questionnaire ? questionnaire.questions : [];
  const renderAnswer = (q) => {
    const v = answers[q.id];
    if (q.answer_type === "number") {
      return v ? String(v) + (q.unit ? " " + q.unit : "") : "—";
    }
    if (q.answer_type === "multi") {
      const arr = Array.isArray(v) ? v : [];
      return arr.length ? arr.map((x) => optionLabel(q, x)).join(", ") : "—";
    }
    if (q.answer_type === "multi_with_custom") {
      const obj = v && typeof v === "object" ? v : { selected: [], custom: [] };
      const parts = [
        ...obj.selected.map((k) => suggestionLabel(q, k)),
        ...obj.custom,
      ];
      return parts.length ? parts.join(", ") : "—";
    }
    return v ? optionLabel(q, v) : "—";
  };
  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <Logo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="quizMain wide">
        <h1>Проверим ответы</h1>
        <p className="qsub">
          Всё верно? Можно вернуться и поправить перед подбором.
        </p>
        <div className="reviewGrid">
          {questions.map((q) => (
            <div className="reviewCard" key={q.id}>
              <b>{q.title}</b>
              <span>{renderAnswer(q)}</span>
            </div>
          ))}
        </div>
        <div className="navRow">
          <button className="btn ghost" onClick={() => go("quiz")}>
            Назад
          </button>
          <button className="btn solid" onClick={() => go("loading")}>
            Собрать косметичку
          </button>
        </div>
      </div>
    </div>
  );
}

function Loading'''
)


main_path = ROOT / "frontend/src/main.jsx"
main_text = main_path.read_text(encoding="utf-8")

account_marker = '''        <div className="reviewGrid">
          <div className="reviewCard">
            <b>Тип кожи</b>'''

if '            <b>Возраст</b>' not in main_text and account_marker in main_text:
    main_text = main_text.replace(
        account_marker,
        '''        <div className="reviewGrid">
          <div className="reviewCard">
            <b>Возраст</b>
            <span>{profile && profile.age ? profile.age + " лет" : "—"}</span>
          </div>
          <div className="reviewCard">
            <b>Тип кожи</b>'''
    )

main_path.write_text(main_text, encoding="utf-8")


styles_path = ROOT / "frontend/src/styles.css"
styles_text = styles_path.read_text(encoding="utf-8")

if ".smallWarn" not in styles_text:
    styles_text += '''

.ageField input {
  max-width: 280px;
  font-size: 20px;
}

.smallWarn {
  color: #9f415b;
  margin-top: 8px;
}
'''

styles_path.write_text(styles_text, encoding="utf-8")


write_file("backend/tests/test_questionnaire.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def test_questionnaire_matches_design_flow() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/questionnaire")

    assert response.status_code == 200
    payload = response.json()

    assert payload["version"] == "design-aligned-v1"
    assert len(payload["questions"]) == 7

    question_ids = [question["id"] for question in payload["questions"]]
    assert question_ids == [
        "age",
        "skin_type",
        "concerns",
        "budget",
        "restrictions",
        "experience",
        "values",
    ]

    questions = {question["id"]: question for question in payload["questions"]}

    assert questions["age"]["answer_type"] == "number"
    assert questions["age"]["min_value"] == 12
    assert questions["age"]["max_value"] == 100
    assert questions["age"]["unit"] == "лет"

    assert questions["restrictions"]["allows_custom"] is True
    assert questions["restrictions"]["answer_type"] == "multi_with_custom"
    assert len(questions["restrictions"]["popular_suggestions"]) >= 4

    for question_id, question in questions.items():
        if question_id != "restrictions":
            assert question["popular_suggestions"] == []


def test_questionnaire_contains_design_labels() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/questionnaire")

    assert response.status_code == 200
    questions = {question["id"]: question for question in response.json()["questions"]}

    assert questions["age"]["title"] == "Сколько тебе лет?"
    assert questions["concerns"]["title"] == "Что волнует больше всего?"
    assert questions["budget"]["title"] == "Какой ориентир по бюджету?"
    assert questions["restrictions"]["title"] == "Есть ли ограничения?"

    concern_values = {option["value"] for option in questions["concerns"]["options"]}
    assert "reactivity" in concern_values
    assert "unknown" in concern_values

    value_values = {option["value"] for option in questions["values"]["options"]}
    assert {"price", "quality", "simple_routine"}.issubset(value_values)
''')


write_file("backend/tests/test_recommendations.py", r'''
from fastapi.testclient import TestClient

from app.main import app


def _payload() -> dict:
    return {
        "age": 19,
        "skin_type": "combination",
        "concerns": ["acne", "sebum"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "guided",
        "values": ["comfort", "price", "quality"],
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
        assert item["llm_ready_context"]["user_profile"]["age"] == 19


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


def test_reactivity_and_design_values_are_normalized() -> None:
    payload = {
        **_payload(),
        "concerns": ["reactivity", "unknown"],
        "excluded_ingredients": ["unknown", "none", "fragrance"],
        "experience": "guided",
        "values": ["price", "quality", "simple_routine", "unknown"],
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=payload)

    assert response.status_code == 200
    result = response.json()
    items = result["routine"]["morning"] + result["routine"]["evening"]

    assert items
    assert all(item["score"] > 0 for item in items)


def test_unknown_recommendation_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/recommendations/000000000000000000000000")

    assert response.status_code == 404
''')


auth_test_path = ROOT / "backend/tests/test_auth_users.py"
auth_test_text = auth_test_path.read_text(encoding="utf-8")

auth_test_text = auth_test_text.replace(
    '''                "skin_type": "combination",
                "concerns": ["acne", "sebum"],''',
    '''                "age": 19,
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],'''
)

auth_test_text = auth_test_text.replace(
    '''    assert payload["skin_type"] == "combination"
    assert "acne" in payload["concerns"]''',
    '''    assert payload["age"] == 19
    assert payload["skin_type"] == "combination"
    assert "acne" in payload["concerns"]'''
)

auth_test_path.write_text(auth_test_text, encoding="utf-8")

print("Step 3.1 questionnaire design alignment written successfully.")