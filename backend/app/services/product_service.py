from collections import Counter
from math import ceil
from typing import Literal

from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    CatalogFacetValue,
    CatalogIssue,
    ProductCatalogFacets,
    ProductCatalogIssueItem,
    ProductCatalogIssueResponse,
    ProductCatalogQualityResponse,
    ProductCatalogResponse,
    ProductResponse,
)

KNOWN_IRRITANT_FLAGS = {
    "contains_alcohol",
    "contains_essential_oils",
    "contains_fragrance",
}


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    async def list_products(
        self,
        routine_step: str | None = None,
        budget_segment: str | None = None,
    ) -> list[dict]:
        return await self.repository.list_active_products(
            routine_step=routine_step,
            budget_segment=budget_segment,
        )

    async def get_product(self, external_id: str) -> dict | None:
        return await self.repository.find_by_external_id(external_id)

    async def catalog(
        self,
        *,
        search: str | None,
        routine_steps: list[str],
        budget_segments: list[str],
        skin_types: list[str],
        concerns: list[str],
        values: list[str],
        min_price_rub: int | None,
        max_price_rub: int | None,
        no_known_irritants: bool,
        sort: Literal["relevance", "price_asc", "price_desc", "name"],
        page: int,
        page_size: int,
    ) -> ProductCatalogResponse:
        products = await self.repository.list_active_products()
        query = str(search or "").strip().casefold()

        def includes_all(product_values: list[str], selected: list[str]) -> bool:
            return not selected or set(selected).issubset(set(product_values or []))

        def matches(product: dict) -> bool:
            if routine_steps and product.get("routine_step") not in routine_steps:
                return False
            if budget_segments and product.get("budget_segment") not in budget_segments:
                return False
            product_skin_types = product.get("skin_types") or []
            if skin_types and not (
                set(skin_types).intersection(product_skin_types) or "all" in product_skin_types
            ):
                return False
            if concerns and not set(concerns).intersection(product.get("concerns") or []):
                return False
            if not includes_all(product.get("values") or [], values):
                return False
            price = int(product.get("price_rub", 0) or 0)
            if min_price_rub is not None and price < min_price_rub:
                return False
            if max_price_rub is not None and price > max_price_rub:
                return False
            if no_known_irritants and set(product.get("risk_flags") or []).intersection(
                KNOWN_IRRITANT_FLAGS
            ):
                return False
            if query:
                searchable = " ".join(
                    [
                        str(product.get("name") or ""),
                        str(product.get("brand") or ""),
                        str(product.get("category") or ""),
                        str(product.get("description") or ""),
                        *(str(value) for value in product.get("key_ingredients") or []),
                        *(str(value) for value in product.get("ingredients") or []),
                    ]
                ).casefold()
                if query not in searchable:
                    return False
            return True

        filtered = [product for product in products if matches(product)]

        if sort == "price_asc":
            filtered.sort(key=lambda item: (int(item.get("price_rub", 0)), item["external_id"]))
        elif sort == "price_desc":
            filtered.sort(key=lambda item: (-int(item.get("price_rub", 0)), item["external_id"]))
        elif sort == "name":
            filtered.sort(
                key=lambda item: (str(item.get("name", "")).casefold(), item["external_id"])
            )
        elif query:
            filtered.sort(
                key=lambda item: (
                    0 if str(item.get("name", "")).casefold().startswith(query) else 1,
                    0 if query in str(item.get("brand", "")).casefold() else 1,
                    int(item.get("price_rub", 0)),
                    item["external_id"],
                )
            )
        else:
            filtered = self._interleave_routine_steps(filtered)

        total = len(filtered)
        offset = (page - 1) * page_size
        page_items = filtered[offset : offset + page_size]

        return ProductCatalogResponse(
            items=[ProductResponse(**product) for product in page_items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
            facets=self._facets(filtered),
        )

    async def catalog_quality(self) -> ProductCatalogQualityResponse:
        products = await self.repository.list_all_products()
        required_fields = (
            "external_id",
            "name",
            "brand",
            "routine_step",
            "price_rub",
            "description",
            "how_to_use",
            "ingredients",
        )
        missing = Counter(
            field
            for product in products
            for field in required_fields
            if product.get(field) in (None, "", [])
        )
        possible = len(products) * len(required_fields)
        completeness = 100.0
        if possible:
            completeness = round((1 - sum(missing.values()) / possible) * 100, 2)

        active = [product for product in products if product.get("is_active", True)]
        dataset_count = sum(product.get("source") == "dataset" for product in products)

        def coverage(field: str) -> float:
            if not products:
                return 0.0
            populated = sum(product.get(field) not in (None, "", []) for product in products)
            return round(populated / len(products) * 100, 2)

        import_dates = [
            product.get("imported_at")
            for product in products
            if product.get("imported_at") is not None
        ]

        return ProductCatalogQualityResponse(
            total_products=len(products),
            active_products=len(active),
            inactive_products=len(products) - len(active),
            dataset_products=dataset_count,
            strict_dataset_ok=dataset_count == len(products) and bool(products),
            step_counts=dict(
                sorted(
                    Counter(product.get("routine_step") or "unknown" for product in active).items()
                )
            ),
            budget_counts=dict(
                sorted(
                    Counter(
                        product.get("budget_segment") or "unknown" for product in active
                    ).items()
                )
            ),
            risk_flag_counts=dict(
                sorted(
                    Counter(
                        flag for product in active for flag in product.get("risk_flags") or []
                    ).items()
                )
            ),
            missing_field_counts=dict(sorted(missing.items())),
            completeness_percent=completeness,
            image_coverage_percent=coverage("image_url"),
            product_link_coverage_percent=coverage("product_url"),
            usage_coverage_percent=coverage("how_to_use"),
            last_imported_at=max(import_dates, default=None),
        )

    async def catalog_issues(
        self,
        *,
        issue: CatalogIssue,
        search: str | None,
        page: int,
        page_size: int,
    ) -> ProductCatalogIssueResponse:
        products = await self.repository.list_all_products()
        query = str(search or "").strip().casefold()

        def issues_for(product: dict) -> list[str]:
            issues: list[str] = []
            if not product.get("is_active", True):
                issues.append("inactive")
            if not product.get("ingredients"):
                issues.append("missing_ingredients")
            if not str(product.get("how_to_use") or "").strip():
                issues.append("missing_usage")
            if not str(product.get("image_url") or "").strip():
                issues.append("missing_image")
            if not str(product.get("product_url") or "").strip():
                issues.append("missing_product_link")
            return issues

        rows: list[ProductCatalogIssueItem] = []
        for product in products:
            product_issues = issues_for(product)
            if not product_issues:
                continue
            if issue != "all" and issue not in product_issues:
                continue
            searchable = " ".join(
                [
                    str(product.get("external_id") or ""),
                    str(product.get("name") or ""),
                    str(product.get("brand") or ""),
                ]
            ).casefold()
            if query and query not in searchable:
                continue
            rows.append(
                ProductCatalogIssueItem(
                    external_id=product["external_id"],
                    name=product["name"],
                    brand=product["brand"],
                    routine_step=product["routine_step"],
                    is_active=product.get("is_active", True),
                    issues=product_issues,
                    description=str(product.get("description") or ""),
                    how_to_use=str(product.get("how_to_use") or ""),
                    image_url=product.get("image_url") or None,
                    product_url=product.get("product_url") or None,
                )
            )

        rows.sort(key=lambda item: (-len(item.issues), item.external_id))
        total = len(rows)
        offset = (page - 1) * page_size
        return ProductCatalogIssueResponse(
            items=rows[offset : offset + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )

    @staticmethod
    def _interleave_routine_steps(products: list[dict]) -> list[dict]:
        """Keep the default catalog useful without pretending to personalize it."""

        preferred_order = (
            "cleanser",
            "toner",
            "serum",
            "treatment",
            "moisturizer",
            "spf",
            "exfoliation",
            "mask",
        )
        groups: dict[str, list[dict]] = {}
        for product in products:
            groups.setdefault(str(product.get("routine_step") or "other"), []).append(product)
        for group in groups.values():
            group.sort(key=lambda item: str(item.get("external_id") or ""))

        ordered_steps = [step for step in preferred_order if step in groups]
        ordered_steps.extend(sorted(set(groups) - set(ordered_steps)))
        interleaved: list[dict] = []
        for index in range(max((len(group) for group in groups.values()), default=0)):
            interleaved.extend(
                groups[step][index] for step in ordered_steps if index < len(groups[step])
            )
        return interleaved

    @staticmethod
    def _facets(products: list[dict]) -> ProductCatalogFacets:
        def values(field: str, *, scalar: bool = False) -> list[CatalogFacetValue]:
            counter: Counter[str] = Counter()
            for product in products:
                raw = product.get(field)
                source = [raw] if scalar else (raw or [])
                for value in source:
                    if value:
                        counter[str(value)] += 1
            return [
                CatalogFacetValue(value=value, count=count)
                for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
            ]

        prices = [int(product.get("price_rub", 0) or 0) for product in products]
        return ProductCatalogFacets(
            routine_steps=values("routine_step", scalar=True),
            budget_segments=values("budget_segment", scalar=True),
            skin_types=values("skin_types"),
            concerns=values("concerns"),
            values=values("values"),
            textures=values("texture", scalar=True),
            min_price_rub=min(prices, default=0),
            max_price_rub=max(prices, default=0),
        )
