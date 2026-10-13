import re

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.enums import AnalyticsEventType
from app.llm.prompt_templates import KOYASH_EXPLANATION_SYSTEM_PROMPT, build_user_prompt
from app.schemas.llm import LLMExplanationPreviewRequest, LLMExplanationPreviewResponse
from app.schemas.recommendation import RecommendationRequest, RecommendedProduct
from app.services.event_tracking_service import EventTrackingService

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

FORBIDDEN_EXPLANATION_MARKERS = (
    "справляется с",
    "помогает справиться",
    "поможет справиться",
    "борется с",
    "избавляет от",
    "избавит от",
    "убирает",
    "уберет",
    "устраняет",
    "устранит",
    "вылеч",
    "лечит",
    "гарантирован",
    "осветляет",
    "выравнивает",
    "контролирует",
    "решает проблему",
    "решит проблему",
    "станет легче",
    "поможет поддерживать чистоту",
    "способствует улучшению",
    "лучший",
    "идеальный",
    "прекрасно",
    "отлично",
)

UNMATCHED_PERSONALIZATION_MARKERS = (
    "подходит вам",
    "подходит для вашей",
    "для вашего типа кожи",
    "важно для вашей кожи",
    "по вашему запросу",
    "о которой вы писали",
    "о котором вы писали",
    "поможет при",
    "важно для",
)


class LLMExplanationService:
    def __init__(
        self,
        event_tracking_service: EventTrackingService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.event_tracking_service = event_tracking_service

    @property
    def provider(self) -> str:
        return self.settings.llm_provider.strip().casefold()

    @property
    def model(self) -> str:
        if self.provider == "openai":
            return self.settings.openai_model
        return self.settings.vsellm_model

    @property
    def api_key(self) -> str | None:
        if self.provider == "openai":
            return self.settings.openai_api_key
        if self.provider == "vsellm":
            return self.settings.vsellm_api_key
        return None

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.llm_enabled
            and self.provider in {"openai", "vsellm"}
            and self.api_key
        )

    async def enhance_recommended_product(
        self,
        item: RecommendedProduct,
        request: RecommendationRequest,
        *,
        user_id: str | None = None,
        anonymous_id: str | None = None,
    ) -> RecommendedProduct:
        """Rewrite an explanation without changing selection or score data."""

        if not self.is_configured:
            return item

        ingredients = (
            item.product.key_ingredients
            or item.product.ingredients[:6]
        )
        response = await self.preview(
            LLMExplanationPreviewRequest(
                skin_type=request.skin_type,
                concerns=request.concerns,
                matched_concerns=item.matched_concerns,
                name=item.product.name,
                brand=item.product.brand,
                step=item.routine_step,
                ingredients=ingredients,
                concern_match=len(item.matched_concerns),
                use_llm=True,
            ),
            user_id=user_id,
            anonymous_id=anonymous_id,
        )
        if not response.used_llm:
            return item

        return item.model_copy(
            update={
                "why_here": response.explanation,
                "explanation_source": "llm",
                "explanation_model": response.model,
            }
        )

    @staticmethod
    def _is_safe_explanation(
        value: str,
        payload: LLMExplanationPreviewRequest,
    ) -> bool:
        normalized = value.strip().casefold()
        if (
            not normalized
            or len(value.strip()) > 200
            or "ё" in normalized
            or "—" in value
            or "–" in value
            or normalized.startswith("продукт ")
            or any(marker in normalized for marker in FORBIDDEN_EXPLANATION_MARKERS)
        ):
            return False

        sentences = [part for part in re.split(r"[.!?]+", normalized) if part.strip()]
        if not 1 <= len(sentences) <= 2:
            return False

        named_facts = [payload.name, *payload.ingredients]
        if not any(
            fact.strip() and fact.strip().casefold() in normalized
            for fact in named_facts
        ):
            return False

        if not payload.matched_concerns:
            return not any(
                marker in normalized
                for marker in UNMATCHED_PERSONALIZATION_MARKERS
            )

        mentions_ingredient = any(
            ingredient.strip()
            and ingredient.strip().casefold() in normalized
            for ingredient in payload.ingredients
        )
        mentions_matched_concern = any(
            concern.strip()
            and concern.strip().casefold() in normalized
            for concern in payload.matched_concerns
        )
        return mentions_ingredient and mentions_matched_concern

    def _ingredient_function(
        self,
        ingredients: list[str],
    ) -> tuple[str | None, str | None]:
        if not ingredients:
            return None, None

        for ingredient in ingredients:
            key = ingredient.lower()
            for pattern, function in FUNCTION_HINTS.items():
                if pattern in key:
                    return ingredient, function

        return None, None

    def _fallback_explanation(self, payload: LLMExplanationPreviewRequest) -> str:
        ingredient, function = self._ingredient_function(payload.ingredients)

        if not payload.matched_concerns:
            if ingredient and function:
                candidates = [
                    f"Для шага «{payload.step}» выбрали {payload.name}. "
                    f"Внутри {ingredient} - известный {function} компонент.",
                    f"Для шага «{payload.step}» выбрали {payload.name}. "
                    f"Внутри {ingredient}.",
                ]
            else:
                candidates = [
                    f"Для шага «{payload.step}» выбрали {payload.name}, "
                    "чтобы сохранить понятную последовательность ухода."
                ]
        else:
            concern = payload.matched_concerns[0]
            selected_ingredient = ingredient or (
                payload.ingredients[0] if payload.ingredients else None
            )
            if selected_ingredient:
                candidates = [
                    f"Для вашей косметички выбрали {payload.name}: внутри "
                    f"{selected_ingredient}, его в уходе связывают с запросом "
                    f"«{concern}».",
                    f"Внутри {selected_ingredient}; в уходе его связывают с "
                    f"запросом «{concern}», поэтому средство оказалось в наборе.",
                ]
            else:
                candidates = [
                    f"Для шага «{payload.step}» выбрали {payload.name} - "
                    f"движок связал средство с запросом «{concern}»."
                ]

        for candidate in candidates:
            normalized = candidate.replace("ё", "е")
            if len(normalized) <= 200:
                return normalized

        return f"Для шага «{payload.step}» выбрали средство из готового набора."

    def _build_prompts(self, payload: LLMExplanationPreviewRequest) -> tuple[str, str]:
        user_prompt = build_user_prompt(
            skin_type=payload.skin_type,
            concerns=payload.concerns,
            matched_concerns=payload.matched_concerns,
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
        *,
        user_id: str | None = None,
        anonymous_id: str | None = None,
    ) -> LLMExplanationPreviewResponse:
        system_prompt, user_prompt = self._build_prompts(payload)

        fallback_reason = self._fallback_reason(payload)
        if fallback_reason is not None:
            await self._record_result(
                event_type=AnalyticsEventType.LLM_EXPLANATION_FALLBACK,
                payload=payload,
                user_id=user_id,
                anonymous_id=anonymous_id,
                metadata={"fallback_reason": fallback_reason},
            )
            return self._fallback_response(payload, system_prompt, user_prompt)

        try:
            explanation = await self._request_explanation(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            if not explanation:
                raise ValueError("empty_llm_response")
            if not self._is_safe_explanation(explanation, payload):
                raise ValueError("unsafe_llm_response")
        except Exception as exc:
            fallback_reason = (
                "policy_rejected"
                if str(exc) == "unsafe_llm_response"
                else "provider_error"
            )
            await self._record_result(
                event_type=AnalyticsEventType.LLM_EXPLANATION_FALLBACK,
                payload=payload,
                user_id=user_id,
                anonymous_id=anonymous_id,
                metadata={
                    "fallback_reason": fallback_reason,
                    "error_type": type(exc).__name__,
                },
            )
            return self._fallback_response(payload, system_prompt, user_prompt)

        await self._record_result(
            event_type=AnalyticsEventType.LLM_EXPLANATION_SUCCESS,
            payload=payload,
            user_id=user_id,
            anonymous_id=anonymous_id,
            metadata={"provider": self.provider},
        )

        return LLMExplanationPreviewResponse(
            used_llm=True,
            provider=self.provider,
            model=self.model,
            explanation=explanation,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _fallback_reason(self, payload: LLMExplanationPreviewRequest) -> str | None:
        if not payload.use_llm:
            return "llm_not_requested"
        if not self.settings.llm_enabled:
            return "llm_disabled"
        if self.provider not in {"openai", "vsellm"}:
            return "provider_not_supported"
        if not self.api_key:
            return "api_key_missing"
        return None

    async def _request_explanation(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        if self.provider == "openai":
            client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
                timeout=self.settings.llm_timeout_seconds,
            )
            response = await client.responses.create(
                model=self.settings.openai_model,
                instructions=system_prompt,
                input=user_prompt,
                max_output_tokens=120,
            )
            return (response.output_text or "").strip()

        client = AsyncOpenAI(
            api_key=self.settings.vsellm_api_key,
            base_url=self.settings.vsellm_base_url,
            timeout=self.settings.llm_timeout_seconds,
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
        return (response.choices[0].message.content or "").strip()

    def _fallback_response(
        self,
        payload: LLMExplanationPreviewRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMExplanationPreviewResponse:
        return LLMExplanationPreviewResponse(
            used_llm=False,
            provider="deterministic-fallback",
            model=self.model,
            explanation=self._fallback_explanation(payload),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    async def _record_result(
        self,
        *,
        event_type: AnalyticsEventType,
        payload: LLMExplanationPreviewRequest,
        user_id: str | None,
        anonymous_id: str | None,
        metadata: dict,
    ) -> None:
        if self.event_tracking_service is None:
            return

        await self.event_tracking_service.record(
            event_type,
            user_id=user_id,
            anonymous_id=anonymous_id,
            metadata={
                **metadata,
                "provider": self.provider,
                "model": self.model,
                "step": payload.step,
                "concern_match": payload.concern_match,
                "ingredient_count": len(payload.ingredients),
                "requested_llm": payload.use_llm,
            },
        )

    def demo_payloads(self) -> list[LLMExplanationPreviewRequest]:
        return [
            LLMExplanationPreviewRequest(
                skin_type="combination",
                concerns=["acne", "sebum"],
                matched_concerns=[],
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
                matched_concerns=["sebum"],
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
                matched_concerns=["sensitivity", "dryness"],
                name="Barrier Comfort Cream",
                brand="Koyash Sample",
                step="moisturizer",
                ingredients=["panthenol", "glycerin", "centella"],
                concern_match=2,
                use_llm=False,
            ),
        ]
