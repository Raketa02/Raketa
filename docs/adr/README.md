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
- [0005 — Three-app monorepo with enforced ownership boundaries](0005-three-app-monorepo-ownership-boundaries.md) — *re-examined and upheld by 0021*
- [0006 — The backend owns the API contract](0006-backend-owns-api-contract.md) — *amended to two documents by 0016*
- [0007 — Club web: BFF with an httpOnly-cookie session](0007-club-web-bff-httponly-cookie-session.md)
- [0008 — Player mobile: secure-store tokens, direct to the API](0008-player-mobile-securestore-direct-api.md)
- [0009 — Feature-first Clean Architecture on both frontends](0009-feature-first-clean-architecture-frontends.md) — *narrowed to the player app by 0014*
- [0010 — Local-first development; AWS deployment deferred](0010-local-first-development-aws-deferred.md)
- [0011 — A locked design system for the club console](0011-club-console-design-system.md)
- [0012 — A locked design system for the player app](0012-player-app-design-system.md)
- [0013 — Player app: the production runtime architecture](0013-player-app-runtime-architecture.md)
- [0014 — The club console follows its production architecture standard](0014-club-console-production-architecture-standard.md)
- [0015 — Engines as a pure, versioned layer](0015-engines-as-a-pure-versioned-layer.md) — *the kernel's negative space and constant homes added by 0022*
- [0016 — A modular monolith with two API surfaces](0016-modular-monolith-two-api-surfaces.md)
- [0017 — Assessment and SkillRating are event-sourced](0017-rating-context-event-sourced.md) — *its irreversibility rule superseded by 0020*
- [0018 — Aggregate repositories over the event store](0018-aggregate-repositories-over-the-event-store.md)
- [0019 — Assessment stream ids are derived from (player, sport, attempt)](0019-deterministic-assessment-stream-ids.md)
- [0020 — Revising an assessment answer truncates the transcript and replays](0020-revisable-assessment-answers.md)
- [0021 — The kernel lives in the backend; clients derive only by comparison](0021-kernel-in-backend-clients-derive-by-comparison.md)
- [0022 — What the kernel is not, and where a constant lives](0022-kernel-negative-space-and-constant-homes.md)
- [0023 — Money is integer grosze, gross, and a court price is a whole number of złoty](0023-money-integer-grosze-gross-whole-zloty.md)
- [0024 — An Instant is an aware datetime; engines compute in integer minute coordinates](0024-instant-as-aware-datetime-minute-coordinates.md)
- [0025 — A counted match's pairing is elected before commitment and fixed after](0025-binding-pairing-for-counted-matches.md)
- [0026 — Two matchmaking engines, one snapshot input contract](0026-matchmaking-engines-snapshot-input-contract.md)
- [0027 — Fit and certainty are separate numbers, and ranking a list is policy](0027-fit-and-certainty-are-separate-ranking-is-policy.md)
- [0028 — Four environments, one typed configuration](0028-four-environment-model-and-typed-configuration.md) — *renames the dev compose file to `docker-compose-local.yml`; 0010 names the old filename and stands as written*
- [0029 — Seed data goes through aggregates, and never runs in production](0029-seed-data-through-aggregates-never-in-production.md)
- [0030 — A departure is an audience, not a state](0030-a-departure-is-an-audience-not-a-state.md) — *its filler rule amended by 0033*
- [0031 — The hold ladder is a floor at a given level of certainty](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)
- [0032 — Order is a property of the composed screen, not of the match](0032-order-is-a-property-of-the-composed-screen.md)
- [0033 — A departure's settlement and its vacancy are independent](0033-settlement-and-occupancy-are-independent.md) — *amends 0030*
- [0034 — The Matches context is a record and keeps no history](0034-matches-is-a-record-and-keeps-no-history.md) — *the first racket-sport context to answer 0002's per-context question the other way*
- [0035 — A reservation is the only claim on a court, and it claims an interval](0035-a-reservation-claims-a-court-over-an-interval.md)
- [0036 — A UI document is final on the screen, not on the arithmetic](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)
- [0037 — The fit badge shouts once, and only about a seat](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)
- [0038 — Now is polled; the push is specified and deferred](0038-now-is-polled-the-push-is-specified-and-deferred.md) — *answers 0008's premise: no long-lived connection exists to outlive a token*
- [0039 — The card projection rebuilds from the record, so its consumer needs no partition](0039-the-card-projection-rebuilds-from-the-record.md)
- [0040 — One ladder resolves a situation; every other vocabulary projects off it](0040-one-ladder-resolves-a-situation.md) — *narrows 0021's cross-application contract suite: clients hold no ladder, so the generated enum is the fence*
- [0041 — Tone is editorial, so the wire carries a situation and its facts](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)
- [0042 — A paid share returns to the seat's last funder](0042-a-share-returns-to-the-seats-last-funder.md)
- [0043 — Opening a court to strangers is the private path's commitment](0043-opening-a-court-is-the-private-paths-commitment.md) — *narrows 0030: the private path has no commitment deadline, but it does have a commitment act*
- [0044 — A marketplace seat is a promise of a game, not a share of a court](0044-a-marketplace-seat-is-a-promise-of-a-game.md) — *bounds the "a guarantee only ever decreases" invariant to the match's lifetime*
