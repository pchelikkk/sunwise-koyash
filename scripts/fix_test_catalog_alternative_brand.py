from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(r"C:\Projects\sunwise-koyash")
CATALOG_PATH = ROOT / "backend/app/seed/test_catalog.py"
TEST_PATH = ROOT / "backend/tests/test_test_catalog_contract.py"

TARGET_EXTERNAL_ID = "cleanser_002"
TARGET_BRAND = "KOYASH Alternative Test"


def line_offsets(text: str) -> list[int]:
    offsets = [0]

    for index, character in enumerate(text):
        if character == "\n":
            offsets.append(index + 1)

    return offsets


text = CATALOG_PATH.read_text(encoding="utf-8-sig")
tree = ast.parse(text)

target_call: ast.Call | None = None

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue

    if not node.args:
        continue

    first_argument = node.args[0]

    if (
        isinstance(first_argument, ast.Constant)
        and first_argument.value == TARGET_EXTERNAL_ID
    ):
        target_call = node
        break

if target_call is None:
    raise RuntimeError(
        "Could not find cleanser_002 in backend/app/seed/test_catalog.py"
    )

brand_keyword = next(
    (
        keyword
        for keyword in target_call.keywords
        if keyword.arg == "brand"
    ),
    None,
)

if brand_keyword is None:
    if target_call.end_lineno is None:
        raise RuntimeError("AST does not contain cleanser_002 end line")

    source_lines = text.splitlines(keepends=True)
    closing_line_index = target_call.end_lineno - 1
    closing_line = source_lines[closing_line_index]
    closing_indent = closing_line[: len(closing_line) - len(closing_line.lstrip())]

    source_lines.insert(
        closing_line_index,
        f'{closing_indent}    brand="{TARGET_BRAND}",\n',
    )

    text = "".join(source_lines)
else:
    value = brand_keyword.value

    if (
        value.lineno is None
        or value.end_lineno is None
        or value.end_col_offset is None
    ):
        raise RuntimeError("AST does not contain brand source coordinates")

    offsets = line_offsets(text)

    start = offsets[value.lineno - 1] + value.col_offset
    end = offsets[value.end_lineno - 1] + value.end_col_offset

    text = text[:start] + f'"{TARGET_BRAND}"' + text[end:]

# Syntax check before writing.
ast.parse(text)
CATALOG_PATH.write_text(text, encoding="utf-8")

TEST_PATH.write_text(
    '''
from app.seed.test_catalog import TEST_PRODUCTS


def test_test_catalog_has_cross_brand_cleanser_alternative() -> None:
    cleansers = [
        product
        for product in TEST_PRODUCTS
        if product.get("routine_step") == "cleanser"
    ]

    brands = {
        str(product.get("brand") or "").strip().casefold()
        for product in cleansers
        if str(product.get("brand") or "").strip()
    }

    assert len(cleansers) >= 2
    assert len(brands) >= 2


def test_cleanser_002_is_a_different_brand_alternative() -> None:
    products = {
        product["external_id"]: product
        for product in TEST_PRODUCTS
    }

    original = products["cleanser_001"]
    alternative = products["cleanser_002"]

    assert original["routine_step"] == alternative["routine_step"]
    assert original["brand"].casefold() != alternative["brand"].casefold()
    assert alternative["price_rub"] < original["price_rub"]
'''.lstrip(),
    encoding="utf-8",
)

# Final syntax checks.
ast.parse(CATALOG_PATH.read_text(encoding="utf-8"))
ast.parse(TEST_PATH.read_text(encoding="utf-8"))

print("FIX APPLIED")
print(f"{TARGET_EXTERNAL_ID} brand = {TARGET_BRAND}")
print("Production replacement algorithm was not changed.")