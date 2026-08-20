# ADR-0051 — Now is ordered, never drawn: the list-builder's contract

- **Status:** Accepted
- **Date:** 2026-08-20

## Context

The layer that turns a city full of matches into one player's screen has never been written.
`backend/app/engines/matchmaking.py` is the snapshot input vocabulary and holds no `sorted`, no
`key=` and no filter; [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md)
§81–85 assigns lanes, floors, diversity, freshness, exploration and the cut to *"a policy object
in the calling module's application layer"*, and names that layer the one place permitted to
*"read configuration, run experiments and draw randomness, because it is not an engine and makes
no claim to reproducibility."*

That licence to draw randomness was granted for a specific job: **exploration**, deliberately
showing a player matches the score does not favour, so that a new club's matches are seen at all
rather than dying unseen for want of history. ADR-0027 accepted its cost openly —
*"some of those will be worse experiences. That cost is real and is being paid to keep supply
alive."*

[ADR-0050](0050-now-below-the-strip-is-shelves.md) removes the need for it. A **New clubs** shelf
and a **New on Raketa** shelf do exploration's job **editorially and legibly**: a match from
Podgórze is on the screen because Podgórze is new, which is a sentence, rather than because a
coin came up heads, which is not.

Three further things were left open and are settled here.

- **The open list has no floor anywhere**, while [ADR-0037](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)
  clamps the badge to 20–99 at display time and records that the clamp *"is only defensible while
  the ranking layer keeps a 12 off the screen, which is a floor not yet decided."*
- **The `−8` "the same four again" penalty was re-homed here** as a variety cap on how many cards
  share the viewer's regular group — and the field it would read, `PlayHistory.played_recently`,
  **ships dark**: absent from every snapshot today, which is why the `familiarity` term is
  excluded rather than guessed.
- **`FEED_ORDER`** — `[desc(fit), asc(start), asc(dist), asc(id)]` — is specified as a total
  order whose fourth key *"is not decoration"*, but nothing says whether it survives once
  diversity and exploration are applied over it.

## Decision

**We will make every card's presence on Now explainable in one sentence, and we will pay for that
by giving up randomness.**

- **Nothing on Now is random.** Exploration is dropped. Discovery is a shelf with a title, and
  *"why am I seeing this?"* always has a plain answer that does not require reading a seed.
  ADR-0027's licence stands unexercised rather than revoked: the ranking layer may still draw
  randomness the day an experiment needs it, and today none does.
- **Because nothing is random, nothing extra is recorded.** No per-composition seed, no
  ranked-versus-explored flag, no stored draw. A support agent reconstructs what a player saw
  from the shelf titles and the policy version, and the materialisation cost of replay is not
  paid for a capability nothing needs.
- **The order is strict, then adjusted by named passes, in a fixed sequence.** Per shelf:
  retrieve → eligibility → score → floor → **sort by `FEED_ORDER`** → diversity → cap → tail
  card; then compose: shelf order, the repeat guard, emphasis. **`FEED_ORDER` survives as the
  total base order**, not as a tie-break underneath other mechanisms, so the base order is always
  recoverable and each pass is a named delta from it. *"Why is this card third?"* is answerable —
  *"second on fit; the same-club rule moved it down one"* — and folding any of it into the score
  is refused for the reason `4` §3.4 already gave: an 84 would stop meaning *this match fits you
  84*.
- **The open shelf's floor is 70.** It is a quality bar, chosen by the product owner, and it is
  affordable only because a shelf that cannot fill is absent rather than empty
  ([ADR-0050](0050-now-below-the-strip-is-shelves.md)) — which is also what discharges ADR-0037's
  open worry: a true 12 can no longer reach the screen, so the display clamp never prints a
  number that is not the match's. **The waitlist shelf keeps 80. *Recently viewed* has no floor
  at all**, because it makes no claim — it says *you looked at this*, and a 41 with its badge
  printed is exactly what reminds the player why they backed out.
- **Eligibility is per shelf, evaluated exhaustively and never short-circuited**, so the
  exclusion histogram is complete. Both match shelves run `NotAlreadyMine`, `StartsInFuture`,
  `BeforeJoinCutoff`, `NotCancelled`, `SportMatchesFilter`, `NoScheduleConflict`, `NotSuppressed`
  and **`NotOnStandby`**; the seat rule is the one that inverts — `HasFreeSeat` open, `IsFull`
  waitlist. **`WithinTravelCeiling` is in neither**: distance, price and level are never
  exclusions, and a match removed before scoring cannot be graded by the travel term that exists
  to grade it. `!m.forced` is not a rule — `forced` is the prototype's demo-gallery hatch, marked
  *"must not survive"*.
  - **`NotOnStandby` applies to both shelves.** When a seat frees on a match the viewer is
    waiting for, they are offered it directly ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md));
    re-offering it in the suggestion list as though it were news is the app forgetting they asked.
  - **`BeforeJoinCutoff` binds the waitlist shelf too.** If a seat freeing at 18:50 cannot be
    taken because the club stopped accepting joins at 18:30, offering the match to wait on is a
    promise of a game already known to be unkeepable.
- **The variety rule is not built.** The regular-group cap has no input — `played_recently` ships
  dark — so it is left out rather than written dormant, and returns as its own decision when play
  history exists. The **same-club-same-hour** cap survives and is fixed here: a diversity pass may
  **reorder**, and may **never** return fewer cards than supply allows. `4` §3.4's implementation
  does return fewer, silently, which is a defect and not a policy.
- **At most one card on the whole screen is emphatic**, unchanged from ADR-0037 — not one per
  shelf. Emphasis means *drop what you are doing*, and five of those is none of them. When more
  than one card clears fit ≥ 90 · coverage ≥ 80 % · a seat open, **the emphatic one is the first
  in the final composed order** — read off the composed screen rather than recomputed from
  scores, the identical argument [ADR-0032](0032-order-is-a-property-of-the-composed-screen.md)
  made for order. **An offer on the screen silences the badge entirely**
  ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md)): two elements claiming to be the most
  important thing is resolved by the player trusting neither.

### The shelves that are not matches

- ***New on Raketa*** shows **people**: photo, name and Level. A player with no photo shows the
  first two letters of their name. **The Level is shown whether or not they have played** — it is
  public by design and has to be, or nobody could judge a match — but a player whose rating is
  still questionnaire-derived carries **a quiet marker, not a second number**. Onboarding cannot
  produce confidence above 30 %, and a 3,2 from six questions is visually identical to a 3,4 from
  eleven matches; the marker is the app being accurate about itself, and it costs nothing on the
  card, where Confidence as a printed percentage would be the second gauge ADR-0037 already
  refused.
  - Ordered by **closeness to the viewer's own Level**, not descending by Level. Descending makes
    the shelf a leaderboard — it tells every new player where they rank on the home screen of
    every stranger in the city — and puts the players the viewer can least enjoy a game with at
    the front.
  - **The card is inert in v1 and is styled so**: flat, no press feedback, no chevron. A profile
    screen and an invite flow are future efforts, and a first draft of either made under this
    ticket is the draft the real effort would have to argue with.
  - **Appearing is on by default with a switch to leave.** Level visibility is not the question —
    it is already public. Being *shown to strangers by photograph on their home screen* is, and a
    default that is cheap to set now is expensive to change after ten thousand people have joined
    under it.
- ***New clubs*** shows **clubs**. **Tapping opens Find, pre-filtered to that club** — no new
  screen, nothing built, and when the club detail screen lands the tap target changes and the
  shelf does not. A card that is inert with no plan behind it is a dead tap; this one keeps its
  promise today with what exists.

## Consequences

**Easier**

- Every card's presence is explainable from its shelf title, so support answers *"why did the app
  show me this?"* without instrumentation, and the storage question disappears with the
  randomness that raised it.
- Two identical requests over identical facts produce an identical screen, because `FEED_ORDER`'s
  fourth key is total and no pass above it draws.
- The floors are one number per shelf in a policy object, tunable without a client release, and
  *"does the policy starve the tail?"* stays the property test over the ranker alone that
  ADR-0027 promised.

**Harder**

- **Supply for a new club is now an editorial problem, not a statistical one.** If nobody swipes
  to the *New clubs* shelf, its matches die exactly as they would have without exploration — and
  unlike exploration, a shelf nobody reaches produces no measurement saying so.
- **The 70 floor is a product judgement with no measurement behind it.** It will hide matches
  that would have been joined, and because those matches were never shown, nothing will ever
  report how many.
- **The variety rule is a known gap, not a solved problem.** Until play history exists, a player
  whose regular group is active can get a screen that is three views of the same four people.
- **Dropping exploration is a decision that gets harder to revisit**, because the day somebody
  wants to A/B a ranking change, the recording that would have made it measurable was never
  built and the first experiment pays for it.
- **Two shelves make the ranking layer responsible for people and clubs**, which is a second and
  a third retrieval path in a component that was going to have one.

**Neutral**

- No line of `backend/app/engines/` changes. Floors, caps, eligibility, ordering, emphasis and
  shelf membership are all ranking-layer policy.
