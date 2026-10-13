from app.algorithms.explanation_context import build_llm_context, matched_concern_labels
from app.algorithms.scoring import ScoredProduct
from app.schemas.product import ProductResponse
from app.schemas.recommendation import RecommendationRequest, RecommendedProduct

ROUTINE_STEP_LABELS = {
    "cleanser": "очищение",
    "toner": "тонизирование",
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
        routine_step_label = ROUTINE_STEP_LABELS.get(
            product.get("routine_step"),
            product.get("routine_step"),
        )

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
            budget_reason = (
                "Средство немного доступнее выбранного бюджета, поэтому помогает "
                "не перегрузить косметичку."
            )
        else:
            budget_reason = (
                "Средство не идеально совпадает с бюджетом, но прошло фильтры "
                "и набрало высокий score."
            )

        risk_flags = product.get("risk_flags", [])
        ingredient_flags = product.get("ingredient_flags", [])

        if not risk_flags:
            safety_note = "В карточке нет явных риск-флагов для выбранного профиля."
        elif "active_formula" in risk_flags:
            safety_note = (
                "Это активная формула, её лучше вводить постепенно и отслеживать "
                "реакцию кожи."
            )
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
