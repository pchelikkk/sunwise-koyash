from app.schemas.questionnaire import (
    QuestionnaireQuestion,
    QuestionnaireResponse,
    QuestionOption,
)
from app.schemas.restriction import RestrictionSuggestionResponse

CONCERN_OPTIONS = [
    QuestionOption(
        id="acne",
        label="Высыпания",
        value="acne",
        description="Воспаления, комедоны или следы после них",
    ),
    QuestionOption(
        id="sebum",
        label="Жирный блеск",
        value="sebum",
        description="Блеск появляется быстро, поры становятся заметнее",
    ),
    QuestionOption(
        id="dryness",
        label="Сухость и шелушение",
        value="dryness",
        description="Коже не хватает мягкости и комфорта",
    ),
    QuestionOption(
        id="dehydration",
        label="Нехватка влаги",
        value="dehydration",
        description="Стянутость, тусклость или мелкие линии от сухости",
    ),
    QuestionOption(
        id="reactivity",
        label="Покраснение и раздражение",
        value="reactivity",
        description="Кожа легко краснеет, щиплет или реагирует на новые средства",
    ),
    QuestionOption(
        id="pigmentation",
        label="Пятна и неровный тон",
        value="pigmentation",
        description="Пигментация, постакне или неоднородный цвет кожи",
    ),
    QuestionOption(
        id="age_changes",
        label="Упругость и морщины",
        value="age_changes",
        description="Хочется поддержать плотность и гладкость кожи",
    ),
    QuestionOption(
        id="unknown",
        label="Пока не знаю",
        value="unknown",
        description="Можно выбрать это — подбор останется нейтральным",
    ),
]


class QuestionnaireService:
    version = "professional-v4"

    def get_questionnaire(
        self,
        restriction_suggestions: list[RestrictionSuggestionResponse],
    ) -> QuestionnaireResponse:
        total_steps = 15

        questions = [
            QuestionnaireQuestion(
                id="skin_type",
                step=1,
                total_steps=total_steps,
                title="Как обычно ведёт себя твоя кожа?",
                description=(
                    "Выбери самое похожее описание. Если сомневаешься, KOYASH поможет "
                    "разобраться с помощью четырёх простых уточнений."
                ),
                answer_type="single",
                why_we_ask=(
                    "Так мы подберём комфортные текстуры и не предложим уход, который "
                    "будет слишком лёгким или, наоборот, тяжёлым."
                ),
                options=[
                    QuestionOption(
                        id="normal",
                        label="Сбалансированная",
                        value="normal",
                        description="Обычно комфортна: без сильной сухости и блеска",
                    ),
                    QuestionOption(
                        id="oily",
                        label="Склонная к жирности",
                        value="oily",
                        description="Блеск заметен на большей части лица",
                    ),
                    QuestionOption(
                        id="dry",
                        label="Склонная к сухости",
                        value="dry",
                        description="Часто ощущается стянутость или есть шелушение",
                    ),
                    QuestionOption(
                        id="combination",
                        label="Комбинированная",
                        value="combination",
                        description="Т-зона блестит, а щёки остаются нормальными или сухими",
                    ),
                    QuestionOption(
                        id="sensitive",
                        label="Часто реагирует",
                        value="sensitive",
                        description="Если покраснение и дискомфорт — главная особенность кожи",
                    ),
                    QuestionOption(
                        id="unknown",
                        label="Помогите определить",
                        value="unknown",
                        description="Отвечу ещё на четыре коротких вопроса",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="diagnostic_after_cleansing",
                step=2,
                total_steps=total_steps,
                title="Как кожа чувствует себя после умывания?",
                description=(
                    "Вспомни ощущения через 10–20 минут после мягкого очищения, до нанесения крема."
                ),
                answer_type="single",
                visible_when_question_id="skin_type",
                visible_when_values=["unknown"],
                why_we_ask=(
                    "Ощущение после умывания помогает понять, хватает ли коже собственного "
                    "защитного слоя."
                ),
                options=[
                    QuestionOption(
                        id="comfortable",
                        label="Комфортно",
                        value="comfortable",
                    ),
                    QuestionOption(
                        id="slightly_tight",
                        label="Немного стягивает",
                        value="slightly_tight",
                    ),
                    QuestionOption(
                        id="very_tight",
                        label="Сильно стягивает",
                        value="very_tight",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="diagnostic_midday_shine",
                step=3,
                total_steps=total_steps,
                title="Где появляется блеск к середине дня?",
                description="Оцени обычный день без плотного макияжа.",
                answer_type="single",
                visible_when_question_id="skin_type",
                visible_when_values=["unknown"],
                why_we_ask=(
                    "Важно не само наличие блеска, а то, где именно он появляется."
                ),
                options=[
                    QuestionOption(id="none", label="Почти нигде", value="none"),
                    QuestionOption(
                        id="t_zone",
                        label="В Т-зоне",
                        value="t_zone",
                        description="Лоб, нос и подбородок",
                    ),
                    QuestionOption(
                        id="all_over",
                        label="По всему лицу",
                        value="all_over",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="diagnostic_pore_visibility",
                step=4,
                total_steps=total_steps,
                title="Насколько заметны поры?",
                description="Выбери наиболее похожее описание без увеличительного зеркала.",
                answer_type="single",
                visible_when_question_id="skin_type",
                visible_when_values=["unknown"],
                why_we_ask=(
                    "Этот ответ дополняет картину. По одному виду пор тип кожи не определяется."
                ),
                options=[
                    QuestionOption(
                        id="barely_visible",
                        label="Почти не заметны",
                        value="barely_visible",
                    ),
                    QuestionOption(
                        id="t_zone_visible",
                        label="Заметнее в Т-зоне",
                        value="t_zone_visible",
                    ),
                    QuestionOption(
                        id="widely_visible",
                        label="Заметны на большей части лица",
                        value="widely_visible",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="diagnostic_flaking",
                step=5,
                total_steps=total_steps,
                title="Как часто появляется шелушение?",
                description="Не учитывай разовую реакцию после пилинга или активов.",
                answer_type="single",
                visible_when_question_id="skin_type",
                visible_when_values=["unknown"],
                why_we_ask=(
                    "Шелушение вместе с другими ответами помогает отличить сухой тип "
                    "от временной нехватки влаги."
                ),
                options=[
                    QuestionOption(id="never", label="Почти никогда", value="never"),
                    QuestionOption(
                        id="sometimes",
                        label="Иногда",
                        value="sometimes",
                    ),
                    QuestionOption(id="often", label="Часто", value="often"),
                ],
            ),
            QuestionnaireQuestion(
                id="concerns",
                step=6,
                total_steps=total_steps,
                title="Что сейчас хочется улучшить?",
                description=(
                    "Можно выбрать до пяти пунктов. Не обязательно знать точные термины — "
                    "ориентируйся на знакомые ощущения."
                ),
                answer_type="multi",
                min_selections=1,
                max_selections=5,
                why_we_ask=(
                    "Так мы поймём, какие свойства средств действительно важны именно тебе."
                ),
                options=CONCERN_OPTIONS,
            ),
            QuestionnaireQuestion(
                id="primary_concern",
                step=7,
                total_steps=total_steps,
                title="На чём сосредоточимся в первую очередь?",
                description=(
                    "Выбери один пункт из предыдущего ответа. Остальные задачи тоже "
                    "останутся в подборе."
                ),
                answer_type="single",
                depends_on_question_id="concerns",
                why_we_ask=(
                    "Главный приоритет помогает сделать результат точнее, когда задач несколько."
                ),
                options=CONCERN_OPTIONS,
            ),
            QuestionnaireQuestion(
                id="sensitivity_level",
                step=8,
                total_steps=total_steps,
                title="Как кожа реагирует на новые средства?",
                description=(
                    "Вспомни жжение, заметное покраснение или раздражение. Это вопрос о "
                    "твоём опыте, а не медицинская диагностика."
                ),
                answer_type="single",
                why_we_ask=(
                    "Чем чаще кожа реагирует, тем осторожнее мы относимся к отдушкам, "
                    "спирту и эфирным маслам."
                ),
                options=[
                    QuestionOption(
                        id="low",
                        label="Обычно всё спокойно",
                        value="low",
                        description="Реакции бывают редко или не бывают",
                    ),
                    QuestionOption(
                        id="medium",
                        label="Иногда реагирует",
                        value="medium",
                        description="Не каждое новое средство подходит с первого раза",
                    ),
                    QuestionOption(
                        id="high",
                        label="Часто реагирует",
                        value="high",
                        description="Раздражение или покраснение возникает регулярно",
                    ),
                    QuestionOption(
                        id="unknown",
                        label="Пока не знаю",
                        value="unknown",
                        description="Не было возможности это отследить",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="budget",
                step=9,
                total_steps=total_steps,
                title="Какой бюджет комфортен для одного средства?",
                description="Речь о цене одного продукта, а не всей косметички.",
                answer_type="single",
                why_we_ask=(
                    "Средства дороже выбранного предела не попадут в рекомендации."
                ),
                options=[
                    QuestionOption(
                        id="minimum",
                        label="До 1 200 ₽ за средство",
                        value="minimum",
                    ),
                    QuestionOption(
                        id="balanced",
                        label="До 2 200 ₽ за средство",
                        value="balanced",
                    ),
                    QuestionOption(
                        id="premium",
                        label="Без жёсткого лимита",
                        value="premium",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="restrictions",
                step=10,
                total_steps=total_steps,
                title="Есть ли компоненты, которых стоит избегать?",
                description=(
                    "Выбери готовый вариант или напиши точное название из состава. "
                    "Если ограничений нет, просто переходи дальше."
                ),
                answer_type="multi_with_custom",
                allows_custom=True,
                max_selections=10,
                custom_input_max_length=100,
                why_we_ask=(
                    "Мы сначала исключаем совпадения из состава и только потом выбираем "
                    "лучшие из оставшихся средств. Свободный текст стоит перепроверить вручную."
                ),
                popular_suggestions=restriction_suggestions,
                options=[],
            ),
            QuestionnaireQuestion(
                id="experience",
                step=11,
                total_steps=total_steps,
                title="Какой у тебя опыт с уходом?",
                description="Выбери вариант, с которым тебе будет комфортно начинать.",
                answer_type="single",
                why_we_ask=(
                    "Новичкам мы предлагаем более понятную схему, а опытным пользователям "
                    "можем показать дополнительные активные шаги."
                ),
                options=[
                    QuestionOption(
                        id="beginner",
                        label="Только начинаю",
                        value="beginner",
                        description="Хочу простую и понятную основу",
                    ),
                    QuestionOption(
                        id="basic",
                        label="Есть базовый опыт",
                        value="basic",
                        description="Пользуюсь очищением, кремом и SPF",
                    ),
                    QuestionOption(
                        id="advanced",
                        label="Уверенно использую активы",
                        value="advanced",
                        description="Знаком(а) с кислотами, ретиноидами или витамином C",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="routine_preference",
                step=12,
                total_steps=total_steps,
                title="Какой ритм ухода тебе подойдёт?",
                description="Лучше выбрать схему, которую получится выполнять регулярно.",
                answer_type="single",
                why_we_ask=(
                    "Количество шагов меняется под твой ритм, а обязательная база остаётся."
                ),
                options=[
                    QuestionOption(
                        id="minimal",
                        label="Просто и быстро",
                        value="minimal",
                        description="Очищение, увлажнение и SPF",
                    ),
                    QuestionOption(
                        id="balanced",
                        label="База плюс один акцент",
                        value="balanced",
                        description="База и один целевой шаг",
                    ),
                    QuestionOption(
                        id="complete",
                        label="Хочу полную схему",
                        value="complete",
                        description="База и доступные дополнительные шаги",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="texture_preference",
                step=13,
                total_steps=total_steps,
                title="Какие текстуры тебе приятнее?",
                description="Это пожелание: безопасность и совместимость всё равно важнее.",
                answer_type="single",
                why_we_ask=(
                    "При равных вариантах мы поднимем выше средство с приятной тебе текстурой."
                ),
                options=[
                    QuestionOption(
                        id="lightweight",
                        label="Лёгкие и быстро впитывающиеся",
                        value="lightweight",
                    ),
                    QuestionOption(id="cream", label="Мягкие кремовые", value="cream"),
                    QuestionOption(id="rich", label="Плотные и питательные", value="rich"),
                    QuestionOption(
                        id="no_preference",
                        label="Не принципиально",
                        value="no_preference",
                    ),
                ],
            ),
            QuestionnaireQuestion(
                id="values",
                step=14,
                total_steps=total_steps,
                title="Что ещё важно при выборе?",
                description="Можно выбрать до трёх пунктов — только то, что действительно важно.",
                answer_type="multi",
                min_selections=1,
                max_selections=3,
                why_we_ask=(
                    "Мы учитываем только те свойства, которые подтверждены данными каталога."
                ),
                options=[
                    QuestionOption(
                        id="soft_formula",
                        label="Бережная формула",
                        value="soft_formula",
                    ),
                    QuestionOption(
                        id="vegan",
                        label="Веганский состав",
                        value="vegan",
                    ),
                    QuestionOption(
                        id="cruelty_free",
                        label="Не тестируется на животных",
                        value="cruelty_free",
                    ),
                    QuestionOption(
                        id="price_quality",
                        label="Разумная цена",
                        value="price_quality",
                    ),
                    QuestionOption(id="unknown", label="Не принципиально", value="unknown"),
                ],
            ),
            QuestionnaireQuestion(
                id="age",
                step=15,
                total_steps=total_steps,
                title="Сколько тебе лет?",
                description=(
                    "Если не хочется отвечать, этот шаг можно пропустить — возраст "
                    "не определяет тип кожи."
                ),
                answer_type="number",
                input_placeholder="например, 24",
                min_value=12,
                max_value=100,
                unit="лет",
                required=False,
                why_we_ask=(
                    "Ответ помогает нам проверять, одинаково ли хорошо сервис работает "
                    "для разных возрастных групп. На подбор влияют особенности кожи, "
                    "а не число в паспорте."
                ),
            ),
        ]

        # The Figma flow opens with the short optional age step. Keep model step
        # metadata aligned with the order returned to clients.
        ordered_questions = [questions[-1], *questions[:-1]]
        questions = [
            question.model_copy(update={"step": index})
            for index, question in enumerate(ordered_questions, start=1)
        ]

        return QuestionnaireResponse(version=self.version, questions=questions)
