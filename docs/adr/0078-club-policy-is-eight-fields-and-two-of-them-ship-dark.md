# ADR-0078 — A club's policy is eight fields, and two of them ship read by nobody

- **Status:** Accepted
- **Date:** 2026-08-21
- **Completes:** [ADR-0077](0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md), which fixed that a policy is versioned **whole** and left its contents to this ticket
- **Answers:** the open items handed here by [#8](https://github.com/Raketa02/Raketa/issues/8) (`maxHoldAge`'s floor and authorship; a hard hold at `n−1`), [#9](https://github.com/Raketa02/Raketa/issues/9) (a turnaround buffer), [#18](https://github.com/Raketa02/Raketa/issues/18) (the counter-cash capability; the cancellation window as a notification moment) and [#30](https://github.com/Raketa02/Raketa/issues/30) (a club's location)
- **Answers:** [ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)'s *"Whether the platform floors the value, and who authors it, is ClubPolicy's decision and is deliberately not made here"*
- **Closes:** `now-section-domain-spec.md` **[GAP-C3]** (two sources of truth for the checkpoint policy) and **[GAP-C4]** (three policy keys published and never read)
- **See also:** [ADR-0079](0079-a-category-is-club-authored-and-it-is-the-priced-unit.md), which takes the court `category` question out of this one

## Context

[ADR-0077](0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md) settled that a
club is a record, that a **policy is changed as a whole rather than a field at a time**, and that
the policy, the payout destination and the court catalogue are three separately versioned series.
It deliberately did not say **what is in the policy**, and it named this ticket as the place.

Five tickets had already handed obligations here without settling any of them, and the pile had a
shape: each one had found a lever that changes what happens to a player, discovered that nobody
authored it, and moved on. Meanwhile the v37 prototype carries a **concrete, running policy
object** (`prototype-v37/rakietaPlayerPrototype.html:6175–6201`) — `POLICY_BASE` merged with
`POLICY[club]` merged with two fields that live on `CLUBS[club]` — which is the behavioural oracle
for all of it. The job was not to invent a field set. It was to read the one that ships, decide
which of its keys are policy at all, and answer the five questions.

Reading it that way sorts sixteen keys into four piles, and three of the piles are not policy.

### What the object actually holds

| Reaches Now | Never reaches Now | Duplicated or dead |
|---|---|---|
| `window`, `joinCut`, `maxHoldAge`, `probHold`, `checkpoint` | `alloc`, `checkinMin`, `slotDisc`, `cancelPriv`/`cancelAcad`/`cancelComp`, `langs`, `legal` | `rebooking` (on `CLUBS`, the same fact as `checkpoint` — **[GAP-C3]**), `holdFar`/`holdNear`/`softDoubles` (published, never read — **[GAP-C4]**) |

Plus, on the club record rather than in the policy: `card[sport]`, `pm`, `km`, and `dist` in
minutes — which [ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md)
already killed.

### Why the scope question is the load-bearing one

Because ADR-0077 versions a policy **whole**, scope is not tidiness — it is cost. A row holding
`legal` means every revision of a facility-rules PDF opens a new policy version, and the question
that motivated versioning in the first place (*what was this club's hold cap on Friday at 16:00*)
gets answered out of a series whose entries are mostly document bumps. The narrower the row, the
sharper the history.

## Decision

**A club's policy is exactly eight fields, all of which change what happens to a player inside a
match. Everything else a club declares is the club record, and is not versioned.**

### The eight

| Field | Type | Default | Read by |
|---|---|---|---|
| `window` | hours | `24` | `commit = min(start − window·h, start − 12h)` |
| `joinCut` | minutes | `30` | `joinCut = start − joinCut·min` |
| `maxHoldAge` | hours, `null`, or `0` | `null` | the ladder's staleness rung |
| `probHold` | bool | `false` | gates the `heldExtended` rung |
| `rebookingCredit` | bool | `false` | the checkpoint's outcome |
| `freeCancelHours` | hours or `null` | `null` | the owner's last free choice |
| `turnaroundMin` | minutes | `0` | widens a Raketa-created reservation |
| `countsCash` | bool | **`true`** | whether a share may be offered as payable at the counter |

**The test for membership is a single sentence: a club decision that changes what happens to a
player inside a match.** `alloc`, `checkinMin`, `slotDisc`, the three cancellation refund tables,
`langs`, `legal` and `pm` all fail it and move to the club record, unversioned. They are read by
screens this map does not build, and none of them alters a match outcome.

### `cardOffset[sport]` is pricing, not policy

The standing per-sport club-card allowance (`0`, an integer, or `'full'`) stays in the money chain
and is read when computing `payable` — but it is **not in the versioned row**. ADR-0077's test does
not separate it from `pm`: neither is ever asked about in the past, because both are inputs to a
price that is **copied onto the match at quote time**. Versioning it would open a new policy
version every time a club tweaks a discount rate, for a question nobody will ever ask — the exact
noise ADR-0077 avoided by keeping the payout destination in its own series.

**And "club card" was naming two different things.** [ADR-0058](0058-one-balance-and-it-never-goes-above-zero.md)
absorbs the checkpoint credit by making it *"a club card entry"*, while `card[sport]` is a standing
discount rate. A rate a club sets and a ledger of credits a player has accrued at that club are not
one object. **`cardOffset[sport]` is the rate and lives here; the club card that receives a credit
is a Money-context record, per player per club, and is not policy at all.**

### `maxHoldAge` has no platform floor, and opting out is sayable

ADR-0031 handed over the question of whether the platform floors this value. **It does not.**
Raketa cannot compel a club to lend inventory to a match that may never form, and a floor is a rule
we could not enforce against a club that simply stops publishing courts. Note the lever is already
narrow: the `filled < n−1` guard means it can only ever reclaim a **`far`**-tier hold on a match two
or more seats short.

But `maxHoldAge: 1` is a hostile number wearing the costume of a setting. So the value is
three-valued and the third value is the honest one:

- **`null`** — never stale; hold to the ladder floor.
- **a positive number** — honoured with no minimum.
- **`0`** — **this club does not hold speculatively at all**, said plainly rather than performed by
  a hold that dies an hour after it is granted.

**`0` needs a sentence the ladder does not have.** The existing release copy is *"a soft hold older
than {N} h goes back on sale"*, which at `N = 0` reads as a bug. It resolves as a **new `why`,
`noSpeculative`, under the existing released situation** — not a new situation.
[ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md) puts the
situation on the wire with its **facts**, and a reason is a fact. **The enumeration stays at 36 and
[#42](https://github.com/Raketa02/Raketa/issues/42) stays closed** — a 37th situation would buy a
distinct card for a state differing from *released* only in why, at the cost of reopening a ticket
that closed two days ago.

### There is no hard hold at `n−1`, and there never was

[#8](https://github.com/Raketa02/Raketa/issues/8) left this open as the home for whatever
`protectedCourt` / `protectedLate` were reaching for. **No field is added, and this is not a new
restriction — it is a name for what already ships.** `courtHold` at `f >= n−1` returns
`{kind:'soft', why:'near'}` or `{kind:'none', why:'farLapsed'}`, **never `hard`, for any `n`** —
including `n = 2`, which the specification's own note (*"unreachable by any natural path for a
4-player open match"*) understates. Both contexts are reachable only through full, committed,
locked or private, all tested earlier in `matchState`.

**Why no such lever should exist:** a hard hold at `n−1` means a club may not sell that court to a
paying private booking while one seat is still unpaid. That is Raketa taking inventory risk it does
not pay for, on the club's balance sheet, in exchange for a match that might not form.

### `rebookingCredit` replaces two fields that encoded one fact

**[GAP-C3] is closed by deletion.** `POLICY[club].checkpoint` (`'rebook'`/`'short'`) and
`CLUBS[club].rebooking` (boolean) are independently seeded and nothing enforces agreement; the
domain spec's own note is that *"a drift here cancels a match that should have lived, or keeps
alive one that should have been credited — money in both directions."* The spec proposes deriving
one from the other, which fixes the drift but keeps a two-valued string standing in for a boolean.

**`CLUBS.rebooking` is deleted and `checkpoint` is renamed `rebookingCredit`, a boolean.** What a
club decides is *does this club offer rebooking credit when a committed match is short at the
checkpoint*, and `3.1-enrolled_match_states_and_transitions.md`'s own copy already says it that
way: *"This club does not offer rebooking credit, so the match stays alive."* The field is named
the sentence. **The money side is untouched and already settled** — ADR-0058 makes the credit a
club card entry, club-initiated (`I-12`), never platform credit.

**The drift was latent, not actual.** All nine seeded clubs agree across the two fields, so nothing
needs reconciling on the way in.

### `turnaroundMin` widens a range; it does not become a second concept

[#9](https://github.com/Raketa02/Raketa/issues/9) asked whether a club needs a buffer between
reservations, which [ADR-0035](0035-a-reservation-claims-a-court-over-an-interval.md) does not
model. **It does, because on the marketplace path Raketa creates the reservation and the club has
nothing to pad.**

- A reservation's **claimed** interval is the played interval **plus `turnaroundMin`**. ADR-0035's
  *"exclusion is by overlapping interval, enforced by the database"* is untouched: there is still
  one range and one exclusion rule. A buffer checked *separately* from the overlap would make *"is
  this court free"* two questions with two answers — the failure ADR-0035 exists to prevent.
- **The player sees the played interval, always.** A card printing `18:00–19:40` for a 90-minute
  game is a lie about what was bought, and the price is for the played interval regardless.
- **It applies only to reservations Raketa creates.** Intervals a club publishes are already padded
  however that club likes; padding them again double-books the gap and quietly shrinks the club's
  sellable day.

### `freeCancelHours` is a moment, not a refund table

[#18](https://github.com/Raketa02/Raketa/issues/18) established that the cancellation window is no
longer a money escape hatch — collection happens after the event at every club
([ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md)) — but that it remains *the
moment the owner's last free choice expires*, and is therefore policy-bearing **for notification,
not for money**.

So the field is **one number of hours before start, `null` meaning the club offers none**. The
three v37 refund tables (`cancelPriv`/`cancelAcad`/`cancelComp`) are club-info-screen copy on the
club record. **The default is `null` rather than the prototype's 24**: that 24 lives inside a
refund table whose money meaning ADR-0047 removed, and inheriting a number from a structure we
deleted is how a dead decision comes back.

### `countsCash` defaults **on**, and the risk moves to the offer

[ADR-0059](0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md) fixed that a
counter mark is authoritative and that a late one is **refused** — the club returns the cash at the
counter. What was open is whether the *capability* is policy, and what a club that never marks
looks like. The failure is sharp: **a club that never marks charges an owner for money the club is
already holding.**

**Defaulting the capability off would not have fixed it, and would have been false.** Every Polish
racket club takes cash at its counter; entering nine of them as *refuses cash* describes none of
them. And a default is only a fail-safe when clubs arrive unattended — under the authorship rule
below they arrive **one at a time, hand-entered**, so a default is a value in a form, not a silent
fleet-wide fallback.

**The risk attaches to the offer, not to the club's willingness, so they are two facts** — the same
split [ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md) made
between a city and an anchor:

| | What it says | Where it lives | v1 |
|---|---|---|---|
| **`countsCash`** | Does this club take cash at its counter | Policy, ops-authored | **`true`** |
| **Whether Raketa offers *pay at the club*** | Is there a surface that can mark it | Platform capability, gated on that surface existing | **Off everywhere** |

**A gate is stronger than a default**: a default can be overridden into the failure, a gate cannot.
And in v1 there is no marking surface at all — ADR-0059 puts it on the club console, which this map
holds out of scope.

### Two fields ship read by nobody, deliberately

**`countsCash` and `freeCancelHours` have no v1 reader.** `freeCancelHours`' only two consumers are
the owner messages ruled out of scope on [#44](https://github.com/Raketa02/Raketa/issues/44) —
*specified and undeliverable*; `countsCash` is gated off by the missing marking surface. They ship
anyway, because **the fact is cheap to capture while a human is entering the club and expensive to
backfill across every club later** — which is ADR-0077's own `changedBy` argument (*"a column added
later leaves every old row claiming an actor it never had"*) applied one context over.

**A consequence to carry: ADR-0059's refusal rule is unexercised in v1.** Nothing can produce a
late mark, because nothing can produce a mark. The first session to build the console must not read
that silence as *nobody needed this*.

### `clubExtended` and `clubFill` stay on the match, and nothing recomputes them

Invariant 6 — *this app never recomputes a club's model* — names a regression that already
happened once, where two apps disagreed about whether a court was held. The split that prevents it
is already correct in the domain spec's field table and is affirmed here rather than changed:

- **The policy carries `probHold`** — may this club ever hold past the ladder.
- **The match carries `clubExtended` and `clubFill`**, marked `S (external)`, written by the club.
  A fill probability is a fact about one match at one hour and could not live on a club.
- `clubExtended(m) = m.clubExtended && pol(m.club).probHold`. Extension may only ever **lengthen**
  a hold; no model may release a court earlier than the ladder promised.

**The v1 consequence nobody had written down: with no club console, no surface writes either field,
so `heldExtended` is reachable only from seeded data.** That is not a defect — the rung fails safe
(absent ⇒ no extension ⇒ court released at the ladder floor) — but it means
[#52](https://github.com/Raketa02/Raketa/issues/52) is the only thing that will ever produce that
card.

### `holdFar`, `holdNear` and `softDoubles` are deleted

**[GAP-C4] is closed by deletion, not by wiring them up.** They are the ladder's own constants, and
a club-settable `holdFar` would let a club **shorten** the ladder — which ADR-0031's Rule 12
forbids outright (*a club may hold longer than the ladder promises, and never shorter at the same
level of certainty*). Publishing a lever nobody may pull is worse than not publishing it: it invites
exactly one implementation to read it.

### A club carries an address, a point and a zone

[#30](https://github.com/Raketa02/Raketa/issues/30) called a club's location *"the only thing
standing between ADR-0063 and a distance a player can see."*

- **A street address and a geocoded point, both stored.** Unlike a player — where ADR-0063 keeps
  the anchor coarse for privacy — a club is a public venue with a front door: no reason for
  imprecision, no consent to ask.
- **`km` is derived at read time** from the point and the player's anchor. Never stored, never
  pre-rendered. **`dist` in minutes is deleted**, per ADR-0063.
- **The point is supplied by hand at authoring time**, not by a geocoding API and never lazily. A
  lazy geocode puts a third-party call on the path that computes every distance on the busiest
  screen in the app, and fails as a blank distance rather than as an error somebody sees. There are
  nine clubs and a human is entering them; the console can offer a map picker later without the
  stored shape changing.
- **`Club.timezone`, an IANA name, entered with the address.** Three things read a club's zone —
  ADR-0024's `slot_start(anchor, day, minute, tz)` (*"the single conversion"*), `CONTEXT.md`'s rule
  that a match's start is read against declared hours *"through the club's zone"*, and
  [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md)'s *"the moment carries the
  club's zone beside it"* — and **no field existed**. A constant would be true today and is the
  trap: ADR-0063 made the city a field from day one *"so nothing downstream may assume one
  market"*, and a hardcoded `Europe/Warsaw` is that assumption buried somewhere far less visible
  than a header.

### Raketa ops authors all of it in v1

There is no club console and **no role concept on `User`**. Ops authors the policy, the record, the
address, the point and the zone, on the club's instruction. ADR-0077 already accepted the cost that
every history entry reads *"changed by: system"*; this is that cost arriving. **The console takes
authorship later and nothing in the model changes when it does** — which is the whole reason the
shape is decided now and the screen is not.

## Consequences

**The policy row is eight fields and every one of them has a named reader** — or a named reader it
is waiting for, written down as such. That is the property to preserve: the next field proposed for
this row has to name what it changes about a match, or it belongs on the club record.

**Six keys and one field are deleted from a running prototype.** `holdFar`, `holdNear`,
`softDoubles`, `CLUBS.rebooking`, `dist`, and `checkpoint` (renamed). Anyone diffing v37 against
this will find the object smaller and should find this ADR rather than assume an oversight.

**Two of the eight are dark in v1, and one is dark for a reason that will change without warning.**
`countsCash` turns on the moment a marking surface exists — that is a **platform** gate, not a
per-club one, so building the console's mark screen silently opens the counter-cash channel at
every club that has `countsCash: true`, which is all of them by default. The session that builds it
owns the rollout, and ADR-0059's obligation (the window and the outstanding shares visible to the
club throughout) is the precondition, not a follow-up.

**A new `why` lands on a table that closed two days ago.** `noSpeculative` joins the released
situation's reasons. #42 stays closed and the enumeration stays at 36, but the copy table gains a
sentence and whoever writes it should know it arrived after the count was fixed.

**`turnaroundMin` defaults to `0`, so the buffer ships unexercised too.** No seeded club sets it.
The first club that needs one will be the first test of whether widening the claimed interval
really is invisible everywhere the played interval is printed — and the places that print it are
not enumerated anywhere.

**The club card is now two things with one name, and only one of them is here.** `cardOffset[sport]`
is settled; the per-player-per-club credit record ADR-0058 implies is **not modelled** and belongs
to Money. Nothing on Now reads it, so it is not fog on this map, but the name collision is real and
the next Money session should find it named.

**`km` derived at read time is an unmeasured cost.** Every card on Now carries a distance, and the
budget work ([ADR-0069](0069-the-budget-is-two-budgets-and-both-fail-the-build.md)) priced a
composed screen without a per-card distance computation in it. The arithmetic is trivial; doing it
fifty times per request against a stored point is the thing nobody has measured.

**A club policy still has no console, and ops is a person typing.** Nine clubs is fine. The first
time this is fifty, hand-authorship is the bottleneck and `changedBy: system` stops being a
tolerable simplification — but neither is a v1 problem, and pre-solving them is how the console
arrives through the back door.

## Alternatives considered

**Floor `maxHoldAge` at the platform level.** Refused: unenforceable against a club that stops
publishing inventory, and it prices a lever whose reach is already bounded to `far`-tier holds on
matches two or more seats short.

**Default `countsCash` to `false` as a fail-safe.** Refused, and the reasoning was wrong rather
than merely cautious: it describes no real club, and a default is only fail-safe where clubs arrive
unattended. Gating the **offer** on a marking surface is the stronger fix, because it cannot be
overridden into the failure.

**One row for everything a club declares.** Refused: it makes a facility-rules PDF revision open a
policy version, and buries the one question versioning exists to answer.

**Derive `rebooking` from `checkpoint` rather than deleting one.** Refused: fixes the drift, keeps
a two-valued string standing in for the boolean the domain copy already speaks.

**A 37th situation for `maxHoldAge: 0`.** Refused: a distinct card for a state differing from
*released* only in why, bought with a reopened ticket.

**Derive the club's timezone from its geocoded point.** Refused: a reverse-geocode with a failure
mode, bought for nothing when a human is already typing the address.
