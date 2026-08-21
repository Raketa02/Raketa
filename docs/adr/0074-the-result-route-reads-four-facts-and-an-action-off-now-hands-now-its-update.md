# ADR-0074 — The result route reads four facts, and an action off Now hands Now its update

- **Status:** Accepted
- **Date:** 2026-08-21
- **Resolves:** [`Raketa02/Raketa#43`](https://github.com/Raketa02/Raketa/issues/43)

## Context

[ADR-0060](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md) put the result
conversation on a route of its own and, in doing so, put a **second reader** beside the composed
screen. [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md) drew what `GET /now`
returns and said nothing about this one, because it did not have to.

The slate is as blank as ADR-0070's was: `backend/app/` exposes auth, users, sports and ratings,
and **no route reads a match at all**. Every name below is free.

Three constraints arrive already settled, and between them they do most of the work.

- **The phone holds no rules** ([ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md)):
  a client subtracts the current time from a moment it was handed, and derives nothing else.
  ADR-0048's permissions are the sharpest test this rule has faced — accepting is
  opposing-side-only and one person suffices, countering is open to anyone who played *including*
  your own side, a side may propose once, and a leaver may do none of it.
- **The match holds four score facts and no list**
  ([ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)): the score on the table, who put
  it there, whether it is agreed, and how many proposals have been made. *A count, not a
  sequence.* Superseded proposals are announcements.
- **A refusal is not a second shape** (ADR-0070): an act that no longer applies returns what a
  success returns — what is true now — and the player *sees* it rather than being told it.

One thing the ticket asked for is a collision rather than a choice. It listed *"the proposal
history, who proposed what and when"* as a candidate payload; ADR-0034 has already refused to keep
one. Projecting it out of the outbox is `playerEventsTracker`, which this map rules out of scope.

And one thing nobody had noticed. ADR-0054 names *"entering a score"* as an action, and defines
**arrival** as *"the player opens the app, or switches back to it from another app."* A player
popping back off the result route has done none of the four things that count as asking — so
without a deliberate answer, Now sits underneath holding a card that says the wrong thing, with
nothing to trigger a correction.

## Decision

**We will serve the result conversation as one route that reads four facts and states what the
viewer may do, and whose writes hand Now the update ADR-0054 promised.**

### The route

**`GET /api/v1/matches/{matchId}/result`**, and the three writes under the same path.

- **It embeds the match's spine verbatim** — the same object `GET /api/v1/now` sends: which match,
  the moment and the club's zone, where, how much. The player arrives having just read those facts
  on a card, and ADR-0070's own argument against repeating the city in two answers applies
  unchanged: two definitions of *when and where* is how two answers come to disagree.
- **It is not a card.** No fit badge, no emphasis flag, no card stamp. All three are judgements
  the *composition* made about a card's place on Now, and none of them means anything on a screen
  with one thing on it.
- **It carries the situation off the same ladder**, per ADR-0060's *render by situation, not by a
  screen identifier* — so entry, the two audience renderings of a live proposal, the counter, the
  settled result and the unscored ending are **one reader** with five renderings.
  [ADR-0040](0040-one-ladder-resolves-a-situation.md) survives intact; a second endpoint for *the
  settled case* would have been the second vocabulary it exists to prevent.
- **A general `GET /matches/{id}` was refused.** It authors the match-detail screen's contract
  inside a ticket that is not about it — and that screen is out of scope precisely so a later
  effort can draw it properly. It would also be the attractive nuisance every later screen reaches
  for instead of asking for what it needs.

### What it carries, and what it does not

**The result block is the four facts and nothing more.** No history: a counter *replaces* what is
on the table, and printing the score it beat invites arguing with a number that is no longer live.
None of ADR-0060's renderings draws a timeline.

**The block is always present, and empty when nothing is on the table.** An empty score and a zero
count on `needsResult`, not an absent object. ADR-0070 answered the same shape twice and in
opposite directions — a shelf with nothing is **absent** because it makes a claim, a region with
nothing is **present and empty** because it makes none. The result block makes none. This also
removes the most productive bug in the class: *not there* and *there and empty* handled in one
place and not the other. The **situation half stays optional** as ADR-0070 fixed it — that one can
genuinely be unknown to an old phone, where a score a phone cannot read is not a thing.

**Two clocks, both named, and the grace is shown.** A card gets exactly one clock slot because a
36-row rule about *which fact is the clock* must not live on the phone (ADR-0070,
[ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md)). That argument does
not bind a screen resolving one situation, and this one has two live deadlines at once: the
**24-hour settlement deadline** and the **30-minute acceptance grace** inside which a counter beats
a pending acceptance ([ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)).
The settlement deadline is the hero, per ADR-0060. The grace is a second, quieter line, present
only while it runs.

- **Hiding the grace was refused.** It produces the outcome ADR-0048 built it to prevent, inverted:
  a player taps accept, the screen says *settled*, and thirty minutes later it is not. That reads
  as the app lying about the one thing the screen exists to state.

**A score is an ordered list of sets, each two integers, the viewer's side first, sides named by
their players.** ADR-0060 fixed per-side and never a display string; this fixes the value.
**No tiebreak field in v1** — nothing in the specification set has ever asked for one, and
[ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md) has just refused a
field with no reader. **The server validates.** The per-sport pads — 0–7, 0–11, 0–21 — are an
instrument for typing a score standing on a court in the dark, not a rule: ADR-0053 forbids the
phone deciding whether 7–6 is legal padel.

### What the viewer may do

**The server states the acts as three named booleans — `mayEnter`, `mayAccept`, `mayCounter` —
and the phone derives none of them.**

- **Not a generic list of act codes**: it invents a vocabulary to describe three things nothing
  else in the product reads. This is the call ADR-0070 made for the debt line — send the
  consequence, not the inputs.
- ADR-0048's cap (*a side may propose once*) and its exclusions (never a leaver, never a standby
  player, per [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md)) are therefore enforced in
  **one** place rather than mirrored onto two clients that will drift.

### The writes

**Entering, accepting and countering are three writes under the same path, and each returns the
identical payload a read returns.**

A stale accept — you tapped accept on a score countered while your screen was open — comes back as
the counter's situation with `mayAccept` false. One code path on the client, and it is the one it
already has for Now.

**No version crosses the wire.** ADR-0034 gives the match a version and guarantees two concurrent
writers cannot interleave; the server's own rules land every concurrent case somewhere defensible
without the client holding one. Two teammates countering at the same instant: one wins, the other's
response says their side has proposed. Two opponents accepting: the second is a no-op on an
already-accepted result. A client-held version would make the phone hold a rule about its own
staleness, and would buy a distinction the player cannot act on differently.

### An action off Now returns Now's update

**A write on this route returns its own screen's answer *and* Now's update, in one response.**

ADR-0054 wrote its action rule with this exact act named in it — *"joining a match, taking a seat,
entering a score… the response to the action updates the screen off the player's own tap"* — and
this is the **first action in the product that happens off Now**, so it is where that rule gets its
shape. The update is ADR-0070's existing update shape: the one card that changed, plus either
viewer-owned region whose contents or order moved, whole. The shelves are never in it.

- **The duplication is real and accepted.** The match's spine and situation appear twice in one
  response — once for the route, once inside the Now card. They are not two answers that can
  disagree: same read, same transaction.
- **Recomposing on the pop was refused.** ADR-0068 deleted the player feed cache, so *every ask
  pays the full funnel*; paying it on every return from a screen the server has just finished
  computing is a cost bought for tidiness.

**And this fixes, for everything later: arrival is the app foregrounding, not a screen becoming
visible.** ADR-0054's wording already says so; recording it here stops the next screen's session
reading *arrival* as *this screen appeared* and putting a funnel run behind every back button in
the app.

### Who may open it

**Anyone who held a seat when the match ended resolves normally — including a leaver — with the
three booleans false where ADR-0048 says so. A stranger gets a 404.**

The leaver is the case that proves the rule. They played half an evening and paid for it; a 404
tells them their match never existed, which is exactly the class of defect ADR-0030 was written
against. A match still forming resolves to its forming situation with an empty result block — dull,
correct, and not a special case. The stranger is **authorisation, not situation**, and that is the
one place a different shape is right.

## Consequences

**Easier**

- The player app's second screen has a contract that reuses the first one's spine, situation
  vocabulary, update shape and refusal shape. Nothing about it is a new idea.
- ADR-0048's permission rules exist in exactly one place. The two clients hold none of them, and a
  correction to the rules is a server deploy.
- Five renderings, one reader, one ladder. A sixth post-match situation is additive.
- Every future action taken off Now now has a pattern to copy rather than a question to reopen.

**Harder**

- **`matches` enters the player contract as a resource for the first time**, and it enters through
  a sub-path of a screen. The match-detail screen will want `GET /api/v1/matches/{id}` and will
  find `/result` already hanging off it — a shape it did not choose. That is the price of not
  authoring its contract here, and it is the cheaper of the two bills.
- **One response now serves two screens.** It is coherent today because the result route is the
  only thing that writes off Now; the moment a second off-Now action exists, *which* regions an
  update may carry stops being obvious, and this ADR is the precedent that will be read as
  permission.
- **The grace is a second clock on a screen whose countdown was meant to be the hero.** Two live
  timers compete, and the quieter one is quiet by instruction rather than by construction.
- **No history means a disputed result is unreconstructable from the product.** Support can read
  announcements; a player cannot, and a player who wants to know what the other side originally put
  has no answer. Accepted, and it is ADR-0034's cost being paid rather than a new one.

**Neutral**

- Nothing here is built. No route, schema or OpenAPI path exists, so `make gen-api` has never
  emitted any of this — the same standing as ADR-0070's contract.
- The copy is untouched and still the client's, per
  [ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md). The four
  sentences ADR-0048 §10 names are [#44](https://github.com/Raketa02/Raketa/issues/44)'s.
- ADR-0048's own gap stands untouched: **nothing in the flow can say "no"**, so a side that believes
  the match was abandoned rather than played still has no move but silence, and still lands on
  `playedNoScore` a day later.
