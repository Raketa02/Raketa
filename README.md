# Base Backend

Production-ready FastAPI backend providing user signup, login, refresh, logout,
and a `/users/me` endpoint, backed by async SQLAlchemy + PostgreSQL, deployed
to AWS ECS Fargate.

## Architecture

```
src/application/
  server.py                     # FastAPI app factory + lifespan
  core/                         # config, db engine, security, ssl, logging, exceptions
  domain/
    user/                       # entities, schemas, repository, service
    auth/                       # refresh-token entities, schemas, repository, TokenService
  api/v1/
    routers/                    # users, auth, health
    dependencies/               # get_current_user, RequireAuthority, require_admin
  tests/                        # pytest suite (in-memory SQLite)
```

Routes:

| Method | Path | Auth | Description |
|---|---|---|---|
| GET  | `/health`                | — | Liveness probe (200 only) |
| POST | `/api/v1/users`          | — | Create user (201) |
| POST | `/api/v1/users/login`    | — | Login → access/refresh JWT pair (200) |
| GET  | `/api/v1/users/me`       | Bearer access | Current user (200/401) |
| POST | `/auth/refresh`          | refresh in body | Rotate token pair (200/401) |
| POST | `/auth/logout`           | refresh in body | Revoke refresh (200, idempotent) |

## Running locally

```bash
poetry install
cp .env.example .env.local      # already exists with safe placeholders
docker compose -f docker-compose-dev.yml up --build -d
docker compose -f docker-compose-dev.yml exec api alembic upgrade head
curl http://localhost:8000/health
```

Run the test suite:

```bash
poetry run pytest src/application/tests -q
```

## Deploying to AWS ECS

See [docs/deployment/aws-ecs.md](docs/deployment/aws-ecs.md) for end-to-end
steps (ECR, secrets, task def, ALB, mTLS, migrations, CloudWatch).

Quick cycle:

```bash
make ecr-push      # build + login + push to ECR
make ecs-deploy    # force ECS to roll onto the latest image
```

CI/CD lives in [`.github/workflows/deploy-ecs.yml`](.github/workflows/deploy-ecs.yml).

## Security notes

- Passwords: bcrypt (`PasswordHasher` in `core/security.py`).
- Refresh tokens: JWT issued *plus* server-side row with bcrypt-hashed token, `jti`, `is_valid` flag. Rotation on every refresh.
- JWTs enforce `token_type` on decode — an access token cannot be used to refresh and a refresh token cannot be used as access.
- Logout is idempotent and does not leak whether the token was valid.
- The HTTP listener bound by the app is plain HTTP — TLS / mTLS terminate at the ALB in production.

## Out of scope (not implemented)

- Email verification, password reset, OAuth.
- Rate limiting (use ALB / WAF / API Gateway).
- Persistent access-token revocation list — refresh rotation + short access lifetime is the chosen trade-off.

## After cloning

If you cloned this repo *before* the secret cleanup, the previous `.env.local`
contained a real DockerHub PAT. **Revoke it**:
<https://hub.docker.com/settings/security>
