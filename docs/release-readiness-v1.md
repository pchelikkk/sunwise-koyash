# KOYASH release readiness

Date: 2026-07-17

Scope: professional questionnaire, backend completion, approved-design implementation,
catalog operations, and responsive product experience.

## Automated gate

| Gate | Result |
|---|---:|
| Ruff (`app` and `tests`) | Passed |
| Backend pytest suite | 190 passed |
| Canonical dataset import | 69 valid, 0 invalid |
| Startup dataset synchronization | 69 products, idempotency and repair verified |
| Routine-quality scenarios | 8 scenarios, 0 contract errors |
| Frontend Vitest | 3 passed |
| Frontend Playwright | 26 passed (Desktop Chrome and Pixel 7) |
| Vite production build | Passed |
| npm dependency audit | 0 vulnerabilities |

The routine audit has one documented coverage observation: `mask` is an optional
catalog category and is not required by the current morning/evening routine contract.
It is therefore reported, not silently hidden, and does not produce a contract error.

## Catalog evidence

- `data/products.xlsx` imports 69/69 rows under the strict dataset contract.
- Every active product has a non-empty usage instruction and product link.
- The active catalog contains 68 products: 67 have verified remote imagery (98.5%).
  The remaining andplus card deliberately uses the product-family fallback because
  the only indexed exact image now returns HTTP 404; a similar product image is not
  substituted.
- EMANSI, Tony Morris, and Maskoholic were rechecked against their official product
  pages and updated with current Russian prices, usage guidance, links, and exact
  product imagery.
- External product and image URLs are restricted to safe HTTP(S) values.
- Minimum and balanced price choices are hard per-product caps.
- The backend synchronizes the canonical catalog at startup only when its SHA-256
  fingerprint or expected product count changes.
- Administrators can see completeness and repair safe presentation fields; changes are
  recorded in `admin_audit_events`.

## UX and visual evidence

The implemented screens preserve the approved Figma direction: warm white and blush
surfaces, KOYASH pink, rounded two-column answer cards, handwritten brand details,
sun/cottage illustration language, and large friendly headings. The implementation
extends the prototype where the working product needs more states and data:

- adaptive 10–15 question flow with four skin-type clarification questions;
- review and loading states;
- explainable routine, product detail, feedback, and replacement flows;
- catalog search, filters, favorites, a server-synced cosmetic bag, and responsive
  product illustrations;
- guest-to-account migration for both saved collections and a share/copy action for
  the completed routine;
- login, registration, reset, account, and history states;
- protected analytics, catalog quality, and audited catalog editor.

The final landing refinement removes curtain/window reveal metaphors and hover-hidden
copy. Product fallbacks use a coherent Figma-exported illustration family instead of
generic CSS packaging, with distinct cleanser, toner, serum, jar, and SPF silhouettes.
Automated browser assertions prevent the removed reveal pattern and legacy artwork from
returning.

Browser QA covered 1440px desktop and a Pixel 7 viewport. The tested landing has no
horizontal overflow or console errors. Keyboard Escape closes the product dialog,
form fields have labels, account collections survive reload, and reduced motion
remains supported.

The live replacement smoke test also verified that choosing a cheaper cleanser updates
both morning and evening occurrences, recalculates the unique routine total, leaves the
cosmetic bag untouched, and displays the updated selection immediately. The Some By Mi
detail dialog was checked with its real product image and no text overlap.

## Operational smoke

The release candidate was rebuilt and started from the repository with:

```text
docker compose up -d --build
```

The smoke passed: MongoDB and the API reported healthy, nginx returned the SPA on port
8080 and forwarded `/api/v1`, the questionnaire exposed `professional-v3` with 15 raw
questions, and the catalog returned 69 synchronized products. The backend image was
also checked to confirm that local `.env` secrets are not embedded. The merge request
still requires independent reviewer approval before merge.
