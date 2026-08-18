# AWS ECS / Fargate Deployment Guide

> ## ⚠️ DORMANT — not currently in use
>
> Development is **entirely local**: local Postgres + local Docker via
> [`../../docker-compose-dev.yml`](../../docker-compose-dev.yml). Nothing described
> below is provisioned, and the pipeline that would use it
> (`.github/workflows/deploy-ecs.yml`) is manual-only and gated on `vars.AWS_REGION`.
>
> This guide is kept intact so deployment can resume without being reconstructed from
> memory. See [ADR-0010](../../../docs/adr/0010-local-first-development-aws-deferred.md).
>
> **Before reactivating, re-read this against the current code.** Dormant infrastructure
> drifts silently — in particular, check that every setting in
> [`../../app/core/config.py`](../../app/core/config.py) that has no default is present
> in [`../../deploy/ecs/taskdef.json`](../../deploy/ecs/taskdef.json). A missing env var
> shows up as a task that starts and immediately dies.

This service is built to run on **ECS Fargate**, pulling images from **ECR**,
secrets from **Secrets Manager**, logs to **CloudWatch**, and serving traffic
through an **Application Load Balancer** that terminates HTTPS (and optionally
mTLS via Trust Stores).

The high-level flow:

```
GitHub Actions ──build──▶ ECR (image)
                │
                └──render taskdef──▶ ECS task def revision
                                       │
                                       └──update service──▶ ECS Fargate ◀── ALB ◀── Internet
                                                              │
                                                              └──▶ RDS Postgres (TLS, root CA)
                                                              └──▶ event delivery worker
```

## 1. One-time AWS prep

1. **ECR repository**
   ```bash
   aws ecr create-repository \
     --repository-name raketa-api \
     --image-scanning-configuration scanOnPush=true \
     --region $AWS_REGION
   ```

2. **CloudWatch log group**
   ```bash
   aws logs create-log-group --log-group-name /ecs/raketa --region $AWS_REGION
   aws logs put-retention-policy --log-group-name /ecs/raketa --retention-in-days 30 --region $AWS_REGION
   ```

3. **IAM roles**
   - `ecsTaskExecutionRole` — attach `AmazonECSTaskExecutionRolePolicy` *and* `SecretsManagerReadWrite` (or a tighter scoped policy that allows `secretsmanager:GetSecretValue` on the prod secret ARN).
   - `raketa-task-role` — attaches whatever the application itself needs at runtime (S3 access, SES, etc.). For now it can be empty.

4. **Secrets Manager secret** (JSON-shaped so the task definition can reference individual keys via the `:KEY::` suffix):
   ```bash
   aws secretsmanager create-secret \
     --name raketa/prod \
     --secret-string '{
        "JWT_SECRET_KEY":"<generate-with-openssl-rand>",
        "WRITER_DB_URL":"postgresql+asyncpg://<user>:<pwd>@<rds-endpoint>:5432/<db>",
        "READER_DB_URL":"postgresql+asyncpg://<user>:<pwd>@<rds-endpoint>:5432/<db>"
     }' \
     --region $AWS_REGION
   ```

5. **RDS PostgreSQL** with TLS enforced:
   - Parameter group: `rds.force_ssl = 1`.
   - Bundle the AWS RDS global root CA at `https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem`.
   - Mount it inside the container at `DB_SSL_ROOT_CERT_PATH` (default `/etc/ssl/rds/rds-global-bundle.pem`). Two valid options:
     - **Bake into the image** during a CI step (`RUN curl -fsSL ... -o /etc/ssl/rds/rds-global-bundle.pem`). Lowest moving parts.
     - **Sidecar / EFS mount** if you want to rotate the bundle without rebuilds.
   - With `DB_SSL_MODE=verify-full`, asyncpg will validate the RDS hostname against the bundle. **Use the RDS-issued DNS name in the URL** (not the underlying CNAME).

6. **ECS cluster + ALB + Target Group**
   - ALB listener on `:443` with an ACM certificate.
   - Target group health check path: `/health`, port `traffic-port` (8000), interval 30s, threshold 2.
   - For **mTLS**: configure the listener to require client certs and attach a trust store (S3-hosted CA bundle of your clients). FastAPI does not terminate mTLS — the ALB does.

7. **Register the initial task definition**
   ```bash
   # Render the placeholders manually for the very first registration
   sed "s/__AWS_ACCOUNT_ID__/$ACCOUNT_ID/g; s|__AWS_REGION__|$AWS_REGION|g; s|__IMAGE__|$ECR_URI:latest|g" \
     deploy/ecs/taskdef.json > /tmp/taskdef.rendered.json
   aws ecs register-task-definition --cli-input-json file:///tmp/taskdef.rendered.json --region $AWS_REGION
   ```

8. **Create the ECS service** (one-time)
   ```bash
   aws ecs create-service \
     --cluster raketa-cluster \
     --service-name raketa-service \
     --task-definition raketa-task \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-…],securityGroups=[sg-…],assignPublicIp=DISABLED}" \
     --load-balancers "targetGroupArn=arn:...,containerName=api,containerPort=8000" \
     --health-check-grace-period-seconds 60 \
     --region $AWS_REGION
   ```

9. **Enable domain-event delivery in the API service**
   - Set `EVENT_DELIVERY_WORKER_ENABLED=true` on the API task definition.
   - Each API process hosts a background event delivery worker. The default
     production command starts one Gunicorn process for one worker.
   - Multiple API tasks can deliver events concurrently. Delivery remains
     at-least-once, so event handlers must be idempotent.

## 2. GitHub Actions secrets / variables

The `.github/workflows/deploy-ecs.yml` workflow expects:

| Type | Name | Example |
|---|---|---|
| Secret | `AWS_OIDC_ROLE_ARN` | `arn:aws:iam::123456789012:role/github-actions-raketa` |
| Variable | `AWS_REGION` | `eu-north-1` |
| Variable | `ECR_REPOSITORY` | `raketa-api` |
| Variable | `ECS_CLUSTER` | `raketa-cluster` |
| Variable | `ECS_SERVICE` | `raketa-service` |
| Variable | `ECS_CONTAINER_NAME` | `api` |

OIDC trust policy on the IAM role should restrict by repo + branch — e.g.
`token.actions.githubusercontent.com:sub = repo:OWNER/REPO:ref:refs/heads/main`.

## 3. Migrations

We do **not** run Alembic from inside the long-running API container by default
(it's a race condition risk when the service rolls). Two recommended patterns:

- **One-shot ECS RunTask** before the service update:
  ```bash
  aws ecs run-task \
    --cluster raketa-cluster \
    --task-definition raketa-migrate \
    --launch-type FARGATE \
    --overrides '{"containerOverrides":[{"name":"api","command":["alembic","-c","/home/app/alembic.ini","upgrade","head"]}]}' \
    --network-configuration "..."
  ```
  Add a second job in the workflow that runs RunTask before `amazon-ecs-deploy-task-definition`.
- **Toggle on startup migrations**: set `RUN_MIGRATIONS_ON_STARTUP=true` in the task def's environment. Simpler but couples deploy + migration.

Migration `0003` intentionally deletes unpublished legacy event rows because
previous rows use Python class names rather than durable event contract
identifiers. Schedule this cutover only when discarding those pending deliveries
is acceptable. Migration
`0005_rename_event_table_to_delivery_queue` then renames the durable event table
to `event_delivery_queue`.

## 4. Local build → push → deploy

```bash
# Login to ECR
make ecr-login AWS_REGION=eu-north-1

# Build (tags with git short SHA)
make build-prod

# Push
make ecr-push

# Force a service rollout onto the latest task def
make ecs-deploy
```

## 5. Smoke testing the deploy

```bash
# Direct ALB DNS:
curl -fsS https://<alb-dns>/health
# → {"status":"ok"}

# OpenAPI is exposed only when DEBUG=true (off in prod). Test the auth flow:
TOKEN=$(curl -fsS -X POST https://<alb-dns>/api/v1/users/login \
  -H 'content-type: application/json' \
  -d '{"email":"...","password":"..."}' | jq -r .access_token)

curl -fsS https://<alb-dns>/api/v1/users/me -H "Authorization: Bearer $TOKEN"
```

## 6. Common ECS deployment failures (and what they look like)

| Symptom | Likely cause | Fix |
|---|---|---|
| Target group reports unhealthy, container keeps restarting | Healthcheck path returns 404 | `/health` is correct in this app; verify TG path + port (8000) match the task def `portMappings` |
| Service stuck in `PROVISIONING` then `STOPPED` | Task can't pull image | Confirm `executionRoleArn` allows ECR pull; image tag exists in ECR |
| Service starts but `/health` times out from the ALB | App bound to `127.0.0.1` | `APP_HOST=0.0.0.0` in env (default in this repo); confirm SG allows ALB → task on 8000 |
| Container logs show `connection refused` to DB | Missing DB env vars / wrong RDS endpoint | Check `secrets:` ARN is correct; subnet SG allows egress to RDS SG on 5432 |
| `asyncpg.exceptions.InvalidAuthorizationSpecificationError: SSL connection is required` | RDS forces SSL but `DB_SSL_MODE=disable` | Set `DB_SSL_MODE=verify-full` and mount the RDS root CA at `DB_SSL_ROOT_CERT_PATH` |
| `ssl.SSLCertVerificationError: certificate verify failed` | Wrong / outdated RDS root CA bundle | Refresh from `truststore.pki.rds.amazonaws.com/global/global-bundle.pem` |
| Tasks register and immediately drain on every deploy | Health check `start-period` too short | Bump `startPeriod` (current default: 20s) |
| Migration RunTask hangs forever | Same DB, an in-flight rolling deploy holding sessions | Run migrations *before* you update the service, not in parallel |
| Logs missing from CloudWatch | `awslogs-create-group=true` flag not set + group doesn't exist | Pre-create the log group (step 1.2) or set `awslogs-create-group: "true"` (it is, in our task def) |

## 7. Mutual TLS at the ALB (optional)

ALB Mutual TLS (released GA late 2023) supports two modes:
- **Passthrough** — ALB delivers the client cert in `X-Amzn-Mtls-Clientcert-Leaf` headers; the app can use it for app-level authz.
- **Verify with Trust Store** — ALB enforces that the client cert chains to a CA bundle uploaded to an ALB Trust Store (S3-hosted).

For verify mode:
```bash
aws elbv2 create-trust-store \
  --name raketa-clients \
  --ca-certificates-bundle-s3-bucket my-bucket \
  --ca-certificates-bundle-s3-key clients-ca.pem
# Attach it to the listener
aws elbv2 modify-listener --listener-arn <arn> \
  --mutual-authentication "Mode=verify,TrustStoreArn=<trust-store-arn>,IgnoreClientCertificateExpiry=false"
```

FastAPI itself does *not* need to validate the cert — the ALB has already done
it. The app's `EXTERNAL_SSL_ROOT_CA_PATH` / `CLIENT_CERT_PATH` / `CLIENT_KEY_PATH`
are for **outbound** client-authenticated TLS, not inbound.
