from hashlib import sha1

from app.repositories.restriction_repository import RestrictionRepository
from app.schemas.restriction import (
    CustomRestrictionCreate,
    CustomRestrictionResponse,
    RestrictionSuggestionResponse,
)


class RestrictionService:
    def __init__(self, repository: RestrictionRepository) -> None:
        self.repository = repository

    async def get_popular_suggestions(self) -> list[RestrictionSuggestionResponse]:
        documents = await self.repository.list_popular_suggestions()
        return [RestrictionSuggestionResponse(**document) for document in documents]

    async def add_custom_restriction(
        self,
        payload: CustomRestrictionCreate,
    ) -> CustomRestrictionResponse:
        raw_value = payload.value.strip()
        normalized_input = raw_value.lower()

        alias = await self.repository.find_alias(normalized_input)

        if alias is not None:
            canonical_key = alias["canonical_key"]
            display_name = alias["display_name"]
            status = "approved"
            is_popular = True
        else:
            canonical_key = "custom_" + sha1(normalized_input.encode("utf-8")).hexdigest()[:12]
            display_name = raw_value
            status = "pending"
            is_popular = False

        await self.repository.record_custom_restriction(
            raw_value=raw_value,
            normalized_key=canonical_key,
            anonymous_id=payload.anonymous_id,
        )

        await self.repository.upsert_suggestion_usage(
            canonical_key=canonical_key,
            display_name=display_name,
            status=status,
            is_popular=is_popular,
        )

        return CustomRestrictionResponse(
            raw_value=raw_value,
            normalized_key=canonical_key,
            display_name=display_name,
            status=status,
            added_to_popular=is_popular,
        )
