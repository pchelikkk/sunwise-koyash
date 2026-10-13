# Product price and image refresh

`backend/scripts/refresh_product_metadata.py` checks product pages for structured
price and image metadata. It is intentionally conservative:

- dry-run is the default;
- only approved merchant domains and product URL patterns are allowed;
- `robots.txt` is checked before product pages are requested;
- requests are sequential and rate-limited;
- only public HTTP(S) URLs are accepted;
- price changes above the configured threshold are reported but not applied;
- writes use a temporary workbook and an atomic replacement;
- formula-based `segment` and `price_per_ml` fields are materialized before a
  write, so headless imports receive current values without relying on Excel's
  formula cache;
- applied checks store a timestamp and status in the workbook.

## Preview

The dataset is mounted read-only in the regular backend container, which is ideal
for a preview:

```bash
docker compose exec -T backend python scripts/refresh_product_metadata.py \
  --limit 10 \
  --report /tmp/catalog-metadata-report.json
```

Use one or more `--only-id product_001` flags for a focused check.

To preview or repair only the formula-derived fields without making network
requests, add `--derived-only` (and `--apply` when the preview is approved).

## Apply

Run the existing backend image with an explicit read-write dataset mount:

```bash
docker run --rm \
  -v "$PWD/backend:/app" \
  -v "$PWD/data:/data:rw" \
  -w /app \
  sunwise-koyash-backend \
  python scripts/refresh_product_metadata.py \
  --apply \
  --report /data/catalog-metadata-report.json
```

Review the report and workbook diff, then restart the backend so the normal
dataset synchronizer imports the new values:

```bash
docker compose restart backend
```

## Scheduling

For production, schedule a dry-run first and retain its JSON report as an
artifact. Apply only after the report passes operational review. The command is
safe to repeat; unchanged values are not counted as updates.

Gold Apple currently returns a JavaScript device-check page to a normal server
request and exposes no product metadata in that response. The updater records
`metadata_not_found` and does not attempt to bypass the protection.

The approved fallback sources are deliberately product-specific rather than broad
marketplace crawls. Product URLs from Pleyana, Siberian Wellness, Pharmacosmetica,
Aravia, ART&FACT, Geltek, COSRX, and Some By Mi are accepted only on their known
catalog paths. The canonical workbook records the exact source URL, check timestamp,
and whether price metadata was structured, visibly verified, or image-only. A price
is changed only when the source describes the same product and volume; otherwise the
existing price is retained and only the verified image/link is updated.
