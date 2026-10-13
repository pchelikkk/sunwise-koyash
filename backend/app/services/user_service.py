from app.core.enums import AnalyticsEventType
from app.repositories.cosmetic_bag_repository import CosmeticBagRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.library import (
    CosmeticBagProductListResponse,
    CosmeticBagProductResponse,
    FavoriteProductListResponse,
    FavoriteProductResponse,
    RecommendationHistoryResponse,
)
from app.schemas.product import ProductResponse
from app.schemas.recommendation import RecommendationResponse
from app.schemas.user import (
    QuestionnaireHistoryCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.event_tracking_service import EventTrackingService


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        product_repository: ProductRepository | None = None,
        favorite_repository: FavoriteRepository | None = None,
        cosmetic_bag_repository: CosmeticBagRepository | None = None,
        recommendation_repository: RecommendationRepository | None = None,
        event_tracking_service: EventTrackingService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.product_repository = product_repository
        self.favorite_repository = favorite_repository
        self.cosmetic_bag_repository = cosmetic_bag_repository
        self.recommendation_repository = recommendation_repository
        self.event_tracking_service = event_tracking_service

    async def get_me(self, user: dict) -> UserResponse:
        return UserResponse(**user)

    async def update_me(
        self,
        user: dict,
        payload: UserUpdate,
    ) -> UserResponse | None:
        updated = await self.user_repository.update_user(
            user_id=user["user_id"],
            full_name=payload.full_name,
            anonymous_id=payload.anonymous_id,
        )

        if updated is None:
            return None

        await self.profile_repository.sync_anonymous_id(
            user_id=updated["user_id"],
            anonymous_id=updated.get("anonymous_id"),
        )

        return UserResponse(**updated)

    async def get_my_profile(self, user: dict) -> UserProfileResponse:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        return UserProfileResponse(**profile)

    async def update_my_profile(
        self,
        user: dict,
        payload: UserProfileUpdate,
    ) -> UserProfileResponse | None:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        payload_data = payload.model_dump()
        updated = await self.profile_repository.update_profile(
            user_id=profile["user_id"],
            payload=payload_data,
        )

        if updated is None:
            return None

        if self.event_tracking_service is not None:
            fields_updated = sorted(key for key, value in payload_data.items() if value is not None)
            await self.event_tracking_service.record(
                AnalyticsEventType.PROFILE_SAVED,
                user_id=user["user_id"],
                anonymous_id=user.get("anonymous_id"),
                metadata={
                    "source": "profile_update",
                    "fields_updated": fields_updated,
                    "skin_type": updated.get("skin_type"),
                    "concern_count": len(updated.get("concerns") or []),
                    "restriction_count": len(
                        [
                            *(updated.get("excluded_ingredients") or []),
                            *(updated.get("custom_restrictions") or []),
                        ]
                    ),
                },
            )

        return UserProfileResponse(**updated)

    async def list_favorites(self, user: dict) -> FavoriteProductListResponse:
        if self.favorite_repository is None or self.product_repository is None:
            raise RuntimeError("Favorite repositories are not configured")

        favorites = await self.favorite_repository.list_for_user(user["user_id"])
        products = await self.product_repository.find_by_external_ids(
            [favorite["product_external_id"] for favorite in favorites]
        )
        items: list[FavoriteProductResponse] = []
        for favorite in favorites:
            product = products.get(favorite["product_external_id"])
            if product is None:
                continue
            items.append(
                FavoriteProductResponse(
                    product=ProductResponse(**product),
                    created_at=favorite["created_at"],
                )
            )
        return FavoriteProductListResponse(items=items, total=len(items))

    async def add_favorite(
        self,
        user: dict,
        product_external_id: str,
    ) -> FavoriteProductResponse | None:
        if self.favorite_repository is None or self.product_repository is None:
            raise RuntimeError("Favorite repositories are not configured")

        product = await self.product_repository.find_by_external_id(product_external_id)
        if product is None:
            return None
        favorite = await self.favorite_repository.upsert(
            user["user_id"],
            product_external_id,
        )
        return FavoriteProductResponse(
            product=ProductResponse(**product),
            created_at=favorite["created_at"],
        )

    async def remove_favorite(self, user: dict, product_external_id: str) -> bool:
        if self.favorite_repository is None:
            raise RuntimeError("Favorite repository is not configured")
        return await self.favorite_repository.remove(
            user["user_id"],
            product_external_id,
        )

    async def list_cosmetic_bag(self, user: dict) -> CosmeticBagProductListResponse:
        if self.cosmetic_bag_repository is None or self.product_repository is None:
            raise RuntimeError("Cosmetic bag repositories are not configured")

        saved_items = await self.cosmetic_bag_repository.list_for_user(user["user_id"])
        products = await self.product_repository.find_by_external_ids(
            [saved_item["product_external_id"] for saved_item in saved_items]
        )
        items: list[CosmeticBagProductResponse] = []
        for saved_item in saved_items:
            product = products.get(saved_item["product_external_id"])
            if product is None:
                continue
            items.append(
                CosmeticBagProductResponse(
                    product=ProductResponse(**product),
                    created_at=saved_item["created_at"],
                )
            )
        return CosmeticBagProductListResponse(items=items, total=len(items))

    async def add_to_cosmetic_bag(
        self,
        user: dict,
        product_external_id: str,
    ) -> CosmeticBagProductResponse | None:
        if self.cosmetic_bag_repository is None or self.product_repository is None:
            raise RuntimeError("Cosmetic bag repositories are not configured")

        product = await self.product_repository.find_by_external_id(product_external_id)
        if product is None:
            return None
        saved_item = await self.cosmetic_bag_repository.upsert(
            user["user_id"],
            product_external_id,
        )
        return CosmeticBagProductResponse(
            product=ProductResponse(**product),
            created_at=saved_item["created_at"],
        )

    async def remove_from_cosmetic_bag(
        self,
        user: dict,
        product_external_id: str,
    ) -> bool:
        if self.cosmetic_bag_repository is None:
            raise RuntimeError("Cosmetic bag repository is not configured")
        return await self.cosmetic_bag_repository.remove(
            user["user_id"],
            product_external_id,
        )

    async def clear_cosmetic_bag(self, user: dict) -> int:
        if self.cosmetic_bag_repository is None:
            raise RuntimeError("Cosmetic bag repository is not configured")
        return await self.cosmetic_bag_repository.clear(user["user_id"])

    async def recommendation_history(
        self,
        user: dict,
        *,
        limit: int,
        offset: int,
    ) -> RecommendationHistoryResponse:
        if self.recommendation_repository is None:
            raise RuntimeError("Recommendation repository is not configured")
        documents, total = await self.recommendation_repository.list_by_user_id(
            user["user_id"],
            limit=limit,
            offset=offset,
        )
        items = [
            RecommendationResponse(
                recommendation_id=document["recommendation_id"],
                **document["result"],
            )
            for document in documents
        ]
        return RecommendationHistoryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def append_questionnaire_history(
        self,
        user: dict,
        payload: QuestionnaireHistoryCreate,
    ) -> UserProfileResponse | None:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        updated = await self.profile_repository.append_questionnaire_history(
            user_id=profile["user_id"],
            entry=payload.model_dump(),
        )

        if updated is None:
            return None

        if self.event_tracking_service is not None:
            await self.event_tracking_service.record(
                AnalyticsEventType.PROFILE_SAVED,
                user_id=user["user_id"],
                anonymous_id=user.get("anonymous_id"),
                recommendation_id=payload.recommendation_id,
                metadata={
                    "source": "questionnaire_history",
                    "history_size": len(updated.get("questionnaire_history") or []),
                },
            )

        return UserProfileResponse(**updated)
