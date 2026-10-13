from app.services.catalog_metadata import (
    canonical_product_url,
    extract_catalog_metadata,
    is_supported_product_url,
)


def test_extracts_product_json_ld_price_and_image() -> None:
    html = """
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "image": ["/media/product.webp"],
        "offers": {"@type": "Offer", "price": "1 249,00", "priceCurrency": "RUB"}
      }
    </script>
    """

    result = extract_catalog_metadata(
        html,
        page_url="https://www.pleyana.com/catalog/product/",
        current_price_rub=1200,
    )

    assert result.price_rub == 1249
    assert result.image_url == "https://www.pleyana.com/media/product.webp"
    assert result.price_candidates == [1249]


def test_prefers_variant_closest_to_catalog_price() -> None:
    html = """
    <meta property="og:image" content="https://static.siberianhealth.com/a.jpg">
    <meta itemprop="priceCurrency" content="RUB">
    <meta itemprop="price" content="743">
    <meta itemprop="price" content="1166">
    """

    result = extract_catalog_metadata(
        html,
        page_url="https://www.pleyana.com/catalog/product/",
        current_price_rub=760,
    )

    assert result.price_rub == 743
    assert result.price_candidates == [743, 1166]
    assert "multiple_price_variants" in result.warnings


def test_ignores_non_ruble_offer_price() -> None:
    html = """
    <script type="application/ld+json">
      {"@type":"Product","offers":{"price":"19.99","priceCurrency":"USD"}}
    </script>
    """

    result = extract_catalog_metadata(
        html,
        page_url="https://goldapple.ru/product",
        current_price_rub=1500,
    )

    assert result.price_rub is None
    assert "non_rub_offer_ignored" in result.warnings


def test_product_urls_are_canonical_and_restricted_to_supported_hosts() -> None:
    canonical = canonical_product_url("goldapple.ru/19000041345-sensibio")

    assert canonical == "https://goldapple.ru/19000041345-sensibio"
    assert is_supported_product_url(canonical)
    assert is_supported_product_url(
        "https://aravia.ru/catalog/hyaluronic_micellar_water/"
    )
    assert is_supported_product_url(
        "https://www.pharmacosmetica.ru/eshop/product_id_123.html"
    )
    assert is_supported_product_url(
        "https://geltek.ru/catalog/product/blemish-control/"
    )
    assert is_supported_product_url(
        "https://www.cosrx.com/products/low-ph-good-morning-gel-cleanser"
    )
    assert is_supported_product_url(
        "https://somebymicosmetics.com/en/miracle-serum/SBM0016"
    )
    assert is_supported_product_url(
        "https://maskshop.ru/catalog/some-by-mi-miracle-serum/"
    )
    assert is_supported_product_url(
        "https://dtmskin.com/product/moisturizer_rich"
    )
    assert is_supported_product_url(
        "https://www.krason.ru/818-beauty-formula/767/p73959"
    )
    assert is_supported_product_url(
        "https://fitomarket.ru/catalog/face/toners/round-lab-birch/"
    )
    assert is_supported_product_url(
        "https://koreanbutik.ru/product/cosrx-snail-essence"
    )
    assert is_supported_product_url("https://www.manyo.ru/sleepingmask")
    assert is_supported_product_url(
        "https://hollyshop.ru/catalog/product/skin1004-centella/"
    )
    assert is_supported_product_url(
        "https://mixit.ru/product/skin-chemistry-bifida-barrier-serum/"
    )
    assert is_supported_product_url(
        "https://levrana.ru/catalog/kosmetika/dlya_litsa/magiya_true_alchemy/656/"
    )
    assert is_supported_product_url(
        "https://rivegauche.ru/product/cosrx-refresh-aha-bha-vitamin-c-daily-toner-150"
    )
    assert is_supported_product_url(
        "https://medipeel.ru/catalog/ukhod-za-kozhey/apple-tox-pore-toner"
    )
    assert is_supported_product_url(
        "https://christinacosmetics.ru/shop/linija-kosmetiki/forever-young/toner/"
    )
    assert is_supported_product_url(
        "https://krygina.com/exfoliating-toner-200-ml/"
    )
    assert is_supported_product_url(
        "https://laboratorium.store/collection/maski/product/niacinamide-mask"
    )
    assert is_supported_product_url("https://www.proficosmetics.ru/catalog/3146366/")
    assert is_supported_product_url("https://elize.ru/shop/product_real/103444/")
    assert is_supported_product_url(
        "https://apteka.ru/product/the-u-krem-s-czentelloj-keep-calm-cream-50-ml/"
    )
    assert is_supported_product_url(
        "https://gum.ru/shop/product/dermaclear-cleansing-foam-763534/"
    )
    assert is_supported_product_url("https://cibum.ru/product/show/50015509")
    assert is_supported_product_url(
        "https://maskoholic.com/katalog/toniki/tproduct/648398163-922133291432-tonik"
    )
    assert is_supported_product_url(
        "https://www.tsum.ru/product/he00888541-dermaclear-120ml-dr-jart/"
    )
    assert not is_supported_product_url("https://goldapple.ru")
    assert not is_supported_product_url("https://geltek.ru/catalog/")
    assert not is_supported_product_url("https://ru.siberianhealth.com")
    assert not is_supported_product_url("https://www.manyo.ru")
    assert not is_supported_product_url("https://mixit.ru/catalog/serums/")
    assert not is_supported_product_url("https://levrana.ru/catalog/kosmetika/")
    assert not is_supported_product_url("https://krygina.com/catalog/")
    assert not is_supported_product_url("https://apteka.ru/product/")
    assert not is_supported_product_url("https://cibum.ru/product/show/")
    assert not is_supported_product_url("https://maskoholic.com/katalog/toniki")
    assert not is_supported_product_url("https://www.tsum.ru/catalog/ukhod-za-kozhey/")
    assert not is_supported_product_url("https://example.com/product")
    assert canonical_product_url("http://127.0.0.1/private") is None
    assert canonical_product_url("javascript:alert(1)") is None
