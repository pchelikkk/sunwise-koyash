from enum import StrEnum


class SkinType(StrEnum):
    OILY = "oily"
    DRY = "dry"
    COMBINATION = "combination"
    SENSITIVE = "sensitive"
    NORMAL = "normal"


class Concern(StrEnum):
    ACNE = "acne"
    AGE_CHANGES = "age_changes"
    DEHYDRATION = "dehydration"
    SEBUM = "sebum"
    DRYNESS = "dryness"
    DULLNESS = "dullness"
    PIGMENTATION = "pigmentation"
    PORES = "pores"
    POST_ACNE = "post_acne"
    REACTIVITY = "reactivity"
    REDNESS = "redness"
    UNEVEN_TONE = "uneven_tone"
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
    GUIDED = "guided"


class RoutineStep(StrEnum):
    CLEANSER = "cleanser"
    TONER = "toner"
    SERUM = "serum"
    TREATMENT = "treatment"
    MOISTURIZER = "moisturizer"
    SPF = "spf"
    EXFOLIATION = "exfoliation"
    MASK = "mask"


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
    FAVORITE_ADDED = "favorite_added"
    FAVORITE_REMOVED = "favorite_removed"
    COSMETIC_BAG_ADDED = "cosmetic_bag_added"
    COSMETIC_BAG_REMOVED = "cosmetic_bag_removed"
    RECOMMENDATION_SHARED = "recommendation_shared"
    STORE_OPENED = "store_opened"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    REPLACEMENT_GENERATED = "replacement_generated"
    REPLACEMENT_SELECTED = "replacement_selected"
    REGISTRATION_COMPLETED = "registration_completed"
    PROFILE_SAVED = "profile_saved"
    LLM_EXPLANATION_SUCCESS = "llm_explanation_success"
    LLM_EXPLANATION_FALLBACK = "llm_explanation_fallback"


class AnalyticsEventSource(StrEnum):
    PUBLIC = "public"
    SERVER = "server"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class PublicAnalyticsEventType(StrEnum):
    QUESTIONNAIRE_OPENED = "questionnaire_opened"
    QUESTIONNAIRE_STARTED = "questionnaire_started"
    QUESTION_ANSWERED = "question_answered"
    RESULT_VIEWED = "result_viewed"
    PRODUCT_VIEWED = "product_viewed"
    PRODUCT_DETAILS_OPENED = "product_details_opened"
    FAVORITE_ADDED = "favorite_added"
    FAVORITE_REMOVED = "favorite_removed"
    COSMETIC_BAG_ADDED = "cosmetic_bag_added"
    COSMETIC_BAG_REMOVED = "cosmetic_bag_removed"
    RECOMMENDATION_SHARED = "recommendation_shared"
    STORE_OPENED = "store_opened"
