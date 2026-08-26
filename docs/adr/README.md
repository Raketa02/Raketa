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
  sequence is easier to reason about than two.

ADRs **0001–0004** were captured **retroactively** from the existing backend
implementation, so the baseline is documented. **0005–0009** are the decisions made when
the repo became a multi-app monorepo.

## The 2026-08-25 reset — why the sequence has gaps

The repository was deliberately reset to the three features that are finished end to end:
**sign-up, sign-in, and the onboarding questionnaire that produces a Skill rating.**
Everything built ahead of them was removed — the club console, the pairing and Match Fit
engines, and the unwritten Clubs / Courts / Matches / Money / Now contexts.

The ADRs that decided *only* removed things were removed with them, because an accepted
ADR describing code that does not exist is worse than no ADR: it reads as a constraint on
work in progress. The numbers are **not reused** — a gap is the record that something was
decided there and then taken out. Removed: **0007, 0011, 0014, 0016, 0023, 0025–0027,**
and **0030–0088**. The `docs/specs/now/` specification set went with them.

This is a reset, not a reversal. Nothing in the removed set was judged *wrong*; it was
judged premature. Anything rebuilt gets a fresh ADR at the next free number, argued from
the code that exists then.

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
- [0005 — Monorepo with enforced ownership boundaries](0005-three-app-monorepo-ownership-boundaries.md) — *written for three apps; two remain after the reset. Re-examined and upheld by 0021*
- [0006 — The backend owns the API contract](0006-backend-owns-api-contract.md) — *one document again, `openapi.player.json`, since the reset left one client*
- [0008 — Player mobile: secure-store tokens, direct to the API](0008-player-mobile-securestore-direct-api.md)
- [0009 — Feature-first Clean Architecture on the player app](0009-feature-first-clean-architecture-frontends.md)
- [0010 — Local-first development; AWS deployment deferred](0010-local-first-development-aws-deferred.md)
- [0012 — A locked design system for the player app](0012-player-app-design-system.md)
- [0013 — Player app: the production runtime architecture](0013-player-app-runtime-architecture.md)
- [0015 — Engines as a pure, versioned layer](0015-engines-as-a-pure-versioned-layer.md) — *the kernel's negative space and constant homes added by 0022*
- [0017 — Assessment and SkillRating are event-sourced](0017-rating-context-event-sourced.md) — *its irreversibility rule superseded by 0020*
- [0018 — Aggregate repositories over the event store](0018-aggregate-repositories-over-the-event-store.md)
- [0019 — Assessment stream ids are derived from (player, sport, attempt)](0019-deterministic-assessment-stream-ids.md)
- [0020 — Revising an assessment answer truncates the transcript and replays](0020-revisable-assessment-answers.md)
- [0021 — The kernel lives in the backend; clients derive only by comparison](0021-kernel-in-backend-clients-derive-by-comparison.md)
- [0022 — What the kernel is not, and where a constant lives](0022-kernel-negative-space-and-constant-homes.md)
- [0024 — An Instant is an aware datetime; engines compute in integer minute coordinates](0024-instant-as-aware-datetime-minute-coordinates.md)
- [0028 — Four environments, one typed configuration](0028-four-environment-model-and-typed-configuration.md) — *renames the dev compose file to `docker-compose-local.yml`; 0010 names the old filename and stands as written*
- [0029 — Seed data goes through aggregates, and never runs in production](0029-seed-data-through-aggregates-never-in-production.md)
- [0089 — The Player profile context is event-sourced](0089-player-profile-context-event-sourced.md) — *the first racket-sport aggregate keyed on the player rather than on (player, sport)*
- [0090 — Onboarding is two parts, and the second one is per player](0090-onboarding-per-player-checkpoint.md) — *narrows `CONTEXT.md`'s "there is no onboarded player" invariant; 0017 and 0020 are untouched*
- [0091 — Photo bytes live behind a port; MinIO locally, S3 deployed](0091-photo-storage-behind-a-port.md) — *does not wake the dormant deployment path of 0010; the scheduler its Consequences say the platform lacks is supplied by 0092*
- [0092 — Periodic jobs are embedded loops, and a job must be safe to run twice at once](0092-periodic-jobs-as-embedded-loops.md) — *supplies the scheduler 0091 recorded the platform as lacking; the outbox worker of 0003 is rewritten on it*
- [0093 — The matcher is a backend module with a pure Match Fit engine](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) — *distinguishes 0015 rather than amending it: the microservice rejection stands, the matcher's state was never engine material. 0005 untouched — no fourth app*
- [0094 — Play intent is declared per sport, in its own aggregate, and edited where the player searches](0094-play-intent-declared-per-sport-in-its-own-aggregate.md) — *keeps 0089's aggregate free of a sport dimension and answers the founding rule of 0017 rather than contradicting it: a level is proved, a preference may be declared*
- [0095 — A block is a directed record with a symmetric effect, and a safety gate that cannot be evaluated excludes](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) — *corrects §7.5 of the matchmaking input document for blocks only: the live re-verify stands, the advisory index copy is dropped. Extends 0093 with the first context the matcher gates on*
- [0096 — A gender preference is a mutual gate the scorer cannot see](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) — *overrules §23 Q8 of the matchmaking input document: a filter on people, made mutual like 0095's block. Amends §7.2 by moving its guarantee to 0093's engine boundary; leaves `kernel/sports.py`'s refusal of a `Format` dimension undisturbed*
- [0097 — The event store's total order is a `sequence_no` column, not a timestamp](0097-event-store-append-order-is-a-sequence-column.md) — *supplies the determinism 0093's rebuildable candidate index assumed; leaves `occurred_at` as the domain moment 0089 defined, which is precisely why it could not serve*
- [0098 — What the matcher demands of the contexts that do not exist is an executable contract](0098-matcher-demands-as-executable-contracts.md) — *extends 0093 with the three consumer-driven ports; carries 0095's `SearchContext` pattern from blocks to pairwise history, and its `NoHoldsExist` naming to the null providers. Corrects the prototype on *settles up*; §7.2's bare `strand_* uint8|null` is amended to value-plus-evidence*
- [0099 — Relaxation offers the searcher's own asks, and never bends the engine's judgement](0099-relaxation-offers-the-searchers-own-asks.md) — *strikes three of §9.8's four rungs as score-inflation wearing a catchment-widening name; adds the quality floor to what is never relaxed, and resolves §9.2's guaranteed inclusions against §9.7. Carries 0022's no-presentation rule to the pool description and 0098's honestly-empty/honestly-neutral test to the ladder*
- [0100 — The challenge window is derived from the grid the search ran on, and is never chosen](0100-challenge-window-derived-never-chosen.md) — *keeps a prototype behaviour §16 never had, after 0093 discarded §16 and made its silence worthless. Argues past `availability.py`'s calendar refusal on coarseness rather than exemption, and past 0099's no-proposed-time rule because a label is not a slot; 0021 forbids the client deriving it*
- [0101 — The matcher's partition is derived, and is never a matching criterion](0101-partition-derived-never-a-matching-criterion.md) — *extends 0093 and amends two of its four triggers with measured numbers: §7.2's 32 MB is wrong by an order of magnitude. Strikes §9.2's shard conjunct — an equality that excludes is a criterion, whatever it is called — and puts the partition beyond reach of one by deriving it. Carries 0100's derived-not-declared shape from a time label to a place*
- [0102 — Silence is never scored: the availability grid is required, and a blank one is absent rather than zero](0102-silence-is-never-scored.md) — *the same blank field meant three different things worth ±15 of 100 — a measured zero in shipped code, `NoEvidence` in 0099, and "any time" in plain English. Applies 0098's measured-versus-invented test to the one onboarding field a player could skip, and keeps the glossary's own no-negative-filter invariant by removing the unanswered case rather than by weighing it*
- [0103 — Where the curve saturates, the gate begins: a level gate at each mode's own tolerance](0103-where-the-curve-saturates-the-gate-begins.md) — *the six judged pairings 0102's ticket left behind could not be satisfied in for-fun at any weight vector that keeps social vibe the largest term — the useful failure they were designed to produce. Past `LEVEL_TOL` both level-sensitive terms are pinned, so the engine ranks a two-level mismatch on sociability and geography alone; a floor cannot discriminate what the score cannot see. Adds no constant, and gives 0098's invariant its mirror*
- [0104 — The search record is the answer, and it never expires](0104-the-search-record-is-the-answer-and-never-expires.md) — *the design wrote one set of numbers into two stores for two good reasons and never noticed: §8.3's Redis cache and §19.2's telemetry table hold the same Fit, free to disagree, in the one place §8.3 calls disagreement fatal. 0093 dissolved the reason they were separate. The cache is deleted, the row is durable and unexpiring, a search that cannot be recorded is not returned, and — since nothing else ever deletes — erasure is written down as a demand in 0098's shape against a backend that cannot yet erase anything*
- [0105 — Determinism is a set-iteration problem in Python, and pinning the hash seed hides it](0105-determinism-is-a-set-iteration-problem-in-python.md) — *§13's Go rule guards the one Python collection that is already ordered, and by naming maps hides sets: `str` hashing is seeded per interpreter, so an id set reorders between processes and never within one — every test green, two workers disagreeing. Binds every engine, not the matcher alone; enforced by two subprocesses with different seeds, and `PYTHONHASHSEED` is never pinned, because 0028 refuses an environment variable that selects behaviour*
- [0106 — Evidence crosses as a closed vocabulary: a weight is configuration, an evidence shape is contract](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) — *0022 settled that the engine emits codes and 0006 settled that the client generates its types from them; between the two sat an unnoticed hole, because `search-telemetry.md` makes the stored terms blob deliberately opaque and an opaque blob generates as `Record<string, unknown>` — 0006's exact failure arriving through a gap in the schema rather than a broken rule, and failing silently on the one screen that promises to show its working. The wire union is closed and the store stays open, deliberately, since they answer different questions. Draws the line 0093 left unfinished: a ruleset may move every number for free, and changing an evidence *shape* is an API release. Carries 0098's measured-versus-invented test to serialisation as two spellings of absence*
- [0107 — The player card is assembled outside the engine, and its contents are a closed list](0107-the-player-card-is-assembled-outside-the-engine.md) — *the contract could name a player and say nothing about who they are: every field of a returned candidate is about a pairing, because 0096 made the scorer's blindness a type boundary. Audited against the prototype's card, five of its twelve fields have no source and two of those are refusals — a bio would be the platform's first player-authored free text, and `active 2 hours ago` is a Liveness input, which 0106 §5 forbids crossing under any name. Rides the seam 0098 opened for `at stake`, stores a photo id because 0091's presigned URLs cannot live in 0104's unexpiring record, and records that 0091 deferred its photo check on the argument that no player card existed*
- [0108 — A forecast is a route, not a search](0108-a-forecast-is-a-route-not-a-search.md) — *§9.9 promised neither forecast is reimplemented on the client and nothing stood behind it: the builder composes line-ups the engine never scored, and the prototype computes them in the browser — 0015 and 0021's failure in TypeScript, on the screen the feature is named after. Re-`POST`ing the line-up would be correct and would enter six swaps into 0104's record as six searches, so the fifth route records nothing — defensible because a forecast is checkable by recomputation under 0105 while a search is checkable only by its row. Bound to the citing search, re-verifying 0095's gates, and it makes §9.9's provisional-equals-arranged claim a property test*
- [0109 — A read-back names what it withholds, and a silent yes stays silent](0109-a-read-back-names-what-it-withholds.md) — *two accepted records disagreeing where neither was looking: 0104's immutable row read back an hour later renders a card for somebody who has since blocked the searcher, which 0095 forbids on every surface — so the read-back re-verifies and **states** the withholding, narrowing `the-two-contracts.md`'s round-trip assertion rather than loosening it. And the interest read route returns outgoing and mutuals only: incoming-and-not-mutual is what §9.5.1's silent yes was promised, and an inbox would re-read banked yeses as consent to a screen nobody agreed to*
