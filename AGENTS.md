# AGENTS.md

This document describes how AI / LLM capabilities are used in KOYASH, both at runtime
and during development.

## Runtime: LLM explanation layer

KOYASH uses an optional LLM layer to generate human-readable explanations for the
skincare recommendations. It is configured through backend environment variables
(see `backend/.env.example`):

- `LLM_ENABLED` — feature flag (disabled by default; deterministic scoring works without it).
- `LLM_PROVIDER` — provider selector (`openai` by default; `vsellm` is supported).
- `OPENAI_API_KEY` — direct OpenAI API key (never committed; set via `.env`).
- `OPENAI_MODEL` — OpenAI model used for the short explanation rewrite.
- `OPENAI_BASE_URL` — OpenAI API base URL.
- `VSELLM_BASE_URL` — provider base URL (default `https://api.vsellm.ru/v1`).
- `VSELLM_MODEL` — model id (default `openai/gpt-4o-mini`).
- `VSELLM_API_KEY` — optional VseLLM API key (never committed; set via `.env`).
- `LLM_TIMEOUT_SECONDS` — request timeout (default `12`).

The recommendation algorithm itself is deterministic and documented in
`docs/recommendation-algorithm.md`; the LLM only produces explanation text on top of
the scored result. Integration design notes are in `docs/llm-integration-plan.md`.

## Guardrails

- The LLM layer is off by default; the product remains fully functional with it disabled.
- All secrets (API keys) are provided through environment variables and are never committed.
- LLM output is limited to explanation text and does not change hard exclusion rules or
  scoring.
- Requests are time-bounded via `LLM_TIMEOUT_SECONDS`.

## Runtime status and prompt contract

The explanation layer is integrated into recommendation creation and replacement
selection. Each recommended item reports `explanation_source` and
`explanation_model`. Provider failures and rejected output use the deterministic text;
selection, scoring, safety notes, and usage instructions are never delegated to the
model. The Week 7 customer prompt constrains the model to a translator-style role:
it must work only from `matched_concerns`, branch explicitly when that list is empty,
avoid unsupported ingredient claims and medical promises, and stay within 200
characters. See `docs/llm-integration-plan.md` and `reports/week7/llm-report.md` for
the runtime and evaluation contract.

## Development-time AI usage

The team uses AI assistants to draft documentation, tests, and boilerplate. All
AI-assisted output is reviewed by a human through the standard merge request process
(reviewer is never the author) before it reaches `main`, following
`docs/definition-of-done.md`.
