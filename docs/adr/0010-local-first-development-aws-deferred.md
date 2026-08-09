# ADR-0010 — Local-first development; AWS deployment deferred

- **Status:** Accepted
- **Date:** 2026-08-09

## Context

The backend arrived with a complete AWS path: an ECS/Fargate task definition, an
ECR/ECS GitHub Actions pipeline, `build-prod`/`ecr-*`/`ecs-*` Makefile targets, and a
written provisioning guide. None of it is in use, and none of it will be for a while:
the project is at the point of establishing structure, not shipping.

That leaves a choice about the AWS material, and both obvious answers are wrong:

- **Delete it.** The repo gets simpler and honest about what runs today, but a working
  deployment path that took real effort to get right is thrown away, and it will be
  reconstructed later from memory — badly, and probably subtly differently.
- **Leave it active.** Every push then attempts a deploy that cannot succeed, because
  the new repository has no OIDC role, no ECR repository, and no ECS service. CI goes
  permanently red on something that isn't broken, and a red CI that is *expected* to be
  red trains everyone to stop reading CI at all. That is how a genuine failure gets
  missed.

There is also an agent-safety angle: dormant-but-runnable deploy commands are exactly
the kind of thing an agent might invoke while "fixing the build".

## Decision

We will develop **entirely locally** — local Postgres and local Docker via
`backend/docker-compose-dev.yml` — and keep the AWS deployment path **intact but
dormant**.

Dormancy is deliberately **layered**, so no single change wakes it by accident:

1. **Trigger.** `deploy-ecs.yml` is `workflow_dispatch` only. It does not run on push.
   Lint and test on every push belong to `ci.yml`; the deploy workflow exists solely to
   ship an image.
2. **Configuration gate.** The `build-and-deploy` job is gated on `vars.AWS_REGION`
   being set. Even a manual run stops after the tests until AWS actually exists.
3. **Agent guardrail.** `.claude/hooks/guard-bash.sh` blocks `make build-prod`,
   `ecr-*`, `ecs-*`, `docker push` and `aws ecs|ecr` outright
   ([ADR-0005](0005-three-app-monorepo-ownership-boundaries.md)).

Nothing is deleted. The task definition, the workflow, the Makefile targets and
`backend/docs/deployment/aws-ecs.md` all stay, each carrying a header saying it is
dormant and how to reactivate it.

## Consequences

**Easier**
- CI is **green and meaningful**. A red run now means something is actually broken.
- No AWS account, credentials, or spend is required to work on the project.
- The deployment path is preserved as a known-good artifact rather than as a memory,
  and reactivating it is a configuration task, not a rebuild.
- Agents cannot deploy, by three independent mechanisms.

**Harder**
- **Dormant code rots quietly.** The task definition and workflow will drift out of
  step with the app — a new required env var added to `Settings` will not appear in
  `taskdef.json`, and nothing will complain. Reactivation must therefore begin with a
  review of the whole path against the current code, not a straight `gh variable set`.
- The repo carries infrastructure that does not describe anything real, which can
  mislead a reader into thinking deployment exists. Hence the explicit `[DORMANT]`
  markers.
- Local-only means production concerns (SSL modes, RDS certificate bundles, ALB health
  checks) are untested until reactivation, so their first real exercise will be late.

**Neutral**
- `docker-compose-prod.yml` remains as the non-ECS on-host option and is equally unused.
- This decision is expected to be superseded rather than reversed: when deployment
  resumes, a new ADR should record the target that was actually chosen — which may not
  be ECS by then.
