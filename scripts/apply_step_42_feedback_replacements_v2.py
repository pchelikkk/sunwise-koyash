from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


write_file("backend/app/algorithms/replacement_strategy.py", r'''
from typing import Any


REASON_LABELS = {
    "too_expensive": "дешевле",
    "dislikes_brand": "другой бренд",
    "composition_concern": "меньше спорных отметок по составу",
    "texture_not_suitable": "другая текстура",
    "too_many_steps": "проще для рутины",
    "other": "альтернатива по тем же правилам подбора",
}


RISK_KEYS = (
    "risk_flags",
    "ingredient_flags",
    "excluded_ingredient_flags",
    "avoid_if",
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def _lower_set(value: Any) -> set[str]:
    return {str(item).strip().lower() for item in _as_list(value) if str(item).strip()}


def _product_id(product: dict[str, Any]) -> str:
    return str(product.get("external_id") or product.get("product_id") or product.get("_id") or "")


def _price(product: dict[str, Any]) -> int:
    try:
        return int(product.get("price_rub") or 0)
    except (TypeError, ValueError):
        return 0


def _risk_flags(product: dict[str, Any]) -> set[str]:
    flags: set[str] = set()

    for key in RISK_KEYS:
        flags.update(_lower_set(product.get(key)))

    return flags


def _texture(product: dict[str, Any]) -> str:
    return str(product.get("texture") or product.get("format") or product.get("product_format") or "").lower()


def _brand(product: dict[str, Any]) -> str:
    return str(product.get("brand") or "").lower()


def _routine_step(product: dict[str, Any]) -> str:
    return str(product.get("routine_step") or product.get("step") or "").lower()


def _concerns(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("concerns")) | _lower_set(product.get("matched_concerns"))


def _skin_types(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("skin_types")) | _lower_set(product.get("suitable_skin_types"))


def _values(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("values")) | _lower_set(product.get("tags"))


def _recommendation_context(recommendation: dict[str, Any]) -> dict[str, Any]:
    for key in ("request", "questionnaire", "profile", "input", "answers"):
        value = recommendation.get(key)
        if isinstance(value, dict):
            return value

    return recommendation


def _candidate_is_allowed(
    candidate: dict[str, Any],
    excluded: set[str],
) -> bool:
    if candidate.get("is_active") is False:
        return False

    candidate_flags = _risk_flags(candidate)

    if excluded and candidate_flags.intersection(excluded):
        return False

    return True


def _base_score(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    context: dict[str, Any],
) -> int:
    score = 0

    if _routine_step(candidate) == _routine_step(original_product):
        score += 50

    user_concerns = _lower_set(context.get("concerns"))
    if user_concerns:
        score += 7 * len(user_concerns.intersection(_concerns(candidate)))

    skin_type = str(context.get("skin_type") or "").lower()
    if skin_type and skin_type in _skin_types(candidate):
        score += 12

    user_values = _lower_set(context.get("values"))
    if user_values:
        score += 4 * len(user_values.intersection(_values(candidate)))

    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if original_price and candidate_price:
        if candidate_price <= original_price:
            score += 5
        else:
            score -= min(15, int((candidate_price - original_price) / 300))

    score -= 4 * len(_risk_flags(candidate))

    return score


def _reason_bonus(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    reason: str,
) -> int:
    candidate_price = _price(candidate)
    original_price = _price(original_product)
    candidate_risks = _risk_flags(candidate)
    original_risks = _risk_flags(original_product)

    if reason == "too_expensive":
        if original_price and candidate_price < original_price:
            return 45 + min(25, int((original_price - candidate_price) / 200))
        return -25

    if reason == "dislikes_brand":
        return 45 if _brand(candidate) and _brand(candidate) != _brand(original_product) else -30

    if reason == "composition_concern":
        if len(candidate_risks) < len(original_risks):
            return 45
        if len(candidate_risks) == 0:
            return 35
        return -8 * len(candidate_risks)

    if reason == "texture_not_suitable":
        candidate_texture = _texture(candidate)
        original_texture = _texture(original_product)

        if candidate_texture and original_texture and candidate_texture != original_texture:
            return 45

        if candidate_texture and not original_texture:
            return 20

        return -10

    if reason == "too_many_steps":
        if candidate.get("is_basic") is True:
            return 35

        if candidate.get("routine_complexity") == "simple":
            return 30

        if _routine_step(candidate) == _routine_step(original_product):
            return 15

        return 0

    return 10


def _why_better(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    reason: str,
) -> str:
    name = candidate.get("name", "Средство")
    brand = candidate.get("brand", "бренд")
    reason_label = REASON_LABELS.get(reason, REASON_LABELS["other"])

    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if reason == "too_expensive" and candidate_price and original_price and candidate_price < original_price:
        return f"{name} от {brand} дешевле исходного средства и закрывает тот же шаг ухода."

    if reason == "dislikes_brand" and _brand(candidate) != _brand(original_product):
        return f"{name} от {brand} — альтернатива от другого бренда для того же шага."

    if reason == "composition_concern":
        risks = _risk_flags(candidate)
        if not risks:
            return f"{name} от {brand} отмечено как вариант без явных risk-флагов в текущем каталоге."
        return f"{name} от {brand} подобрано как вариант с более аккуратным профилем по составу."

    if reason == "texture_not_suitable":
        texture = candidate.get("texture") or candidate.get("format")
        if texture:
            return f"{name} от {brand} даёт альтернативную текстуру: {texture}."
        return f"{name} от {brand} — другой вариант для этого шага ухода."

    if reason == "too_many_steps":
        return f"{name} от {brand} оставляет тот же шаг ухода, но лучше подходит для более простой рутины."

    return f"{name} от {brand} — {reason_label}, подобрана по тем же фильтрам безопасности."


def build_replacement_candidates(
    *,
    original_item: dict[str, Any],
    products: list[dict[str, Any]],
    reason: str,
    recommendation: dict[str, Any],
    limit: int = 4,
) -> list[dict[str, Any]]:
    original_product = original_item.get("product", original_item)
    original_id = _product_id(original_product)
    original_step = _routine_step(original_product)

    context = _recommendation_context(recommendation)
    excluded = _lower_set(context.get("excluded_ingredients")) | _lower_set(
        context.get("custom_restrictions")
    )

    scored: list[tuple[int, dict[str, Any]]] = []

    for candidate in products:
        candidate_id = _product_id(candidate)

        if not candidate_id or candidate_id == original_id:
            continue

        if not _candidate_is_allowed(candidate, excluded):
            continue

        same_step = _routine_step(candidate) == original_step
        score = _base_score(candidate, original_product, context)
        score += _reason_bonus(candidate, original_product, reason)

        if same_step:
            score += 20
        else:
            score -= 25

        scored.append((score, candidate))

    if not scored:
        for candidate in products:
            candidate_id = _product_id(candidate)
            if candidate_id and candidate_id != original_id and candidate.get("is_active") is not False:
                score = _reason_bonus(candidate, original_product, reason)
                score += _base_score(candidate, original_product, context)
                scored.append((score, candidate))

    scored.sort(
        key=lambda item: (
            item[0],
            -_price(item[1]) if reason == "too_expensive" else 0,
        ),
        reverse=True,
    )

    result: list[dict[str, Any]] = []

    for rank, (score, product) in enumerate(scored[:limit], start=1):
        result.append(
            {
                "rank": rank,
                "product": product,
                "reason": reason,
                "replacement_score": score,
                "why_better": _why_better(product, original_product, reason),
                "replacement_reason": REASON_LABELS.get(reason, REASON_LABELS["other"]),
            }
        )

    return result
''')


write_file("backend/app/schemas/feedback.py", r'''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    product_external_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    comment: str | None = Field(default=None, max_length=1000)
    anonymous_id: str | None = Field(default=None, max_length=120)


class FeedbackResponse(BaseModel):
    feedback_id: str
    recommendation_id: str
    product_external_id: str
    reason: str
    comment: str | None = None
    replacement_session_id: str
    replacement_candidates: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
''')


write_file("backend/app/schemas/replacement.py", r'''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReplacementCandidate(BaseModel):
    rank: int
    product: dict[str, Any]
    reason: str
    replacement_score: int
    why_better: str
    replacement_reason: str


class ReplacementSessionResponse(BaseModel):
    replacement_session_id: str
    feedback_id: str
    recommendation_id: str
    original_product_external_id: str
    reason: str
    replacement_candidates: list[ReplacementCandidate] = Field(default_factory=list)
    selected_product_external_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ReplacementSelectionRequest(BaseModel):
    product_external_id: str = Field(min_length=1)


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


def _clean(document: dict[str, Any]) -> dict[str, Any]:
    document["feedback_id"] = str(document.pop("_id"))
    return document


class FeedbackRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["feedback_events"]

    async def create(
        self,
        *,
        recommendation_id: str,
        product_external_id: str,
        reason: str,
        comment: str | None,
        anonymous_id: str | None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "recommendation_id": recommendation_id,
            "product_external_id": product_external_id,
            "reason": reason,
            "comment": comment,
            "anonymous_id": anonymous_id,
            "created_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean(document)

    async def find_by_id(self, feedback_id: str) -> dict[str, Any] | None:
        if not ObjectId.is_valid(feedback_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(feedback_id)})

        if document is None:
            return None

        return _clean(document)
''')


write_file("backend/app/repositories/replacement_repository.py", r'''
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _json_safe(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items() if key != "_id"}

    if isinstance(value, list):
        return [_json_safe(item) for item in value]

    return value


def _clean(document: dict[str, Any]) -> dict[str, Any]:
    document["replacement_session_id"] = str(document.pop("_id"))
    return _json_safe(document)


class ReplacementRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["replacement_sessions"]

    async def create(
        self,
        *,
        recommendation_id: str,
        feedback_id: str,
        original_product_external_id: str,
        reason: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "recommendation_id": recommendation_id,
            "feedback_id": feedback_id,
            "original_product_external_id": original_product_external_id,
            "reason": reason,
            "replacement_candidates": _json_safe(candidates),
            "selected_product_external_id": None,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean(document)

    async def list_by_recommendation(
        self,
        recommendation_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        cursor = (
            self.collection.find({"recommendation_id": recommendation_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )

        documents = await cursor.to_list(length=limit)
        return [_clean(document) for document in documents]

    async def find_by_id(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(session_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(session_id)})

        if document is None:
            return None

        return _clean(document)

    async def select(
        self,
        *,
        session_id: str,
        product_external_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(session_id):
            return None

        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "selected_product_external_id": product_external_id,
                    "updated_at": utc_now(),
                }
            },
        )

        if result.matched_count != 1:
            return None

        return await self.find_by_id(session_id)
''')


write_file("backend/app/services/feedback_service.py", r'''
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.algorithms.replacement_strategy import build_replacement_candidates
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse


class FeedbackService:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.database = database
        self.feedback_repository = FeedbackRepository(database)
        self.replacement_repository = ReplacementRepository(database)

    async def submit_feedback(
        self,
        *,
        recommendation_id: str,
        payload: FeedbackCreate,
    ) -> FeedbackResponse:
        recommendation = await self._find_recommendation(recommendation_id)

        if recommendation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )

        original_item = self._find_original_item(
            recommendation=recommendation,
            product_external_id=payload.product_external_id,
        )

        if original_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product is not part of this recommendation",
            )

        feedback = await self.feedback_repository.create(
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            reason=payload.reason,
            comment=payload.comment,
            anonymous_id=payload.anonymous_id,
        )

        products = await self.database["products"].find({"is_active": True}).to_list(length=None)

        candidates = build_replacement_candidates(
            original_item=original_item,
            products=products,
            reason=payload.reason,
            recommendation=recommendation,
            limit=4,
        )

        session = await self.replacement_repository.create(
            recommendation_id=recommendation_id,
            feedback_id=feedback["feedback_id"],
            original_product_external_id=payload.product_external_id,
            reason=payload.reason,
            candidates=candidates,
        )

        return FeedbackResponse(
            feedback_id=feedback["feedback_id"],
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            reason=payload.reason,
            comment=payload.comment,
            replacement_session_id=session["replacement_session_id"],
            replacement_candidates=session["replacement_candidates"],
            created_at=feedback["created_at"],
        )

    async def _find_recommendation(self, recommendation_id: str) -> dict[str, Any] | None:
        queries: list[dict[str, Any]] = [{"recommendation_id": recommendation_id}]

        if ObjectId.is_valid(recommendation_id):
            queries.insert(0, {"_id": ObjectId(recommendation_id)})

        for query in queries:
            document = await self.database["recommendation_sessions"].find_one(query)
            if document is not None:
                document["recommendation_id"] = str(document.get("_id", recommendation_id))
                return document

        return None

    def _find_original_item(
        self,
        *,
        recommendation: dict[str, Any],
        product_external_id: str,
    ) -> dict[str, Any] | None:
        routine = recommendation.get("routine") or {}
        items = []

        for slot in ("morning", "evening"):
            items.extend(routine.get(slot) or [])

        for item in items:
            product = item.get("product") or {}
            external_id = product.get("external_id") or item.get("product_external_id")

            if external_id == product_external_id:
                return item

        return None
''')


write_file("backend/app/services/replacement_service.py", r'''
from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.replacement import ReplacementSelectionResponse, ReplacementSessionResponse


class ReplacementService:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.repository = ReplacementRepository(database)

    async def list_sessions(
        self,
        recommendation_id: str,
    ) -> list[ReplacementSessionResponse]:
        sessions = await self.repository.list_by_recommendation(recommendation_id)
        return [ReplacementSessionResponse(**session) for session in sessions]

    async def select_replacement(
        self,
        *,
        recommendation_id: str,
        session_id: str,
        product_external_id: str,
    ) -> ReplacementSelectionResponse:
        session = await self.repository.find_by_id(session_id)

        if session is None or session["recommendation_id"] != recommendation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replacement session not found",
            )

        candidate_ids = {
            candidate["product"]["external_id"]
            for candidate in session.get("replacement_candidates", [])
            if candidate.get("product", {}).get("external_id")
        }

        if product_external_id not in candidate_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected product is not part of replacement candidates",
            )

        updated = await self.repository.select(
            session_id=session_id,
            product_external_id=product_external_id,
        )

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replacement session not found",
            )

        return ReplacementSelectionResponse(
            replacement_session_id=session_id,
            selected_product_external_id=product_external_id,
        )
''')


write_file("backend/app/api/v1/endpoints/feedback.py", r'''
from typing import Any

from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(tags=["feedback"])


def get_feedback_service(
    database: AsyncDatabase[Any] = Depends(get_database),
) -> FeedbackService:
    return FeedbackService(database)


@router.post(
    "/recommendations/{recommendation_id}/feedback",
    response_model=FeedbackResponse,
)
async def submit_feedback(
    recommendation_id: str,
    payload: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    return await service.submit_feedback(
        recommendation_id=recommendation_id,
        payload=payload,
    )
''')


write_file("backend/app/api/v1/endpoints/replacements.py", r'''
from typing import Any

from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.schemas.replacement import (
    ReplacementSelectionRequest,
    ReplacementSelectionResponse,
    ReplacementSessionResponse,
)
from app.services.replacement_service import ReplacementService

router = APIRouter(tags=["replacements"])


def get_replacement_service(
    database: AsyncDatabase[Any] = Depends(get_database),
) -> ReplacementService:
    return ReplacementService(database)


@router.get(
    "/recommendations/{recommendation_id}/replacements",
    response_model=list[ReplacementSessionResponse],
)
async def list_replacements(
    recommendation_id: str,
    service: ReplacementService = Depends(get_replacement_service),
) -> list[ReplacementSessionResponse]:
    return await service.list_sessions(recommendation_id)


@router.post(
    "/recommendations/{recommendation_id}/replacements/{session_id}/select",
    response_model=ReplacementSelectionResponse,
)
async def select_replacement(
    recommendation_id: str,
    session_id: str,
    payload: ReplacementSelectionRequest,
    service: ReplacementService = Depends(get_replacement_service),
) -> ReplacementSelectionResponse:
    return await service.select_replacement(
        recommendation_id=recommendation_id,
        session_id=session_id,
        product_external_id=payload.product_external_id,
    )
''')


write_file("backend/tests/test_feedback_replacements_v2.py", r'''
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def _recommendation(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v1/recommendations",
        json={
            "age": 24,
            "skin_type": "combination",
            "concerns": ["sebum", "acne"],
            "budget": "balanced",
            "excluded_ingredients": ["fragrance"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "price_quality"],
            "anonymous_id": "replacement-v2-test",
        },
    )

    assert response.status_code == 200
    return response.json()


def _items(recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    routine = recommendation["routine"]
    return [*routine.get("morning", []), *routine.get("evening", [])]


def _submit_feedback(
    client: TestClient,
    recommendation: dict[str, Any],
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    item = _items(recommendation)[0]
    product = item["product"]

    response = client.post(
        f"/api/v1/recommendations/{recommendation['recommendation_id']}/feedback",
        json={
            "product_external_id": product["external_id"],
            "reason": reason,
            "comment": "test feedback",
            "anonymous_id": "replacement-v2-test",
        },
    )

    assert response.status_code == 200
    return item, response.json()


def test_replacement_candidates_do_not_include_original_product() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        original_item, payload = _submit_feedback(client, recommendation, "other")

    original_id = original_item["product"]["external_id"]
    candidates = payload["replacement_candidates"]

    assert candidates
    assert all(candidate["product"]["external_id"] != original_id for candidate in candidates)


def test_too_expensive_prioritizes_cheaper_candidate_when_available() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        original_item, payload = _submit_feedback(client, recommendation, "too_expensive")

    original_price = original_item["product"]["price_rub"]
    candidates = payload["replacement_candidates"]

    assert candidates

    cheaper_candidates = [
        candidate for candidate in candidates
        if candidate["product"]["price_rub"] < original_price
    ]

    if cheaper_candidates:
        assert candidates[0]["product"]["price_rub"] < original_price

    assert "дешев" in candidates[0]["why_better"].lower() or candidates[0]["reason"] == "too_expensive"


def test_dislikes_brand_prioritizes_another_brand_when_available() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        original_item, payload = _submit_feedback(client, recommendation, "dislikes_brand")

    original_brand = original_item["product"]["brand"]
    candidates = payload["replacement_candidates"]

    assert candidates

    different_brand_candidates = [
        candidate for candidate in candidates
        if candidate["product"]["brand"] != original_brand
    ]

    if different_brand_candidates:
        assert candidates[0]["product"]["brand"] != original_brand


def test_composition_concern_returns_explanatory_safer_alternative() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        _, payload = _submit_feedback(client, recommendation, "composition_concern")

    candidates = payload["replacement_candidates"]

    assert candidates
    assert candidates[0]["why_better"]
    assert candidates[0]["replacement_reason"]


def test_replacement_sessions_can_be_listed_and_selected() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        _, payload = _submit_feedback(client, recommendation, "texture_not_suitable")

        list_response = client.get(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/replacements"
        )

        assert list_response.status_code == 200
        sessions = list_response.json()
        assert sessions

        candidate_id = payload["replacement_candidates"][0]["product"]["external_id"]

        select_response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/replacements/{payload['replacement_session_id']}/select",
            json={"product_external_id": candidate_id},
        )

    assert select_response.status_code == 200
    selected = select_response.json()
    assert selected["selected_product_external_id"] == candidate_id
    assert selected["status"] == "selected"


def test_replacement_selection_rejects_product_outside_candidates() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        _, payload = _submit_feedback(client, recommendation, "too_many_steps")

        response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/replacements/{payload['replacement_session_id']}/select",
            json={"product_external_id": "not-a-candidate"},
        )

    assert response.status_code == 400
''')

print("Step 4.2 feedback replacements v2 files written successfully.")