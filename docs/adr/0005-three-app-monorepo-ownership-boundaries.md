# ADR-0005 — Three-app monorepo with enforced ownership boundaries

- **Status:** Accepted
- **Date:** 2026-08-09

> **Scope note.** This decision stands unchanged.
> [ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md) re-examined it when a
> shared computational core arrived — the case where a shared package is most tempting — and
> kept the rejection, supplying an API-contract mechanism in place of the duplication this
> record accepts under *Consequences → Harder*.

## Context

Raketa is three deployables: a FastAPI backend, a React Native (Expo) player app, and a
Next.js club web app. They are built **in parallel, largely by AI agents**, and that
changes which risks matter.

An agent works from a fresh context. Given access to the whole tree, the cheapest way to
make a failing thing pass is often to reach sideways: patch the client instead of fixing
the contract, "align" a type by editing the other side, or fix a test by changing the
code it was testing. Each is locally reasonable and globally corrosive. With three apps
and several concurrent sessions, "please stay in your lane" written in a markdown file is
not a boundary — it is a suggestion that survives exactly as long as the context window.

The alternatives considered:

- **Three separate repositories.** The strongest possible boundary, but the API contract
  then has to travel between repos (publishing a package, or copy-paste), cross-cutting
  changes need coordinated PRs, and there is no single place to read the domain language.
- **A monorepo with shared workspace packages** (pnpm workspaces + a shared
  `api-client`/`domain` package). Removes contract duplication between the two clients,
  but couples them: a change to shared code can break an app nobody was working on, the
  Expo/Metro setup needs monorepo-specific configuration, and — most relevant here — it
  gives an agent a legitimate-looking path to affect another app.
- **A monorepo of fully independent apps.** No shared source; the only contract is HTTP.

## Decision

We will use a **monorepo of three fully independent applications**, with the boundary
**mechanically enforced**.

- Top-level layout: `backend/`, `frontend_player/`, `frontend_club/`.
- **No shared source and no root workspace.** Each frontend owns its own
  `node_modules`, config, and generated API client. The apps communicate over HTTP only.
- **Cross-app imports are forbidden**, and ESLint's `no-restricted-imports` blocks the
  relative paths that would express one.
- **One session owns one app.** A `PreToolUse` hook (`.claude/hooks/enforce-ownership.sh`)
  resolves the session's app from `$RKTA_TIER` or its working directory and blocks any
  `Edit`/`Write`/`MultiEdit`/`NotebookEdit` targeting a different app.
  `.claude/hooks/guard-bash.sh` applies the same rule to shell redirects and file verbs,
  so a `cp` cannot do what an `Edit` was refused.
- **A scoped session cannot edit the guardrails.** Writes to `.claude/hooks/**` and
  `.claude/settings.json` are blocked unless the session is at the repository root —
  otherwise an agent can disable the boundary that constrains it and then cross it.
- **Shared files stay writable from any session**: the root glossary, `docs/adr/`, and
  `docs/agents/`. The boundary is about *code ownership*, not about preventing
  documentation.
- **The repo root is the orchestrator.** A session started at the root owns everything;
  that is the human's seat.

Duplication between the two clients is accepted, and is bounded on purpose: both
generate their wire types from the same `backend/openapi.json`
([ADR-0006](0006-backend-owns-api-contract.md)), so the thing most likely to drift is
generated rather than written.

## Consequences

**Easier**
- Parallel agent sessions cannot corrupt each other's app. The failure mode becomes a
  blocked tool call with an explanation, instead of a silent edit discovered days later.
- Each app has one lockfile, one dependency graph, one lint config. An Expo SDK upgrade
  cannot break the Next.js build.
- No monorepo tooling to maintain: no workspace protocol, no Turborepo, no Metro
  `watchFolders` configuration.
- One repository still means one glossary, one ADR sequence, one commit that can change
  the backend and note what the clients must regenerate.

**Harder**
- **Genuine duplication between the two clients.** Shared concepts (date formatting,
  a booking-status label, an error shape) get written twice and can diverge. This is the
  real cost of the decision, and it grows with the apps.
- A cross-cutting change takes more than one session: backend first, then each client.
- No compile-time coupling means a breaking contract change is caught by regeneration or
  by tests, not by the type checker at the moment of the change.
- Three `node_modules`/venv trees: more disk, slower cold CI without caching.

**Neutral**
- The two clients deliberately share a *shape* ([ADR-0009](0009-feature-first-clean-architecture-frontends.md))
  even though they share no code, so a rule learned in one transfers to the other.
- If duplication between the clients becomes the dominant pain, the reversal is a new
  ADR introducing a workspace and a shared package — it does not invalidate this one.
  Splitting into three repositories later is likewise still open; nothing here depends
  on shared tooling.
