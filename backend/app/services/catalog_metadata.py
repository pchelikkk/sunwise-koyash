from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

SUPPORTED_PRODUCT_HOSTS = frozenset(
    {
        "goldapple.ru",
        "www.goldapple.ru",
        "aravia.ru",
        "www.aravia.ru",
        "www.pharmacosmetica.ru",
        "pharmacosmetica.ru",
        "www.art-fact-products.com",
        "art-fact-products.com",
        "geltek.ru",
        "www.geltek.ru",
        "www.cosrx.com",
        "cosrx.com",
        "somebymicosmetics.com",
        "www.somebymicosmetics.com",
        "maskshop.ru",
        "www.maskshop.ru",
        "dtmskin.com",
        "www.dtmskin.com",
        "krason.ru",
        "www.krason.ru",
        "fitomarket.ru",
        "www.fitomarket.ru",
        "koreanbutik.ru",
        "www.koreanbutik.ru",
        "manyo.ru",
        "www.manyo.ru",
        "hollyshop.ru",
        "www.hollyshop.ru",
        "mixit.ru",
        "www.mixit.ru",
        "levrana.ru",
        "www.levrana.ru",
        "rivegauche.ru",
        "www.rivegauche.ru",
        "pleyana.com",
        "www.pleyana.com",
        "ru.siberianhealth.com",
        "medipeel.ru",
        "www.medipeel.ru",
        "christinacosmetics.ru",
        "www.christinacosmetics.ru",
        "krygina.com",
        "www.krygina.com",
        "the-u.ru",
        "www.the-u.ru",
        "laboratorium.store",
        "www.laboratorium.store",
        "proficosmetics.ru",
        "www.proficosmetics.ru",
        "elize.ru",
        "www.elize.ru",
        "ashaindia.ru",
        "www.ashaindia.ru",
        "apteka.ru",
        "www.apteka.ru",
        "gum.ru",
        "www.gum.ru",
        "cibum.ru",
        "www.cibum.ru",
        "maskoholic.com",
        "www.maskoholic.com",
        "tsum.ru",
        "www.tsum.ru",
    }
)

_PRODUCT_PATH_PATTERNS = {
    "goldapple.ru": re.compile(r"^/\d+-[^/]+/?$"),
    "www.goldapple.ru": re.compile(r"^/\d+-[^/]+/?$"),
    "aravia.ru": re.compile(r"^/catalog/[^/]+/?$"),
    "www.aravia.ru": re.compile(r"^/catalog/[^/]+/?$"),
    "www.pharmacosmetica.ru": re.compile(r"^/eshop/.+_id_\d+\.html/?$"),
    "pharmacosmetica.ru": re.compile(r"^/eshop/.+_id_\d+\.html/?$"),
    "www.art-fact-products.com": re.compile(r"^/product/[^/]+/?$"),
    "art-fact-products.com": re.compile(r"^/product/[^/]+/?$"),
    "geltek.ru": re.compile(r"^/catalog/product/[^/]+/?$"),
    "www.geltek.ru": re.compile(r"^/catalog/product/[^/]+/?$"),
    "www.cosrx.com": re.compile(r"^/products/[^/]+/?$"),
    "cosrx.com": re.compile(r"^/products/[^/]+/?$"),
    "somebymicosmetics.com": re.compile(r"^/(?:en/)?[^/]+/[^/]+/?$"),
    "www.somebymicosmetics.com": re.compile(r"^/(?:en/)?[^/]+/[^/]+/?$"),
    "maskshop.ru": re.compile(r"^/catalog/[^/]+/?$"),
    "www.maskshop.ru": re.compile(r"^/catalog/[^/]+/?$"),
    "dtmskin.com": re.compile(r"^/product/[^/]+/?$"),
    "www.dtmskin.com": re.compile(r"^/product/[^/]+/?$"),
    "krason.ru": re.compile(r"^/[^/]+/\d+/p\d+/?$"),
    "www.krason.ru": re.compile(r"^/[^/]+/\d+/p\d+/?$"),
    "fitomarket.ru": re.compile(r"^/catalog/.+/?$"),
    "www.fitomarket.ru": re.compile(r"^/catalog/.+/?$"),
    "koreanbutik.ru": re.compile(r"^/product/[^/]+/?$"),
    "www.koreanbutik.ru": re.compile(r"^/product/[^/]+/?$"),
    "manyo.ru": re.compile(r"^/[^/]+/?$"),
    "www.manyo.ru": re.compile(r"^/[^/]+/?$"),
    "hollyshop.ru": re.compile(r"^/catalog/product/[^/]+/?$"),
    "www.hollyshop.ru": re.compile(r"^/catalog/product/[^/]+/?$"),
    "mixit.ru": re.compile(r"^/product/[^/]+/?$"),
    "www.mixit.ru": re.compile(r"^/product/[^/]+/?$"),
    "levrana.ru": re.compile(r"^/catalog/.+/\d+/?$"),
    "www.levrana.ru": re.compile(r"^/catalog/.+/\d+/?$"),
    "rivegauche.ru": re.compile(r"^/product/[^/]+/?$"),
    "www.rivegauche.ru": re.compile(r"^/product/[^/]+/?$"),
    "pleyana.com": re.compile(r"^/catalog/[^/]+/.+"),
    "www.pleyana.com": re.compile(r"^/catalog/[^/]+/.+"),
    "ru.siberianhealth.com": re.compile(r"^/ru/shop/catalog/product/\d+/?$"),
    "medipeel.ru": re.compile(r"^/catalog/.+/?$"),
    "www.medipeel.ru": re.compile(r"^/catalog/.+/?$"),
    "christinacosmetics.ru": re.compile(r"^/shop/.+/?$"),
    "www.christinacosmetics.ru": re.compile(r"^/shop/.+/?$"),
    "krygina.com": re.compile(
        r"^/[a-z0-9-]+(?:toner|cream|serum|cleanser|mask|spf)[a-z0-9-]*/?$"
    ),
    "www.krygina.com": re.compile(
        r"^/[a-z0-9-]+(?:toner|cream|serum|cleanser|mask|spf)[a-z0-9-]*/?$"
    ),
    "the-u.ru": re.compile(r"^/catalog/.+/?$"),
    "www.the-u.ru": re.compile(r"^/catalog/.+/?$"),
    "laboratorium.store": re.compile(r"^/collection/[^/]+/product/[^/]+/?$"),
    "www.laboratorium.store": re.compile(r"^/collection/[^/]+/product/[^/]+/?$"),
    "proficosmetics.ru": re.compile(r"^/catalog/\d+/?$"),
    "www.proficosmetics.ru": re.compile(r"^/catalog/\d+/?$"),
    "elize.ru": re.compile(r"^/shop/product_real/\d+/?$"),
    "www.elize.ru": re.compile(r"^/shop/product_real/\d+/?$"),
    "ashaindia.ru": re.compile(r"^/[^/]+/?$"),
    "www.ashaindia.ru": re.compile(r"^/[^/]+/?$"),
    "apteka.ru": re.compile(r"^/product/[^/]+/?$"),
    "www.apteka.ru": re.compile(r"^/product/[^/]+/?$"),
    "gum.ru": re.compile(r"^/shop/product/[^/]+/?$"),
    "www.gum.ru": re.compile(r"^/shop/product/[^/]+/?$"),
    "cibum.ru": re.compile(r"^/product/show/\d+/?$"),
    "www.cibum.ru": re.compile(r"^/product/show/\d+/?$"),
    "maskoholic.com": re.compile(r"^/katalog/[^/]+/tproduct/\d+-[^/]+/?$"),
    "www.maskoholic.com": re.compile(r"^/katalog/[^/]+/tproduct/\d+-[^/]+/?$"),
    "tsum.ru": re.compile(r"^/product/[^/]+/?$"),
    "www.tsum.ru": re.compile(r"^/product/[^/]+/?$"),
}

_PRICE_PATTERN = re.compile(r"\d[\d\s\u00a0]*(?:[.,]\d{1,2})?")


@dataclass(slots=True)
class CatalogPageMetadata:
    price_rub: int | None = None
    image_url: str | None = None
    price_candidates: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}
        self.json_ld: list[str] = []
        self._json_ld_buffer: list[str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {
            str(key).lower(): str(value or "").strip() for key, value in attrs
        }
        if tag.lower() == "meta":
            key = (
                attributes.get("property")
                or attributes.get("name")
                or attributes.get("itemprop")
            )
            content = attributes.get("content")
            if key and content:
                self.meta.setdefault(key.lower(), []).append(content)
        if (
            tag.lower() == "script"
            and attributes.get("type", "").lower() == "application/ld+json"
        ):
            self._json_ld_buffer = []

    def handle_data(self, data: str) -> None:
        if self._json_ld_buffer is not None:
            self._json_ld_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._json_ld_buffer is not None:
            payload = "".join(self._json_ld_buffer).strip()
            if payload:
                self.json_ld.append(payload)
            self._json_ld_buffer = None


def canonical_product_url(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    initial = urlparse(raw)
    if initial.scheme and initial.scheme not in {"http", "https"}:
        return None
    if "://" not in raw:
        raw = f"https://{raw.lstrip('/')}"
    parsed = urlparse(raw)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return None
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        address = None
    if address and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
    ):
        return None
    return raw


def is_supported_product_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    pattern = _PRODUCT_PATH_PATTERNS.get(hostname)
    return hostname in SUPPORTED_PRODUCT_HOSTS and bool(
        pattern and pattern.match(parsed.path)
    )


def _parse_price(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        result = int(round(float(value)))
        return result if 0 < result <= 10_000_000 else None
    match = _PRICE_PATTERN.search(str(value))
    if not match:
        return None
    normalized = match.group(0).replace("\u00a0", "").replace(" ", "")
    if "," in normalized and "." not in normalized:
        normalized = normalized.replace(",", ".")
    try:
        result = int(round(float(normalized)))
    except ValueError:
        return None
    return result if 0 < result <= 10_000_000 else None


def _iter_nodes(value: Any) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    if isinstance(value, dict):
        nodes.append(value)
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                nodes.extend(_iter_nodes(nested))
    elif isinstance(value, list):
        for nested in value:
            nodes.extend(_iter_nodes(nested))
    return nodes


def _is_product(node: dict[str, Any]) -> bool:
    node_type = node.get("@type")
    values = node_type if isinstance(node_type, list) else [node_type]
    return any(str(value).lower() == "product" for value in values)


def _append_prices(target: list[int], values: Any) -> None:
    candidates = values if isinstance(values, list) else [values]
    for value in candidates:
        parsed = _parse_price(value)
        if parsed is not None and parsed not in target:
            target.append(parsed)


def _append_images(target: list[str], values: Any, page_url: str) -> None:
    candidates = values if isinstance(values, list) else [values]
    for value in candidates:
        if isinstance(value, dict):
            value = value.get("url") or value.get("contentUrl")
        raw = str(value or "").strip()
        if not raw:
            continue
        url = canonical_product_url(urljoin(page_url, raw))
        if url and url not in target:
            target.append(url)


def extract_catalog_metadata(
    html: str,
    *,
    page_url: str,
    current_price_rub: int | None = None,
) -> CatalogPageMetadata:
    parser = _MetadataParser()
    parser.feed(html)

    json_prices: list[int] = []
    meta_prices: list[int] = []
    images: list[str] = []
    warnings: list[str] = []

    for payload in parser.json_ld:
        try:
            decoded = json.loads(payload)
        except (TypeError, ValueError):
            warnings.append("invalid_json_ld")
            continue
        for node in _iter_nodes(decoded):
            if not _is_product(node):
                continue
            _append_images(images, node.get("image"), page_url)
            offers = node.get("offers")
            offer_nodes = offers if isinstance(offers, list) else [offers]
            for offer in offer_nodes:
                if not isinstance(offer, dict):
                    continue
                currency = str(offer.get("priceCurrency") or "").upper()
                if currency and currency not in {"RUB", "RUR"}:
                    warnings.append("non_rub_offer_ignored")
                    continue
                _append_prices(
                    json_prices,
                    offer.get("price") or offer.get("lowPrice"),
                )

    for key in ("og:image", "twitter:image", "twitter:image:src", "image"):
        _append_images(images, parser.meta.get(key, []), page_url)

    currencies = {
        currency.upper()
        for key in ("product:price:currency", "pricecurrency")
        for currency in parser.meta.get(key, [])
        if currency
    }
    if not currencies or currencies.intersection({"RUB", "RUR"}):
        for key in (
            "product:price:amount",
            "price",
            "lowprice",
            "highprice",
        ):
            _append_prices(meta_prices, parser.meta.get(key, []))
    else:
        warnings.append("non_rub_meta_price_ignored")

    prices = list(dict.fromkeys([*json_prices, *meta_prices]))
    selected_price: int | None = None
    if prices:
        if current_price_rub and current_price_rub > 0:
            selected_price = min(
                prices,
                key=lambda price: (abs(price - current_price_rub), price),
            )
        else:
            selected_price = prices[0]
        if len(prices) > 1:
            warnings.append("multiple_price_variants")

    return CatalogPageMetadata(
        price_rub=selected_price,
        image_url=images[0] if images else None,
        price_candidates=prices,
        warnings=list(dict.fromkeys(warnings)),
    )
