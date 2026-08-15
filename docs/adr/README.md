# Architecture Decision Records

Each ADR captures one significant architectural decision: the context and forces, the
decision, and its consequences. They are **immutable once accepted** — to change a
decision, add a new ADR that supersedes the old one. Don't rewrite history; the reason a
past decision looked right is itself information.

## Convention

- Files: `NNNN-short-kebab-title.md`, numbered sequentially from `0001`.
- Format: [Michael Nygard's template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — see [`TEMPLATE.md`](TEMPLATE.md).
- Status: `Proposed` → `Accepted` → (`Superseded by ADR-XXXX` | `Deprecated`).
- **One sequence for the whole repo.** There are no per-app ADR directories: a decision
  that appears to affect one app usually constrains the others, and one numbered
  sequence is easier to reason about than three.

ADRs **0001–0004** were captured **retroactively** from the existing backend
implementation, so the baseline is documented. **0005–0009** are the decisions made when
the repo became a three-app monorepo.

## When to write one

Write an ADR when a choice would be expensive to reverse, when you had to argue yourself
out of the obvious alternative, or when a future reader would otherwise assume the
current shape was accidental. Don't write one for a naming preference.

If your work **contradicts** an existing ADR, surface it rather than silently overriding:

> _Contradicts ADR-0006 (backend owns the contract) — but worth reopening because…_

## Index

- [0001 — Clean / hexagonal architecture on the backend](0001-clean-hexagonal-architecture.md)
- [0002 — Event-sourced User aggregate](0002-event-sourced-user-aggregate.md)
- [0003 — Transactional outbox for event delivery](0003-transactional-outbox-for-event-delivery.md)
- [0004 — JWT access tokens with rotating refresh tokens](0004-jwt-access-with-rotating-refresh-tokens.md)
- [0005 — Three-app monorepo with enforced ownership boundaries](0005-three-app-monorepo-ownership-boundaries.md)
- [0006 — The backend owns the API contract](0006-backend-owns-api-contract.md) — *amended to two documents by 0016*
- [0007 — Club web: BFF with an httpOnly-cookie session](0007-club-web-bff-httponly-cookie-session.md)
- [0008 — Player mobile: secure-store tokens, direct to the API](0008-player-mobile-securestore-direct-api.md)
- [0009 — Feature-first Clean Architecture on both frontends](0009-feature-first-clean-architecture-frontends.md) — *narrowed to the player app by 0014*
- [0010 — Local-first development; AWS deployment deferred](0010-local-first-development-aws-deferred.md)
- [0011 — A locked design system for the club console](0011-club-console-design-system.md)
- [0012 — A locked design system for the player app](0012-player-app-design-system.md)
- [0013 — Player app: the production runtime architecture](0013-player-app-runtime-architecture.md)
- [0014 — The club console follows its production architecture standard](0014-club-console-production-architecture-standard.md)
- [0015 — Engines as a pure, versioned layer](0015-engines-as-a-pure-versioned-layer.md)
- [0016 — A modular monolith with two API surfaces](0016-modular-monolith-two-api-surfaces.md)
- [0017 — Assessment and SkillRating are event-sourced](0017-rating-context-event-sourced.md) — *its irreversibility rule superseded by 0020*
- [0018 — Aggregate repositories over the event store](0018-aggregate-repositories-over-the-event-store.md)
- [0019 — Assessment stream ids are derived from (player, sport, attempt)](0019-deterministic-assessment-stream-ids.md)
- [0020 — Revising an assessment answer truncates the transcript and replays](0020-revisable-assessment-answers.md)
