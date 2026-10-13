# ADR 0001 — Single-port nginx serving the SPA and reverse-proxying the API

- Status: Accepted
- Date: 2026-07-05
- Related quality requirements: QR-02 (availability), QR-03 (operability)

## Context

KOYASH consists of a React/Vite SPA and a FastAPI backend. Serving them on separate
origins requires CORS configuration and exposes two public ports, which complicates
deployment and customer/TA access on the university VM. We need a simple, stable,
single access point for the deployed MVP.

## Decision

nginx serves the static SPA build and reverse-proxies all `/api/` requests to the
backend service on the internal Docker network (`backend:8000`). The SPA is built with
`VITE_API_BASE_URL=/api/v1`, so the browser always calls the same origin. Only one
public port (8080) is exposed.

## Consequences

- Positive: no CORS configuration is needed; a single public entry point simplifies
  deployment and access; TLS can later be terminated in one place.
- Positive: the backend is not directly exposed to the public network.
- Negative: nginx is a single ingress that must be running for the app to be reachable.
- Negative: API access for debugging requires going through the proxy or the internal
  network.