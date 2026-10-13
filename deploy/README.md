# KOYASH production deployment

The production stack is defined in `docker-compose.prod.yml`. It exposes only
the frontend HTTP port. Backend and MongoDB remain reachable only inside the
Compose networks.

## Server requirements

- Ubuntu 24.04;
- Docker Engine with the Compose plugin;
- at least 4 GB RAM and 12 GB free disk space;
- inbound TCP access to `KOYASH_HTTP_PORT` (8080 by default).

## Configuration

1. Copy `deploy/koyash.env.example` to `deploy/koyash.env`.
2. Generate independent URL-safe MongoDB and JWT secrets.
3. Set `FRONTEND_BASE_URL` to the address users open.
4. Set the VseLLM key. Never commit `deploy/koyash.env`.

## Deploy

```bash
docker compose \
  --env-file deploy/koyash.env \
  -f docker-compose.prod.yml \
  up -d --build --remove-orphans
```

## Verify

```bash
docker compose --env-file deploy/koyash.env -f docker-compose.prod.yml ps
curl --fail http://127.0.0.1:8080/healthz
curl --fail http://127.0.0.1:8080/api/v1/health
```

The catalog count should be 68 active products. The canonical dataset still
contains 69 rows; the discontinued Siberian Health peeling remains inactive.

## Backup and rollback

Before replacing an existing deployment, create a MongoDB archive and keep the
previous release directory. A rollback changes the `current` symlink back to
the previous release and runs the same Compose command. Do not delete Docker
volumes during a normal upgrade.
