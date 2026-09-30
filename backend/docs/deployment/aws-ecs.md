# AWS ECS / Fargate Deployment Guide

> ## ⚠️ DORMANT — not currently in use
>
> Development is **entirely local**: local Postgres + local Docker via
> [`../../docker-compose-local.yml`](../../docker-compose-local.yml). Nothing described
> below is provisioned, and the pipeline that would use it
> (`.github/workflows/deploy-ecs.yml`) is manual-only and gated on `vars.AWS_REGION`.
>
> This guide is kept intact so deployment can resume without being reconstructed from
> memory. See [ADR-0010](../../../docs/adr/0010-local-first-development-aws-deferred.md).
>
> **Before reactivating, re-read this against the current code.** Dormant infrastructure
> drifts silently — and it did: the task definition went eleven days without three of the
> variables the settings object demands, which is a task that starts and immediately dies
> ([#341](https://github.com/Raketa02/Raketa/issues/341)).
>
> **That particular drift is now a build gate.** `make taskdef` at the repository root
> boots [`../../deploy/ecs/taskdef.json`](../../deploy/ecs/taskdef.json) through
> [`../../app/core/config.py`](../../app/core/config.py) and names anything it fails to
> supply; CI runs it on every backend pull request. Run it before reactivating rather than
> comparing the two files by eye. It asserts **presence**, not the values behind the secret
> ARNs — those are still yours to check.

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
        "READER_DB_URL":"postgresql+asyncpg://<user>:<pwd>@<rds-endpoint>:5432/<db>",
        "REDIS_URL":"redis://<elasticache-endpoint>:6379/0",
        "PHOTO_STORAGE_SECRET_KEY":"<the-photo-bucket-secret-key>",
        "STRIPE_SECRET_KEY":"<sk_live_… from the Stripe dashboard>",
        "STRIPE_PUBLISHABLE_KEY":"<pk_live_… from the Stripe dashboard>",
        "STRIPE_WEBHOOK_SECRET":"<whsec_… of the platform webhook endpoint>"
     }' \
     --region $AWS_REGION
   ```

   **Every key here is referenced by the task definition, and the set is checked.** Adding
   a variable to `taskdef.json` without adding it to this payload gives a task that cannot
   pull its secrets; `make taskdef` catches the reverse — a settings object that demands a
   variable the task definition does not supply — but it reads nothing from AWS and cannot
   see this command. Keep the two in step by hand.

   `REDIS_URL` needs somewhere to point. **No ElastiCache provisioning steps are written
   here**, because none have ever been run; the ephemeral store is a real prerequisite of a
   deployed environment and not an optional extra — the application refuses to start
   without the variable, on the reasoning in
   [`../../app/infrastructure/redis_client.py`](../../app/infrastructure/redis_client.py).

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
   - Target group **deregistration delay** — set it to the application's own
     `--graceful-timeout`, in
     [`../../docker/api/startup.prod.sh`](../../docker/api/startup.prod.sh), which is the
     number that leads. Read it out of there rather than choosing one here; §4b is the
     argument, including why this comes *down* to meet the timeout and the timeout never
     goes up to meet it. It is a target-group **attribute** rather than a creation
     parameter, so a target group that is merely created keeps AWS's default of **300** —
     five minutes of drain before the container is even told to stop, on every deploy. It
     is a second call:

     ```bash
     aws elbv2 modify-target-group-attributes \
       --target-group-arn <tg-arn> \
       --attributes Key=deregistration_delay.timeout_seconds,Value=30 \
       --region $AWS_REGION
     ```
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

## 4b. Shutdown: which number leads

Three deadlines govern a rolling deploy, and **gunicorn's `--graceful-timeout` is the
one that leads.** It is in
[`../../docker/api/startup.prod.sh`](../../docker/api/startup.prod.sh) and it is **30
seconds**: how long the application gives itself, after SIGTERM, to finish what it is
serving. Everything else is measured against it, and not all in the same direction:
the deadline that falls **after** that window outlives it; the drain that falls
**before** it matches it.

| Setting | Where | Today | Why |
| --- | --- | --- | --- |
| `--graceful-timeout` | `docker/api/startup.prod.sh` | **30** | **Leads.** An SSE stream ([ADR-0147](../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)) lives until its access token expires, so a deploy severs open streams rather than waiting them out. That is the intended trade — the client reconnects, and the nudge design means a severed stream costs latency, never data. |
| `stopTimeout` | `deploy/ecs/taskdef.json` | **40** | Follows. When the ECS agent stops asking and sends SIGKILL. The ten-second margin covers what the gunicorn master does *after* its graceful window closes — force-kill stragglers, reap them, exit — so the container exits on its own rather than being killed. It is a ceiling, not a wait: a healthy stop still finishes at about 30s. |
| `deregistration_delay.timeout_seconds` | the ALB target group — not in this repository | **30**, if §1 step 6 was followed | Follows, by **matching** rather than outliving, because it is the one deadline that falls *before* SIGTERM: ECS drains the target first and tells the container to stop second, so this window and the graceful one are two budgets in sequence rather than two deadlines on one — which is why equality here is not the dead heat row 2 was. AWS defaults it to 300, and the default is why it is lowered to meet the graceful timeout rather than the timeout raised to meet it: the only connection that can hold a drain past the graceful window is one the graceful window then severs anyway, so every second of the default beyond 30 buys nothing and the deploy pays for all of them. |

**Do not raise the graceful timeout to meet a drain window.** That is the wrong direction
for the reason in the third row.

**The third row's ordering is the ECS task lifecycle's, and it is the opposite of the way
this was first filed.** A task being replaced enters `DEACTIVATING`, where **ECS** waits for
the target to finish deregistering; only then does it reach `STOPPING`, which is where
SIGTERM lands. So nothing holds a target draining *after* the process stopped serving — the
drain is what the deploy waits on *before* the process is told to stop.
[#372](https://github.com/Raketa02/Raketa/issues/372) and
[ADR-0147](../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
§8 both describe it the other way round. The number and the direction they settle stand; what
changes is the defect behind them — a deploy that takes five minutes per task, rather than a
stream held open against a process that has stopped.

**And the delay is a ceiling rather than a wait.** A deregistering target with nothing in
flight on it completes **immediately**, which is every request this API has served so far —
so the 300 costs nothing until a connection is long-lived, and ADR-0147's stream is the
first thing to make it visible. It is also why the graceful timeout is what this matches
rather than undercuts: when the delay elapses the balancer **closes** whatever connections
are still open on that target, so a drain shorter than the application's own window would
cut requests the application was willing to finish.

`stopTimeout` was unset before [#345](https://github.com/Raketa02/Raketa/issues/345),
which is not the same as unbounded: Fargate supplies **30** when the key is absent —
exactly the graceful timeout — so the agent's SIGKILL landed on the same second the
master would have force-killed its own stragglers. Fargate accepts 2–120 and rejects
anything outside it at `RegisterTaskDefinition`.

**The first two rows are a build gate, not a convention.** `make taskdef` reads the flag
out of the entrypoint and the integer out of the task definition and fails if the
deadline does not strictly outlive the drain, so changing one without the other cannot
merge.

**The third row is not a gate, and cannot be while the target group is not committed.**
Nothing in this repository describes that resource, so there is no file for a check to
read — which is why the number is written into §1 step 6, in the step that creates the
thing it belongs to, and a provisioner is what applies it. Committing the balancer and its
target group as infrastructure is
[#396](https://github.com/Raketa02/Raketa/issues/396); if that lands, §1 step 6's line
moves into it rather than becoming wrong.

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
