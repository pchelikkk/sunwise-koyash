from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.dependencies import get_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
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
from app.schemas.user import (
    QuestionnaireHistoryCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.event_tracking_service import EventTrackingService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> UserService:
    return UserService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
        product_repository=ProductRepository(database),
        favorite_repository=FavoriteRepository(database),
        cosmetic_bag_repository=CosmeticBagRepository(database),
        recommendation_repository=RecommendationRepository(database),
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await service.get_me(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    result = await service.update_me(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return result


@router.get("/me/favorites", response_model=FavoriteProductListResponse)
async def list_favorites(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> FavoriteProductListResponse:
    return await service.list_favorites(current_user)


@router.put(
    "/me/favorites/{product_external_id}",
    response_model=FavoriteProductResponse,
)
async def add_favorite(
    product_external_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> FavoriteProductResponse:
    result = await service.add_favorite(current_user, product_external_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return result


@router.delete(
    "/me/favorites/{product_external_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_favorite(
    product_external_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    await service.remove_favorite(current_user, product_external_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/cosmetic-bag", response_model=CosmeticBagProductListResponse)
async def list_cosmetic_bag(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> CosmeticBagProductListResponse:
    return await service.list_cosmetic_bag(current_user)


@router.put(
    "/me/cosmetic-bag/{product_external_id}",
    response_model=CosmeticBagProductResponse,
)
async def add_to_cosmetic_bag(
    product_external_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> CosmeticBagProductResponse:
    result = await service.add_to_cosmetic_bag(current_user, product_external_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return result


@router.delete(
    "/me/cosmetic-bag/{product_external_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_from_cosmetic_bag(
    product_external_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    await service.remove_from_cosmetic_bag(current_user, product_external_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/me/cosmetic-bag",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cosmetic_bag(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    await service.clear_cosmetic_bag(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/recommendations", response_model=RecommendationHistoryResponse)
async def recommendation_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RecommendationHistoryResponse:
    return await service.recommendation_history(
        current_user,
        limit=limit,
        offset=offset,
    )


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfileResponse:
    return await service.get_my_profile(current_user)


@router.patch("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfileResponse:
    result = await service.update_my_profile(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return result


@router.post("/me/profile/questionnaire-history", response_model=UserProfileResponse)
async def append_questionnaire_history(
    payload: QuestionnaireHistoryCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfileResponse:
    result = await service.append_questionnaire_history(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return result
