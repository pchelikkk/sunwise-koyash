from app.schemas.skin_diagnosis import SkinDiagnosisResult, SkinDiagnosticAnswers

SKIN_TYPE_ORDER = ("combination", "dry", "oily", "normal")


def _confidence(scores: dict[str, int]) -> tuple[str, int]:
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - ordered[1]

    if margin >= 5:
        return "high", min(95, 84 + margin)
    if margin >= 3:
        return "medium", 78 + margin
    return "low", 62 + margin * 4


def diagnose_skin_type(answers: SkinDiagnosticAnswers) -> SkinDiagnosisResult:
    scores = {skin_type: 0 for skin_type in SKIN_TYPE_ORDER}
    signals: list[str] = []

    if answers.after_cleansing == "very_tight":
        scores["dry"] += 5
        signals.append("После очищения часто ощущается выраженная стянутость.")
    elif answers.after_cleansing == "slightly_tight":
        scores["dry"] += 3
        scores["combination"] += 1
        signals.append("После очищения иногда появляется лёгкая стянутость.")
    else:
        scores["normal"] += 3
        scores["oily"] += 1
        signals.append("После очищения кожа обычно чувствует себя комфортно.")

    if answers.midday_shine == "all_over":
        scores["oily"] += 6
        signals.append("Блеск в течение дня появляется по всему лицу.")
    elif answers.midday_shine == "t_zone":
        scores["combination"] += 6
        signals.append("Блеск сосредоточен преимущественно в Т-зоне.")
    else:
        scores["dry"] += 3
        scores["normal"] += 2
        signals.append("Заметный блеск в течение дня обычно не появляется.")

    if answers.pore_visibility == "widely_visible":
        scores["oily"] += 5
        signals.append("Поры заметны на большей части лица.")
    elif answers.pore_visibility == "t_zone_visible":
        scores["combination"] += 4
        scores["oily"] += 1
        signals.append("Поры заметнее в Т-зоне.")
    else:
        scores["normal"] += 3
        scores["dry"] += 2
        signals.append("Поры обычно малозаметны.")

    if answers.flaking == "often":
        scores["dry"] += 5
        signals.append("Шелушение возникает часто.")
    elif answers.flaking == "sometimes":
        scores["dry"] += 2
        scores["combination"] += 1
        signals.append("Шелушение возникает время от времени.")
    else:
        scores["normal"] += 2
        scores["oily"] += 1
        signals.append("Шелушение почти не беспокоит.")

    resolved = max(
        SKIN_TYPE_ORDER,
        key=lambda skin_type: (scores[skin_type], -SKIN_TYPE_ORDER.index(skin_type)),
    )
    confidence, confidence_percent = _confidence(scores)

    return SkinDiagnosisResult(
        method="guided_diagnostic",
        submitted_skin_type="unknown",
        resolved_skin_type=resolved,
        confidence=confidence,
        confidence_percent=confidence_percent,
        scores=scores,
        signals=signals,
    )


def self_reported_skin_type(skin_type: str) -> SkinDiagnosisResult:
    return SkinDiagnosisResult(
        method="self_reported",
        submitted_skin_type=skin_type,
        resolved_skin_type=skin_type,
        confidence="high",
        confidence_percent=100,
        scores={},
        signals=["Тип кожи выбран пользователем самостоятельно."],
    )
