from app.algorithms.scoring import ScoredProduct


def _best_by_step(
    products: list[ScoredProduct],
    step: str,
) -> ScoredProduct | None:
    for product in products:
        if product.product.get("routine_step") == step:
            return product
    return None


def build_routine(
    products: list[ScoredProduct],
    experience: str,
    routine_preference: str = "balanced",
) -> dict[str, list[ScoredProduct]]:
    cleanser = _best_by_step(products, "cleanser")
    toner = _best_by_step(products, "toner")
    serum = _best_by_step(products, "serum")
    treatment = _best_by_step(products, "treatment")
    moisturizer = _best_by_step(products, "moisturizer")
    spf = _best_by_step(products, "spf")

    morning: list[ScoredProduct] = []
    evening: list[ScoredProduct] = []

    if cleanser is not None:
        morning.append(cleanser)
        evening.append(cleanser)

    if routine_preference == "complete" and toner is not None:
        morning.append(toner)

    if moisturizer is not None:
        morning.append(moisturizer)

    if spf is not None:
        morning.append(spf)

    if routine_preference in {"balanced", "complete"} and toner is not None:
        evening.append(toner)

    if routine_preference == "balanced":
        if experience in {"advanced", "basic"} and treatment is not None:
            evening.append(treatment)
        elif serum is not None:
            evening.append(serum)
        elif treatment is not None:
            evening.append(treatment)

    if routine_preference == "complete":
        if serum is not None:
            evening.append(serum)
        if experience in {"advanced", "basic"} and treatment is not None:
            evening.append(treatment)
        elif serum is None and treatment is not None:
            evening.append(treatment)

    if moisturizer is not None:
        evening.append(moisturizer)

    return {
        "morning": morning,
        "evening": evening,
    }
