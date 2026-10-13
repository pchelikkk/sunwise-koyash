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
