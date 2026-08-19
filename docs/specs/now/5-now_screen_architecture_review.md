# Now Screen Architecture Review

*A validation of the four Phase 3 documents — the Now screen spec, the enrolled-match
engine, its state model, and the recommendation engine — read end to end and checked
against what `rakieta` has actually built and already decided.*

**Date:** 17 August 2026
**Scope:** 4 documents, ~4,900 lines · 21 findings · 14 affirmed

**Sources read in full**

- `1-now_screen_production_spec.md`
- `3-enrolled_match_engine_architecture.md`
- `3.1-enrolled_match_states_and_transitions.md`
- `4-match_recommendation_engine_architecture.md`

**Checked against**

- `docs/adr/0015`, `0021`, `0022`, `0026`, `0027`
- `CONTEXT.md`, `CONTEXT-MAP.md`, `backend/CLAUDE.md`
- `backend/app/engines/{fit,forecast,matchmaking}.py`, `matchfit/v1/`, `pairing/v1/`, `app/kernel/`

---
---

# THE VERDICT

**The feature is right and worth building.** The argument that a booking app's home screen
should be a status surface before a search box is correct, and the enrolled-match
architecture is about eighty percent of what I would build. Nothing here asks you to change
what the screen *is*.

**Two things need to change before any of it becomes code.** The recommendation engine
described in these documents has already been built differently in this repo, on purpose —
ADR-0027 diagnoses the exact seven-factor model in Part 5 of the Now spec as broken, and the
engine that shipped four days ago replaces it. And the enrolled-match state model has a rung
that cannot fire, which makes two of its thirty-three states unreachable.

**The sequencing question is the sharper one.** This feature is a surface over four bounded
contexts that `CONTEXT.md` lists as *not modelled yet*. The next artefact is not the Now
screen — it is the Matches aggregate ADR that ADR-0026 was written to feed.

## Where each document stands

| Document | Verdict | Why |
|---|---|---|
| **The Now Screen**<br>`1-now_screen_production_spec.md` | **Amend** | Purpose, interaction model and copy rules are sound. Part 5 carries the superseded Match Fit model; Parts 2–3 are CSS for an HTML prototype and cannot be applied literally to a React Native app with a locked design system. |
| **Enrolled Match Engine**<br>`3-enrolled_match_engine_architecture.md` | **Keep** | The strongest of the four. One writer, derive-don't-track, idempotent wake-ups, patch-not-list — all correct. Two holes: cross-aggregate court allocation, and a trust property it claims but does not have. |
| **States and Transitions**<br>`3.1-enrolled_match_states_and_transitions.md` | **Amend** | The three-axis model is right and the reasoning is excellent. The resolution ladder has one unreachable rung, one missing gate, and one whole player position — the leaver — with no state at all. |
| **Recommendation Engine**<br>`4-match_recommendation_engine_architecture.md` | **Replace §3.3** | The funnel, the lanes and the pull-not-push decision are all right and should be kept verbatim. The scoring stage and its performance premise are both wrong against the engine that exists. |

## Findings at a glance

| ID | Severity | Finding |
|---|---|---|
| **A1** | Blocking | Match Fit as written is the model ADR-0027 was accepted to remove |
| **A2** | Blocking | Coverage exists and neither the ranking nor the badge reads it |
| **A3** | Blocking | Travel and price are used as exclusions, which ADR-0027 forbids |
| **A4** | Blocking | The determinism invariant forbids exploration, which the ranker must own |
| **A5** | Blocking | "Every string comes from the server" is the opposite of what this repo decided |
| **A6** | Blocking | "The kernel ships to both clients — that is already established" — it is established as *rejected* |
| **B1** | Defect | Rung 9 cannot fire, so `formingBack` and `protectedBack` are unreachable |
| **B2** | Defect | A player on the standby list of a played match is asked to enter the score |
| **B3** | Defect | There is no state for the player who left, and it is the money-bearing one |
| **B4** | Defect | `start` is not immutable, so "the strip never reorders" is false |
| **B5** | Defect | Hold-ladder rules 11 and 12 contradict each other |
| **B6** | Note | `formingLate`'s two context lines key on a fact that is not stored |
| **B7** | Note | Two states claim to be the only one where a player loses money |
| **B8** | Defect | Two simultaneous leaves are not rare enough to leave unhandled |
| **C1** | Blocking | The single-writer story protects the match and leaves the court unprotected |
| **C2** | Blocking | "Any read is still correct" is false for exactly the four bad-news transitions |
| **C3** | Note | "Derive, never track" is stated absolutely over a list of seven written facts |
| **D1** | Blocking | The flyweight's premise does not hold against the engine that exists |
| **D2** | Note | `NoScheduleConflict` is the best addition in the document and is scoped too narrowly |
| **E1** | Defect | Parts 2 and 3 are CSS for the prototype, and the target is React Native |
| **E2** | Note | The fit badge at 90+ breaks the document's own colour rule |
| **E3** | Defect | The Now spec holds three incompatible positions on client-side derivation |
| **E4** | Note | "You are 2nd on the standby list" is a precise number for an unobserved event |

---
---

# PART A — CONFLICTS WITH DECISIONS ALREADY ACCEPTED

*These are the blocking ones. Each would either regress work that already shipped or
contradict an ADR whose reasoning is stronger than the document's.*

## A1 — Match Fit as written is the model ADR-0027 was accepted to remove

**Blocking** · Now §5.2 · Rec §3.3

Both documents specify seven weighted terms summing to 100, three modifiers applied after
the sum, a clamp to 20–99, and friendly defaults for missing evidence — balance `0.70`,
reliability `0.80`, skill overlap scoring against the player's own level when nobody is
seated.

**Evidence**

> Score an empty match with those defaults — counted, cheap, nearby — and it comes to
> **90,5**. Score the prototype's own canonical fully-formed, well-balanced, well-priced
> match and it comes to **84**. That is not a tuning problem. **The score is monotonically
> decreasing in information.**
>
> — ADR-0027, accepted 2026-08-17

The engine that replaced it is in `backend/app/engines/matchfit/` and is complete — ten
terms, every signal a term, no modifier applied outside the weighting, coverage reported as
its own number, and no clamp.

| Documents — 7 terms + 3 modifiers | | Shipped — 10 terms, no modifiers | |
|---|---:|---|---:|
| Skill overlap | 30 | Skill overlap | 24 |
| Predicted balance | 20 | Predicted balance | 14 |
| Group reliability | 15 | Time fit | 12 |
| Time and travel | 15 | **Match viability** | 12 |
| Match type | 8 | Group reliability | 11 |
| Price vs ceiling | 7 | Travel | 8 |
| Preferences and side | 5 | Ladder qualification | 6 |
| | | Price | 6 |
| | | Match type | 4 |
| | | Familiarity | 3 |
| *plus* `+8` promotion, `+5` new opponents, `−8` the same four again. Clamped 20–99. | | Ladder and familiarity became **terms** precisely because a bonus outside the weighting has no meaning once weights renormalise. | |

Note what the new table adds that the documents never had: **match viability at weight 12**
— *will this match actually be played* — which is a large part of what "Best fit" is for and
is nowhere in Part 5.

**Fix**

Delete Rec §3.3's term table and Now §5.2 entirely and point both at `app/engines/fit.py`
and `matchfit/v1/constants.py`. The section subtitle becomes *"Ranked on ten things, not
just level."* The card contract's `fit` object changes from
`{score, reasons: string[], warn}` to `{fit, coverage, terms, reasons: TermCode[], warning}`.

---

## A2 — Coverage exists and neither the ranking nor the badge reads it

**Blocking** · Now §3.9, §5.3 · Rec §3.3, §3.4

The shipped engine returns two numbers. Every ranking rule in these documents reads one.
`FEED_ORDER` sorts on `fit.score`; the waitlist lane floors on fit alone; and the coral
`.fit.hi` badge fires at exactly 90 with nothing else consulted.

**Consequence**

At launch, coverage is structurally low: reliability and familiarity ship dark, and skill
overlap is excluded whenever nobody is seated. So the highest fit scores will systematically
belong to the matches the platform knows least about — and Now will paint a coral *drop what
you are doing* badge on them. That is the failure ADR-0027 exists to prevent, arriving
through the presentation layer instead of the arithmetic.

> Renormalisation makes scores less comparable across matches than a fixed denominator does:
> two matches scoring 80 may have been scored over different term sets. Coverage is what
> makes that visible, but it does not make it go away, and **a naive sort across mixed
> coverage will mislead**.
>
> — ADR-0027 · Consequences · Harder

**Fix**

Give `LaneConfig` a `coverage_floor` beside its `floor`, and put coverage in the comparator
chain after fit. Gate `.fit.hi` on both — a 93 at 40% coverage is not a 93. Below the
coverage floor, render the badge in `--night` with no coral, which the design system already
supports.

---

## A3 — Travel and price are used as exclusions, which ADR-0027 forbids

**Blocking** · Rec §3.1, §3.2

Retrieval filters on `club_id = ANY($clubs_within_travel)` and eligibility carries a
`WithinTravelCeiling` rule emitting `'too-far'`.

> Candidate generation excludes on facts, never on preferences. Sport, seats remaining, the
> join cutoff, live inventory and calendar conflicts are hard filters. **Distance, price and
> level are never exclusions** — the intent pool's rules are explicit that *nothing is ever
> excluded on distance* and that price is *a condition, not a rejection* — so they reach the
> player as a lower score, not as an absence.
>
> — ADR-0027 · Decision

This is not pedantry: the travel term at weight 8 and the price term at weight 6 both exist
to grade exactly these, and a match removed before scoring cannot be graded. It also silently
changes the meaning of an empty feed from *nothing is open* to *nothing is open nearby*,
which is a different sentence than the one Now §5.5 promises to say.

**Fix**

Bound retrieval by city and by a generous geographic ceiling that is a cost valve, not a
preference — the same standing as the `LIMIT 300`. Drop `WithinTravelCeiling`. Rec §3.6's own
example of the trace's value (*"91% of candidates excluded as too-far"*) needs replacing,
since that bucket no longer exists.

---

## A4 — The determinism invariant forbids exploration, which the ranker is required to own

**Blocking** · Rec §3.3, §5.3, §9.1

Output invariant 9 reads *"the same request twice, same world → byte-identical feed"*, and
the acceptance gate demands it a thousand times over. ADR-0027 puts exploration in the ranker
for the opposite reason.

> A list ranked purely by fit-to-this-player starves the supply side: a newly created match
> has little evidence, ranks low, gets no impressions, does not fill, and confirms its own
> score. Fixing that needs exploration — deliberately showing some matches the score does not
> yet favour — and exploration needs controlled randomness, configuration and experiments.
>
> — ADR-0027 · Context

Both properties are wanted. They are only in conflict because the document treats determinism
as byte-identity rather than as reproducibility.

**Fix**

Restate the invariant as *reproducible from stored inputs*: the feed is a pure function of
`(player, minute-bucket, exploration seed)`, and the seed ships in the `FeedTrace`. ADR-0026
already rounds `now` to the minute for exactly this reason — *"makes every score reproducible
from its stored inputs, and makes a result cacheable for a minute instead of never."* The
60-second feed cache in Rec §6.1 falls straight out of it.

---

## A5 — "Every string comes from the server" is the opposite of what this repo decided

**Blocking** · Now §8.2 · States §10.1

Both documents state it as a principle, and Now §8.2 adds that *"the client owns exactly
three things: layout, the countdown tick, and the seat glyph geometry."*

> The backend sends numbers and machine codes and never display text (ADR-0022), so each
> client formats — and both implement one table, in `docs/value-formatting.md`. That is not a
> design system and holds no colour or size; it is the exact string a price, a level, a time
> or a duration becomes… **Copy is not formatting**: the sentence behind an unavailability
> code is each app's own.
>
> — `CONTEXT.md` · Terms the clients must not reinvent

The shipped fit engine enforces this at the type level — it emits `TermCode` plus a payload
of grosze, minutes and exact ratios, and no sentence. A client *must* build the reason
string; there is nothing else to build it from.

There is also a fact neither document mentions: **this is a Polish product**, and the copy is
specified in English throughout. Server-side copy makes every wording change a backend
release and locale a backend concern.

**Fix**

The server sends `{key, tone, facts}` — the state key and the quantities behind it. The
client renders copy per key. This does *not* weaken ADR-0021: deciding the key is the rule
and stays on the server; turning `{key: 'replacement', leaver: 'Ola', share: 3800}` into a
sentence is formatting. The thirty-three-row content contract in States §5 becomes a client
copy table, which is where the two clients' different voices belong anyway.

---

## A6 — "The kernel ships to the server and both clients — that is already established"

**Blocking** · Enrolled §4.1, §4.2

It is established as *rejected*. ADR-0021 considered a TypeScript kernel per client and a
kernel behind a network hop and refused both; the backend is Python and cannot run in Expo,
so the mechanism is unavailable at any price. The whole ADR exists because that sentence
stopped being true.

What matters is that the *intent* survives. Enrolled §4.2's layer 2 — the card stays right
through a threshold with no network — is exactly what ADR-0021 built a replacement for, and
the document is already most of the way there with `nextTransition`.

> Time-varying answers ship with their transition schedule. A resource whose state changes at
> instants known in advance carries the current value, an **explicit list** of `{at, …}`
> transitions, and a `computed_at`. The client renders by comparing `now` against instants it
> was handed… The schedule is an explicit per-resource list, never a generic patch stream.
>
> — ADR-0021 · Decision

**Fix**

Change `nextTransition: {at, becomes} | null` to `transitions: [{at, key, tone, facts}]` —
the list, not the head. `nextWakeAt()` already enumerates the candidates, so producing the
list is free and it is bounded at roughly five entries. The client then crosses *several*
thresholds offline while holding no rule at all, which is strictly better than the document's
design and needs no kernel on the device.

---
---

# PART B — DEFECTS INSIDE THE STATE MODEL

*These are true independent of this repo. They are bugs in the specification itself, and the
first two would be found on the first day of implementation.*

## B1 — Rung 9 cannot fire, so `formingBack` and `protectedBack` are unreachable

**Defect** · States §1.2, §1.4 rung 9, §3.2, §6.2

The fact table writes `vacated` in one circumstance only:

```
vacated   | player id | Written when: A committed player leaves
```

Rung 8 catches `vacated AND committedAt ≠ null`. Rung 9 needs `vacated AND committedAt = null`
— a combination the fact table can never produce. Yet §3.2 and §6.2 both route an uncommitted
leave to `formingBack` / `protectedBack`, and §7.3 draws the branch.

There is a second problem in the same rung. `vacated` is never cleared, and rung 9 sits
*above* rung 10, so once it can fire, a match that refills would read `protectedBack` forever
rather than `full`. §5's own OUT rows say the opposite. The documented decay — *"24 hours
pass with no further change → forming"* — has no mechanism at all.

**Fix**

Write `vacated` / `vacatedAt` on *any* leave, and give rung 9 the bound it is missing:

```
 9  vacated AND committedAt = null
    AND not isFull
    AND now < vacatedAt + 24h        → isProtected ? protectedBack : formingBack
```

That makes both states reachable, makes the 24-hour decay mechanical rather than
aspirational, and stops a recovered match being pinned in a recovery state. It also gives B8
the shape it needs.

---

## B2 — A player on the standby list of a played match is asked to enter the score

**Defect** · States §1.4 rungs 5–6

Rung 5 (`now ≥ matchEnd` → the post-play group) sits above rung 6 (`not my seat AND on the
waitlist` → `waitlisted`), and rung 5 has no test for whether the viewer is actually *in* the
match. A waitlisted player whose match has been played falls into rung 5 and gets
`needsResult` — *"Needs result · thirty minutes, any of the four"* — for a match they did not
play.

The same hole would catch a leaver, if a leaver had a card at all (see B3).

**Fix**

Move rung 6 above rung 5, or gate rung 5 on holding a paid seat. Moving it is cleaner — *"am
I in this match at all"* is a coarser question than *"what happened to it"* and belongs higher
in the ladder, above the cancellation rungs too, since a standby entry on a cancelled match
should read as a standby entry that ended, not as a cancellation of the viewer's booking.

---

## B3 — There is no state for the player who left, and it is the money-bearing one

**Defect** · States §0.2, §5 · Now §8.4 · Enrolled §3.2

States §0.2 promises a card:

> Early exits: you leave, or the match is cancelled. Both are terminal states with their own
> cards; **neither removes the card immediately, because the explanation is the point**.
>
> — States §0.2

No key exists for it in the thirty-three. Now §8.4 filters `myMatches` on `I hold a seat AND
I have not left` — so the card vanishes at exactly the moment the player has an open question
about money. And Enrolled §3.2 quietly assumes the card exists: *"Ola's card → the leaver's
view."*

This is the position with the most at stake in the whole model. A committed leaver's outcome
is not known when they leave: 100% if somebody pays full price, 50% if a rescue player takes
it, 0% if the match plays short, 0% if the checkpoint cancels at a rebooking club — and
States §8.5 says they were shown all four before leaving. The one screen that should track
which one landed does not render them at all.

**Fix**

Add the leaver group — `leftReversed` (pre-commitment, full refund in minutes),
`leftSearching` (outcome pending, all four named), `leftRefunded100`, `leftRefunded50`,
`leftForfeited` — and change the `myMatches` predicate to *I hold a seat, or I held one and
the outcome is not yet settled*, keeping the card for the same 24 hours. The alert strip's
bold money clause is already the right component for it.

---

## B4 — `start` is not immutable, so "the strip never reorders" is false

**Defect** · Enrolled §1.3 rule VI, §4.3, §5.2 inv. 10–11 · States §4.2, §6.4

The patch-not-list design — the sixth governing rule, invariants 10 and 11, and the test in
§4.3 — all rest on one claim: *"Cards are sorted by match start, which never changes."*

Rescue Stage 4 shifts the match by ±30, 60 or 90 minutes with unanimous consent. The states
document says so plainly and treats it as the interesting case:

> A successful Stage 4 moves the entire match half an hour later — a real, consequential
> change — and **the state does not move**. The match is still committed, still short, still
> searching. What changed is a field, not a state.
>
> — States §6.4

A field the sort key is derived from.

**Fix**

Add a fourth frame to the wire protocol — `{"t":"resort", listVersion, order:[matchId]}` — or
simply force a full `sync` on the one event that can change `start`. A consented time shift is
rare, is preceded by a notification the player answered, and is the one moment where a
reordering animation is *informative* rather than jarring. Either way the invariant needs
restating as *"only a consented time shift reorders, and it announces itself."*

---

## B5 — Hold-ladder rules 11 and 12 contradict each other

**Defect** · States §2.1 rules 11–12

Rule 11: *a club may set a maximum age for a soft hold* — which shortens a hold the ladder
would have kept. Rule 12: *a club may hold longer than the ladder promises, never shorter* —
*"the ladder is a floor."* Both are listed in §9.3 as specified but unimplemented, so this is
a live decision rather than a bug in shipped code.

**Fix**

State which governs what. The coherent reading is that Rule 12 constrains the *ladder's
thresholds* — a club cannot release earlier than T−12h or T−4h — while Rule 11 caps how long a
single hold may sit before being re-derived, which is an operational limit and not a
marketplace promise. If that is the intent, Rule 11's cap must never be allowed to release a
court before the ladder's own threshold, and that ordering needs a test.

---

## B6 — `formingLate`'s two context lines key on a fact that is not stored

**Note** · States §1.2, §5 `formingLate`

The variant is chosen by `created < commit` versus `created ≥ commit`, and the distinction is
a good one — *"saying 'the deadline has passed' would read as a warning about something the
player just did on purpose."* But `createdAt` does not appear in the §1.2 fact table.

**Fix**

Add it. It is also the only fact that tells you whether a match was created inside its own
window, which matters for the confirmation copy the last-seat payer sees.

---

## B7 — Two states claim to be the only one where a player loses money

**Note** · States §5 `cancelledCheckpoint`, `playedShort`

`cancelledCheckpoint` is described as *"the only outcome in the model where a player loses
money."* Two entries later, `playedShort` reads *"the leaver is refunded nothing and their
reliability takes the hit."* And `playedNoShow` makes a third.

**Fix**

Small, but the sentence is load-bearing — it justifies showing a leaver all four outcomes
rather than one number. Restate as *the only outcome where a player who stayed loses money*,
which is what makes it exceptional and is presumably what was meant.

---

## B8 — Two simultaneous leaves are not rare enough to leave unhandled

**Defect** · States §9.3

The document names this honestly — *"a second `vacated` overwrites the first"* — and defers
the decision. But with four seats, a four-hour rescue window and a group that often knows each
other, a second departure after the first is a normal Saturday, not an edge case. Overwriting
loses the first leaver's refund position entirely, which is the fact B3 says nothing is
currently rendering either.

**Fix**

Make it `vacancies: [{seat, player, at, outcome}]`. This is the same change B1 wants, and it
makes the recovery group's group facet honest — *"2 of 4 · two seats stay funded"* — instead
of silently reporting one vacancy while two exist. The cascade then runs one process per
vacancy, which is also what the rescue saga wants.

---
---

# PART C — THE TWO HOLES IN THE ENROLLED ARCHITECTURE

*The document's opening section is a well-argued takedown of a two-writer race. Both of these
are the same class of problem, one layer over.*

## C1 — The single-writer story protects the match and leaves the court unprotected

**Blocking** · Enrolled §0.3, §2.2 · States §3.3, §9.2

Enrolled §0.3 spends its strongest pages on the race between a clock threshold and a player
action writing to one match, and solves it correctly with one command handler and a version
column. But assigning a court is not a write to the match — it is an *allocation from club
inventory*:

> assign a court if we have none · write `courtId`, `protectedAt`, `holdKind` · **(or LOSE
> INVENTORY if none is free)**
>
> — States §3.3

Optimistic concurrency on match `m1` says nothing about match `m2`. Two matches at the same
club, same category and same hour, both crossing their ladder threshold in the same second,
both load the free-court list and both take the same court. States §9.2 lists precisely this
case as handled — *"Two open matches, same club, category and hour: each gets a genuinely
different court. `pickCourt` returns the first available one"* — with no mechanism behind it.
And `inventoryLost` is terminal and refunds everybody, so getting it wrong is not a display
bug.

**Fix**

The court hold is a reservation on a Courts or Bookings aggregate, not a field on the match.
The match handler acquires it and then records the identifier, which makes the exclusion a
uniqueness constraint on `(court, slot)` rather than a hope about read ordering. It also
settles a question the document leaves open: whether `inventoryLost` is a *query result*
(nothing was free) or a *race outcome* (something was free and somebody else took it), which
are different stories to tell the player. This is the strongest argument for modelling Courts
before Matches.

---

## C2 — "Any read is still correct" is false for exactly the four bad-news transitions

**Blocking** · Enrolled §1.3 rule IV, §5.1 · States §1.4 rungs 1–4, 12

Rule IV is named as the trust property, and §5.1 asserts that a downed timekeeper degrades to
*late, never wrong*:

> Timekeeper down → Cards stale until it returns. **Any read is still correct.**
>
> — Enrolled §5.1

It is not. Rungs 1–4 test `inventoryLost`, `clubCancelled`, `formCancelled` and
`checkpointCancelled`, and rung 12 tests `releasedAt`. Every one of those is a **stored fact
that only a writer produces**. With the timekeeper down through T−2h, a read of an incomplete
uncommitted match derives `protectedLate` — *"past the deadline, still free to leave"* — when
the truth is `cancelledIncomplete`. Same for a lapsed hold: `courtId` is still set, so a read
says `protectedCourt` while the ladder says no court is held.

Those are not *late*. They are *wrong*, and they are wrong in the reassuring direction, on the
four transitions the product exists to be trusted about.

**Fix**

Separate the derivation from the receipt. The *state* derives from `courtHold(m, now)` and the
checkpoint condition, both of which are pure functions of the record and the clock —
`cancelledIncomplete` is fully derivable as `now ≥ check ∧ committedAt = null ∧ ¬isFull`. The
stored flag records that the *side effects* — the refund, the court release, the notification
— completed. Then a downed timekeeper delays the money and never the truth, which is the
property the document claims and the one worth having.

---

## C3 — "Derive, never track" is stated absolutely over a list of seven written facts

**Note** · Enrolled §1.3 rule II, §2.1

`FactDelta` writes `setCommittedAt`, `assignCourt`, `releaseCourt`, `setHoldKind`,
`markInventoryLost`, `markFormCancelled` and `markCheckpointCancelled`. That is fine — but they
are three different kinds of thing sitting in one list, and after C2 the distinction becomes
load-bearing.

- **Allocations** — `courtId`. Cannot be derived; a court is a scarce resource, not a
  computation.
- **Irreversible crossings** — `committedAt`. Derivable once, then frozen, because the inputs
  stop supporting it. The document's reasoning here is exactly right.
- **Side-effect receipts** — the three cancellation flags. Derivable at any time; stored so the
  refund is not run twice.

**Fix**

Say which is which in §1.2. It is a documentation change that makes C2's fix obvious rather
than clever, and it is what the Matches ADR has to record anyway.

---
---

# PART D — THE RECOMMENDATION ENGINE'S COST MODEL

*The funnel, the lanes and the pull-not-push decision are right. The optimisation those
decisions were sized against is not.*

## D1 — The flyweight's premise does not hold against the engine that exists

**Blocking** · Rec §3.3, §6.2, §7.1

Rec §3.3 rests the whole scoring design on one claim, and calls it *"the 25× win"* and *"what
makes the feature viable at city scale"*:

> `seatTarget` is the whole cost — a 401-candidate grid over three pairings — and it depends
> only on the *seated levels and the sport*, not on who is asking.
>
> — Rec §3.3

Two halves, both wrong. `_seat_target` in `pairing/v1/engine.py` is closed-form, not a grid —
it inverts the team strength once per arrangement and takes the middle of three answers. And
`PairingAnalysis` as a whole is *player-relative*: the pairing engine reads
`snapshot.current_player` to put the asker in the open seat, so the forecast, the three splits
and their orientation all vary by viewer. A per-match cache of the analysis would be silently
wrong.

**What is actually shareable**

`_seat_target(snapshot, seated)` and `_target_band(snapshot, seated)` take the seated roster
only. Those two *are* player-independent and are the right flyweight — smaller than the
document imagines, and cheap enough that caching them may not pay.

**Where the cost actually is**

Not arithmetic. **Snapshot assembly** — gathering a rating per seated player, the club's travel
minutes and crowding, the seat share and payable, the phase, the hold and the cutoff, across
contexts that do not share a table. ADR-0026 names this cost in its own consequences: *"Call
sites are wordier. Assembling a `MatchSnapshot` means gathering ratings, prices, profile and
clock facts across contexts before either engine can be called at all."*

**Fix**

Cache the *player-independent snapshot fragment* per `matchId:recordVersion` — seats, club,
price, phase, hold, cutoff, plus the two targets — and batch-load ratings across the whole
candidate set in one query rather than per match. Then re-derive §6.2's budget table from a
measurement; the 500 µs cold figure and the 50 ms context build are both inherited from a
computation that is not happening. The version-keyed invalidation in §6.1 is correct and should
be kept exactly as written.

---

## D2 — `NoScheduleConflict` is the best addition in the document and is scoped too narrowly

**Note** · Rec §3.2, §5.2

Excluding a match that overlaps one the player is already enrolled in is correct and players
would notice its absence immediately. But a player's calendar is not only their enrolled
matches — a privately booked court is a booking they hold, and States §5 lists four private
states outside the enrolled lifecycle.

The same gap appears in tap-time verification (§5.2), which checks the *match* is still
joinable and not whether the *player* still can join it. A player who booked something
overlapping from another device between feed build and tap gets a clean join into a clash.

**Fix**

Resolve the conflict against the player's bookings, not their enrolled matches, and re-run the
rule inside `verifyJoinable`. Both are the same predicate called twice, which is the cheap
version of this.

---
---

# PART E — THE SCREEN ITSELF

*Smaller, but each one is a contradiction inside a document that is otherwise unusually
precise.*

## E1 — Parts 2 and 3 are CSS for the prototype, and the target is React Native

**Defect** · Now Parts 2–3, §10.1

`:root` custom properties, `.card` classes, `scroll-snap-type: x mandatory`,
`scroll-snap-stop: always`, `@media (prefers-reduced-motion)`, `::-webkit-scrollbar`,
`border-radius: 34px` on a 392×788 frame — none of these exist in the player app. It is Expo
with a typed theme object, a locked design system under ADR-0012, and reduced motion read
through `AccessibilityInfo`.

The acceptance gate *"Every colour, size, radius and spacing value matches Part 2"* is
therefore both unsatisfiable and, where satisfiable, in direct conflict with a locked system —
and the note that neither app is pixel-identical to its prototype already anticipated this.

**Fix**

Keep Parts 2–3 as a statement of *intent* — the colour semantics in §2.2, the two-family type
rule, the elevation refusal, the seven accessibility requirements — and re-express the values
against `frontend_player/src/shared/ui/theme.ts`. The rule worth carrying over verbatim is
§2.2: *a colour used for two things is a colour that means nothing.*

---

## E2 — The fit badge at 90+ breaks the document's own colour rule

**Note** · Now §2.2, §3.9

> Coral: *You. Your action. Your position.* … **Coral is never decorative. If coral appears on
> this screen and the player is not being pointed at a thing they own or an action they can
> take, that is a bug.**
>
> — Now §2.2

A computed recommendation score is neither a thing the player owns nor an action they can take.
§2.2 lists `.fit.hi` among coral's uses and then states the rule that excludes it.

**Fix**

This resolves together with A2. If the badge needs a second visual state, let coverage decide
it rather than the score — high fit *and* high coverage is the only combination that earns an
emphatic treatment, and it is genuinely rare, which is the argument §3.9 makes for coral in the
first place.

---

## E3 — The Now spec holds three incompatible positions on client-side derivation

**Defect** · Now §7.4, §7.5, §8.2, §8.3

- §7.4 — a tick recomputes *"the tag, the context, both facets, every line, the alert, the CTA
  label, the countdown, the glyph, the fit score, the price."*
- §8.2 — *"the client owns exactly three things: layout, the countdown tick, and the seat glyph
  geometry."*
- §7.5 — offline, *"times and deadlines still compute locally from the cached record and the
  device clock"*, while §8.3 says the device clock may never be used directly.

These cannot all be true. §7.4 requires the client to hold the state table; §8.2 forbids it.

**Fix**

A6's transition list settles all three at once. A tick recomputes nothing except *which
supplied transition is now current*; the offline case works because the transitions were
already handed over; and the countdown runs off `serverTime` plus elapsed monotonic time
exactly as §8.3 requires. Delete §7.4's list and replace it with the comparison.

---

## E4 — "You are 2nd on the standby list" is a precise number for an unobserved event

**Note** · Now §6.5, Part 6

The document is candid that the position is computed against a vacancy that has not happened,
ranks on level fit against a seat that does not exist yet, and *"can move without anybody doing
anything wrong."* A number that is precise, prominent, and free to change for reasons the
player cannot see is the same shape as the optimistic defaults ADR-0027 removed — a fabricated
observation wearing the clothes of a measurement.

Everything else about the section is right, including the 80 floor and the argument for why
waiting is a bigger ask than joining.

**Fix**

State the pool rather than the rank — *"you and five others are on standby"* — or say only what
is certain, which the next line already does well: *"if a seat frees the top candidates are
told at the same moment."* That sentence carries the whole mechanism without claiming a
position.

---
---

# WHAT HOLDS UP

*Checked deliberately and found sound. Several of these are decisions I would have expected to
argue with and did not.*

| # | Affirmed |
|---|---|
| 1 | Status before discovery, and refusing to let the player choose which mode they are in |
| 2 | The three-axis state model, and the argument that a five-state model collapses real states into lies |
| 3 | Rule B — the clock alone never commits anybody. This is the product |
| 4 | `committedAt` as the one persisted crossing, and precisely why it cannot be derived |
| 5 | The four load-bearing ladder orderings, each with its reason stated |
| 6 | One writer, optimistic concurrency over a lock, and the retry that re-evaluates rather than replays |
| 7 | The deterministic `EvaluateAt` key — at-least-once scheduling with no leader election |
| 8 | The schedule as a column, recomputed on every write, with a slow sweep as the safety net |
| 9 | Partitioning the projection by `playerId`, and saying it is not optional |
| 10 | Monotonic accept plus a version-carrying heartbeat — a dropped patch self-heals with no server-side tracking |
| 11 | Pull for the feed, push for the strip, and the fan-out argument that separates them |
| 12 | Cache the ranking, verify the joinability, and hand back alternatives already in memory |
| 13 | A lane is data, not a branch — which is exactly where ADR-0027 puts ranking policy |
| 14 | Refusing a learned ranker, and refusing to relax a criterion to fill a list |

---
---

# PART F — FIT FOR THE PROJECT, AND WHAT TO BUILD FIRST

This feature reaches across **Clubs, Courts, Bookings and Matches** — all four of which
`CONTEXT.md` Part 2 lists as intent and naming only, with no code, no events and no committed
terms. It also assumes payments and refunds, a ledger, notifications, waitlists, a rescue saga,
ladders and promotions, club cards, Player Score and the intent pool. None of those exist.
`frontend_player` has two features: auth and onboarding.

## What already fits, better than the documents realise

- **The timekeeper is the shape of `EventWorker`** — an embedded poller over an indexed column
  using `FOR UPDATE SKIP LOCKED`. Same pattern, same neighbourhood in
  `app/infrastructure/events/`. It should probably be the same poller with a second query
  rather than a second process.
- **The transactional outbox is built** (ADR-0003), so the fan-out in Enrolled §2.4 and §2.5 is
  wiring, not infrastructure.
- **The engines are done and fenced.** Pairing and Match Fit are complete, pure, mypy-strict,
  and tested against hand-built snapshots with no database — which is exactly what lets the
  feed be built before Matches exists.

## What is genuinely absent

**WebSockets.** Nothing in `backend/app/` speaks it, and ADR-0008 has the player app talking to
the API directly. That is new build — and by the enrolled document's own Rule IV it can be the
*last* thing built, not the sixth of ten. *The push is an optimisation; the read is the truth*
means the screen is correct without it, which de-risks the entire feature if the build order
honours it.

## One decision the documents pre-empt

Enrolled §6.2 declares the match *"a record with an outbox"* rather than event-sourced. That may
well be right — most of the model is derived, so there is little to source — but every existing
aggregate went the other way, and `CONTEXT.md` is explicit that the choice is *"a real decision
with real consequences — make it deliberately, per context, and write it down."*

## The order

| # | Deliverable | Why here |
|---|---|---|
| **1** | **The Matches aggregate ADR** | ADR-0026 was written to feed exactly this: *"the snapshot becomes the specification for the Matches aggregate."* States §1.2's fact table is the other half of the input. Settle event-sourced versus persisted-with-events here, and resolve C3's three kinds of stored fact while you are in it. |
| **2** | **Courts and the hold, before the match lifecycle** | C1 is unsolvable at the match layer, and `inventoryLost` is terminal. The reservation has to exist before the ladder can assign anything. |
| **3** | **The derivation kernel as a pure module** | The ladder, the twelve hold rules, the seven commitment rules and `nextWakeAt` — under the existing purity gates, taking `now` as an input, tested by scrubbing a demo week forwards and backwards. This is the cheapest and highest-value piece and it needs nothing else to exist. |
| **4** | **Command handler and timekeeper on the existing worker** | One writer, optimistic concurrency, deterministic idempotency key, `next_wake_at` as a column on the read model. |
| **5** | **The feed, pull-only** | No new infrastructure at all — the funnel, the lanes and the two engines that already exist. This is the one part shippable today against hand-built snapshots. |
| **6** | **Now, read-only over both** | The strip and the two lanes, refreshed on open and on pull. Correct, if not yet alive. |
| **7** | **Delivery last** | WebSockets, patches, the heartbeat. Everything above works without it, which is the whole point of Rule IV and the best reason to defer it. |

---

*21 findings · 14 affirmed · 4 documents · checked against 5 accepted ADRs and the shipped
engines.*
