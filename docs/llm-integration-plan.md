# LLM explanation integration

KOYASH keeps product choice deterministic and uses an optional OpenAI or
VseLLM-compatible provider only to rewrite the short `why_here` text after a routine item has passed hard
filters, scoring, sorting, and routine construction.

## Runtime flow

1. The recommendation engine creates the complete routine with `rule-based-v2`.
2. Duplicate morning/evening products are collapsed by external ID for the provider
   call, then mapped back to both dayparts.
3. The model receives the resolved skin type, the complete user concern list, the exact
   product-level `matched_concerns`, routine step, product name/brand, and a bounded
   ingredient list. The customer-authored prompt treats `matched_concerns` as the only
   permitted basis for a concern-specific statement.
4. A valid response can replace only `why_here`. The API marks the item with
   `explanation_source=llm` and the configured model ID.
5. Missing credentials, timeouts, provider errors, empty text, overlong text, medical
   or guarantee-like claims, unsupported personalization, invalid punctuation, and
   explanations that omit the matched concern or supplied ingredient retain the
   deterministic explanation and source.

The direct OpenAI route uses the Responses API with separate `instructions` and
`input`. The VseLLM route keeps its OpenAI-compatible Chat Completions call.

The same policy is used after a user selects a replacement. The candidate is scored and
explained deterministically first; the optional rewrite happens before the new routine
is persisted.

## Configuration

Set these values only in the runtime environment; never commit the key:

```dotenv
LLM_ENABLED=true
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=...
LLM_TIMEOUT_SECONDS=12
```

For the optional VseLLM-compatible route:

```dotenv
LLM_ENABLED=true
LLM_PROVIDER=vsellm
VSELLM_BASE_URL=https://api.vsellm.ru/v1
VSELLM_MODEL=openai/gpt-4o-mini
VSELLM_API_KEY=...
LLM_TIMEOUT_SECONDS=12
```

With `LLM_ENABLED=false` or an empty key, the API remains fully functional and returns
`explanation_source=deterministic`.

## Invariants

- The provider cannot add, remove, reorder, or replace products.
- Score totals and breakdowns are not parsed from model output.
- Hard restrictions and ingredient conflicts run before any provider call.
- Usage instructions come from the catalog, not the model.
- Provider failures do not fail recommendation or replacement requests.
- Success/fallback events contain provider, model, routine step, and request counts but
  no API key or direct personal identifier.
