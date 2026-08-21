# ADR-0053 — The phone holds no rules; its only power is subtracting

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md) put the derivation kernel in
the backend and permitted clients *"nothing but a comparison against a supplied instant."*
`3-enrolled_match_engine_architecture.md` §4.1 assumes the opposite premise — *"the kernel
package ships to the server and both applications"* — and builds §4.2's three-layer render on
it: a card that re-derives locally when a push is late, renders provisionally, and is replaced
when the server disagrees. Doc 5 **A6** rules §4.1's premise rejected but keeps its intent,
proposing that `nextTransition: {at, becomes}` widen to `transitions: [{at, key, tone, facts}]`
so a client could cross several thresholds offline while still holding no rule.

That seam was affordable while a socket was going to carry the truth. It stopped being
affordable when [ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md) deferred the
push, because the client's own sense of time became the only thing keeping the screen right
between reads. §4.2's layer 2 stopped being a nicety for basements and became the mechanism.

Four shapes were on the table for what ships to the device:

- **A hand-written or generated TypeScript port of the kernel.** Two implementations of one
  truth — the failure ADR-0021 exists to prevent, and which the source documents record having
  already happened once: *"the cross-application suite caught the two apps disagreeing about
  whether the same court was held."*
- **A list of predicted transitions** (A6's fix), letting the device chain several boundaries
  with no network.
- **A single predicted transition** — the head of that list, which is what ADR-0038 already
  ships as `nextTransition`.
- **Nothing predictive at all.** The device draws the response and changes when it is asked to.

The product owner's ruling settles it on a ground none of the documents argued from: **there is
no clock running on the device at all** ([ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md)),
so there is nothing for a predicted future to feed. A transition list is only worth its payload
if something acts on it unprompted, and nothing does.

The residual case is real and separate. A card names a moment — *confirm by 14:15*, *your offer
holds until 14:20* — and the screen designs draw that moment as a live countdown. A frozen
number is worse than no number, because it reads as broken rather than static.

## Decision

**We will ship no rules to any client. A client's only derivation is subtracting the current
time from a moment it was handed.**

- **No kernel on the device**, in any form — not hand-written, not generated, not behind a hop.
  A client cannot disagree with the server about a rule because it holds none. **ADR-0021's
  positive rule stands as written**; this is its first concrete instance rather than an
  amendment to it.
- **A card carries the one moment it is about, as an instant** — the confirm deadline, the start
  time, the offer's expiry. The client subtracts and renders a countdown. **This is not
  `nextTransition`**: the moment a card is *about* and the moment a card next *changes* are
  routinely different, and pointing a countdown at the latter drifts the number away from the
  words above it (*"Starts in 15 min"* counting to a commit deadline). Naming the field belongs
  to the `GET /now` wire contract.
- **Reaching zero changes nothing on screen.** The countdown stops; the card does not become
  another card. Zero is instead one of the four things that count as asking — see ADR-0054.
- **`transitions: [...]` is refused, and `nextTransition` has no reader.** Doc 5 A6's fix is
  superseded: it solves offline threshold-crossing, and nothing crosses a threshold unprompted.
  ADR-0038 ships the field anyway on its own grounds — installed phones cannot be forced to
  update — and that argument is untouched here.
- **§4.2's three-layer render does not exist.** There is no layer 2, so there is no locally
  derived card, nothing provisional, nothing to mark, and nothing to reconcile. §4.1's table of
  *may / may not* collapses to its last row: the client may render, and may do nothing else.
- **The countdown runs on the device's own clock**, uncorrected. Server-side time correction was
  considered and refused as an edge case that a network-synced phone does not produce. The
  consequence is that **`serverTime` has no reader either** — ADR-0038 named it the field most
  likely to prove dead weight, and it has.
- **A client never offers what the server did not offer.** It may stop offering; it may never
  start. With no clock it cannot know an offer died, so in practice withdrawal happens when the
  player reaches for it: the action's own response replaces that card. Per
  [ADR-0032](0032-order-is-a-property-of-the-composed-screen.md) that is an **update** — one
  card — never a recompose, so the screen does not reshuffle under a thumb.
- **`frontend_club/` follows the same rule.** Nothing predictive ships to the console and nothing
  ticks. ADR-0005 makes this a separate statement rather than an inheritance, and the console's
  own reason is different: it is a page we redeploy at will, whereas the whole argument for
  shipping a phone something early is that we cannot force it to update.

**No cross-implementation drift test is needed**, because there is no second implementation.
This closes the last thread of ADR-0021's promised *"cross-application contract suite"*, which
[ADR-0040](0040-one-ladder-resolves-a-situation.md) had already narrowed to a generated enum and
an exhaustive switch in each client's own build.

## Consequences

**Easier**

- The single-implementation property becomes structural rather than tested for, on the clients
  as it already is on the server.
- The client is small: a fetch, a render, and one subtraction. No hold ladder, no deadline
  arithmetic, no reconciliation, no merge.
- Retuning any constant changes both apps with no client release.
- Two documents that contradicted each other for months (§4.1 vs ADR-0021) stop being a seam a
  build agent has to arbitrate.

**Harder**

- **A screen is correct only as recently as it was asked.** With nothing predictive and nothing
  on a timer, the residual is bounded by the player's own behaviour rather than by us. ADR-0054
  owns that trade and names the four moments that bound it.
- **`nextTransition` and `serverTime` now ship with no reader and no prospect of one.** They
  survive on ADR-0038's forwards-compatibility argument alone. A later session will read them as
  dead weight and be right about the present tense and wrong about the reason.
- **A card must carry an absolute instant, not a duration.** Any card wanting a countdown has to
  name its moment on the wire; a card that says *"in 15 minutes"* is unrenderable a minute later.
- **Offline is now honestly nothing.** The basement case §4.2 was written for is not solved by a
  worse mechanism; it is not solved. A player with no signal sees the last screen she asked for
  and can tell it is not moving.

**Neutral**

- The 60fps feel ADR-0021 wanted survives on the one thing that still moves — the countdown.
- Nothing here constrains what the kernel *contains*; that remains
  [ADR-0022](0022-kernel-negative-space-and-constant-homes.md).
