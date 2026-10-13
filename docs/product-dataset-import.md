# KOYASH product dataset import

This document describes Step 4.4 product dataset import.

The importer supports CSV and XLSX files. Put the real catalog into the root data folder:

data/products.xlsx

or:

data/products.csv

Inside Docker the file is available as:

/data/products.xlsx

or:

/data/products.csv

Main command:

docker compose exec backend python scripts/import_products.py --file /data/products.xlsx --replace-dataset --delete-sample-products

For the normal Docker deployment this manual command is no longer required. On backend
startup, `IMPORT_DATASET_ON_STARTUP=true` validates and synchronizes
`PRODUCT_DATASET_PATH=/data/products.xlsx`. A SHA-256 fingerprint makes the operation
idempotent; a missing row or changed file triggers repair, while an unchanged complete
catalog is left untouched.

Dry run command:

docker compose exec backend python scripts/import_products.py --file /data/products.xlsx --replace-dataset --delete-sample-products --dry-run

Cleanup sample products only:

docker compose exec backend python scripts/import_products.py --delete-sample-products

Supported column names include Russian and English variants:

external_id, id, sku, артикул, код
name, название, название продукта
brand, бренд
category, категория
routine_step, step, шаг ухода, этап ухода
price_rub, price, цена, стоимость
budget_segment, бюджет, ценовой сегмент
skin_types, тип кожи, типы кожи
concerns, запросы, проблемы, что волнует
ingredients, состав, ингредиенты, ключевые ингредиенты, inci
ingredient_flags, флаги ингредиентов
risk_flags, риски, флаги риска
values, ценности, приоритеты
texture, формат, текстура
description, описание
how_to_use, применение, как использовать
image_url, изображение, фото
product_url, ссылка
is_active, активен, использовать

The importer marks real products with:

source = dataset

Sample/demo products are detected by:

source = sample
or sample-like external_id
or sample demo brands such as Koyash Sample, Soft Lab, Clear Skin, Sun Basic

The importer does not use LLM. It only maps product catalog rows into the backend product
schema. Missing usage text receives a conservative routine-step instruction. External
image and product links are normalized to absolute HTTP(S) URLs; unsafe schemes are
discarded. The current canonical workbook imports 69 valid rows and zero invalid rows.
