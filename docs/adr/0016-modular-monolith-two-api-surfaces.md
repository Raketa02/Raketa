# ADR-0016 — One backend deployable, with a separate API surface per client

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

[ADR-0005](0005-three-app-monorepo-ownership-boundaries.md) settled three deployables: a
backend and two clients. It did not settle whether the *backend* stays one deployable.
[ADR-0006](0006-backend-owns-api-contract.md) settled that the backend owns the API
contract and both clients generate their wire types from it — but assumed a **single**
`openapi.json`.

The question is real, because the player app and the club console look like two systems.
They have different users, different vocabularies, different screens and — plausibly —
different release pressures. The obvious move is a player service and a club service, with
the engines behind a third. It was considered seriously and rejected.

**The seam does not exist in the domain.** Ask where `Match` goes. A match is created by a
player (an open match) or by the club's Intent Pool. Its seats are paid by players. It
occupies a court owned by the club. When the last seat is funded the hold becomes hard and
**a court leaves the club's sellable inventory**. Its state is rendered as player-facing
tags on one side and as the canonical lifecycle in the club's Bookings register on the
other. The Intent Pool reads player intent declarations, club court availability and match
state inside a single scan.

`Match` does not sit on the player side or the club side. It sits astride, and so do the
Intent Pool and the hold ladder. Splitting player/club would put a network boundary through
the middle of the most-written aggregate in the system. Trace one operation — a player pays
for the last seat — and it becomes a distributed transaction whose failure mode is
double-selling a court, which is the first problem the club console exists to solve.

**The product's central engineering claim argues against it.** Microservices are a
technique for letting parts of a system diverge safely. Rakieta's specifications are built
around 40 cross-application assertions proving the two sides *never* diverge, and state the
governing rule as *"there is exactly one implementation of each question."* Those are in
tension, and the specifications pick a side.

**And there is no team boundary.** Independent deployment exists to serve independent
teams. There is one developer. A network boundary where no organisational boundary exists
buys operational cost and no autonomy.

**But a single contract document has its own latent problem:** it lets either client take a
dependency on a path or schema meant for the other. Once both clients have generated
against one document, splitting it later is a migration touching real, shipped wire types —
including a mobile app whose old versions stay installed on phones for months.

The alternatives considered:

- **Three services** — player, club, engines. Rejected above.
- **Two services** — one backend plus an engine service. The engines are pure functions
  with no state and no independent lifecycle, so the hop buys nothing an import rule does
  not already give ([ADR-0015](0015-engines-as-a-pure-versioned-layer.md)).
- **One deployable with internal boundaries**, and the isolation placed at the API surface
  and the module edge rather than at the process edge.

## Decision

We will keep **one backend deployable**, and put the player/club isolation at the contract
rather than the process.

- **Two route trees.** `app/api/v1/player.py` and `app/api/v1/club.py` each build a surface
  router under the versioned `/api/v1` prefix. `app/api/v1/router.py` mounts **both**; the
  deployable is single.
- **Two committed OpenAPI documents.** `make openapi` (`python -m app.api.contract`) emits
  `backend/openapi.player.json` and `backend/openapi.club.json`, each generated from a
  throwaway app carrying only that surface's routes — so a player client never sees a club
  path and vice versa. Each client's `pnpm gen:api` reads its own document.
- **The split is set up now,** while it costs two one-line edits, rather than after real
  club wire types exist. The club surface currently carries no endpoints; the tree exists
  so club routes have a home the day they are written.
- **A module owns its tables.** No module reads another module's tables; cross-context
  reads go through a published interface.
- **Boundaries are enforced mechanically** by `import-linter` in CI, in the same posture as
  the ownership hooks — see [ADR-0015](0015-engines-as-a-pure-versioned-layer.md).
- **Contexts communicate by domain events** over the transactional outbox that already
  exists, wherever the coupling is temporal rather than transactional.

This amends ADR-0006's single-document mechanism; ADR-0006 points here.

We will extract a service when — and only when — one of these becomes true, and each
should be re-read before anyone proposes a split:

1. A second team appears with its own release cadence.
2. Load profiles diverge by an order of magnitude. Note that the Intent Pool's scan is
   heavy batch CPU work whose answer is a **background worker running this same codebase**,
   following the embedded `EventWorker` pattern — not a separate service.
3. Compliance forces data-residency separation.
4. An engine becomes ML inference needing a different runtime.

## Consequences

**Easier**

- The operations that cross the player/club line — funding a seat, taking a hold, running
  the Intent Pool — stay inside one transaction, so the invariants that protect inventory
  are enforced by the database rather than by a saga.
- Neither client can accidentally depend on the other's contract: the other's paths are not
  in its document to import.
- Adding the club surface later is additive — mount routes on the club router, regenerate,
  commit. No migration of existing player wire types.
- One migration history, one test suite, one local dev command. A request can be followed
  in a single process, which matters when the operator is learning.
- The cross-application assertions stay unit tests over shared code instead of becoming
  contract tests between services.

**Harder**

- **The whole backend deploys together.** A change to club reporting redeploys the player
  API. Acceptable at one team; the first real cost of this decision.
- **Two documents to keep current instead of one,** and `make gen-api` regenerates two
  targets. A stale document still looks authoritative — CI should eventually verify both
  are current.
- **A route's surface is now a deliberate choice**, not an afterthought: a developer must
  decide which router to mount it on, and a genuinely shared endpoint (auth, identity) has
  to be included on **each** surface that needs it.
- **Boundaries are conventions plus a linter, not physics.** A determined shortcut can
  cross a module edge in a way a network could have refused. The linter is therefore
  load-bearing and must stay green.
- One database means one scaling unit and one blast radius. A pathological query on the
  club side degrades the player side.
- The structure invites the reasonable question *"why isn't this split by app?"* from
  anyone joining later, and answering it requires this record.

**Neutral**

- Most of the extraction kit is already built — event store, transactional outbox, and an
  event catalog mapping classes to durable names and versions so history survives renames.
  This decision is the first stage of a path that stays open, not a corner painted into.
