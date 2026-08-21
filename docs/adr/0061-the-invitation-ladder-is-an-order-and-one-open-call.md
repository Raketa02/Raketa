# ADR-0061 — The invitation ladder is an order, and one open call replaces the exclusive offer

- **Status:** Accepted
- **Date:** 2026-08-21
- **Amends:** [ADR-0052](0052-a-vacancy-is-offered-not-announced.md). Its ordering principle,
  its channel rules and its screen rules stand. Its **two modes**, the **exclusive hold and
  its clocks**, the **three-offer cap**, the **twelve-hour backstop** and its
  **permission-timing rule** do not. Read 0052 first: it holds the reasoning these rules rest
  on, and in particular the reason the open-call wording is not optional.
- **Amended by:** [ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md) — the
  notification's wording becomes past tense (*"a padel seat **just opened**"*), *several offers
  dispatch as one notification* widens to **one live message per player**, and only a seat the
  player **asked for** may buzz. The ladder, the pool and the two dispatches are untouched.

## Context

[ADR-0052](0052-a-vacancy-is-offered-not-announced.md) settled that a vacancy is **offered**,
and in what order — *"standby first, ordered by fit within standby; then everyone else
eligible, ordered by fit"*. It did not settle who **"everyone else eligible"** is, and that set
is the difference between a rescue that fills the seat and one that spams the city.

Three things were found while answering it, and each moved the question.

**The ladder already exists, on a screen.** The v37 prototype's replacement-status view renders
a card titled *"Who is invited, in order"* with **seven** rungs, and the leaver's own timeline
shows *"18 compatible players notified"* two minutes after the seat reopens **at full price**.
So strangers were always in the pool, from the first minute, and the order was already drawn —
what was missing was a record saying what each rung means and which of them have any data
behind them.

**Two of those rungs are a feature this map ruled out of scope.** Rung 2, *players with
last-minute availability switched on*, is the opt-in alerts feature. The prototype's `avail`
screen shows what it actually is: **standing rules that auto-join waitlists** — *"you are on
every list that matches… this put you on 6 waitlists this week without you opening the app."*
It is not a second notification channel and not a second consent path; it is a machine that
feeds rung 1.

**`3.1` §4.2 has a five-stage cascade with a consent gate**, and 0052's flat two-group list
had quietly stepped over it. Stage 3 *widens the level band* and requires **unanimous consent
from the players who stayed** — *"the engine may try anything computable; it may never decide
anything a player did not consent to."*

Underneath all three sits [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md):
candidate generation excludes on **facts**, never on preferences; *"distance, price and level
are never exclusions"*.

## Decision

**We will treat the ladder as an order over one eligible pool, and — at the volume this
product launches at — tell everyone in that pool about the seat in two steps rather than
walking seven.**

### The pool, and its wall

Eligibility is a **fact filter**, unchanged in kind from the feed's: sport, a free seat, the
join cutoff, live inventory, a calendar conflict — plus one addition and one wall.

- **A player is never offered a seat in a sport they hold no rating in.** The rule is *a
  rating exists at that sport*, not *they answered that questionnaire at onboarding*; the two
  diverge the moment a player adds a sport or is rated by playing. This is legal under ADR-0027
  because it excludes on a **missing fact**, not on a low score: the fit engine imputes a level
  where no rating exists, so without this rule a badminton-only player is "eligible" for every
  squash cancellation in the city at an invented level.
- **The match's level band is the wall.** *"Everyone else eligible"* means everyone inside the
  band the players who stayed signed up for. Reaching outside it remains `3.1` Stage 3 and
  remains **unanimous-consent**. The prototype's automatic *"wave 3 · wider level and
  distance"* is superseded by that gate.

**Above 24 h to the match, a fit floor of 70; inside 24 h, no floor.** The floor keys on the
clock directly, not on a mode name. *We suggest matches over 70* is a promise about
suggestions; *a seat just opened at half price* is a different sentence, and inside a day the
alternative to telling a 55 is a dead seat.

### The seven rungs

Fit-ordered within a rung. Rungs with no source ship **dark** — declared, empty, and plugged in
when the feature that feeds them exists.

| # | Rung | v1 |
|---|---|---|
| 1 | Standby — asked for **this** match | **Ships** |
| 2 | Standing rules / last-minute availability switched on | **Dark** — its own effort; when built it *auto-joins standby*, so it feeds rung 1 rather than bypassing it |
| 3 | Asked for the seat before — offered an earlier vacancy on this match and did not get it | **Ships** |
| 4 | Viewed or followed the match | **Ships as viewed** (48 h, the *Recently viewed* signal). *Follow* does not exist |
| 5 | Compatible players who use this club often | **Ships** — play history at that club |
| 6 | Nearby **reliable** players inside the level range | **Ships degraded** — the level band only. *Reliable* is recorded and unused (below); *nearby* has no source (below) |
| 7 | Marked available at this hour | **Dark** — the same effort as rung 2 |

The order is the expensive part and it is written once, now. The sources are independent
features that plug into it, and adding one later is a re-sort rather than a new stage.

**Rung 6 degrading to "everyone else in the band" is the ladder behaving correctly**, not a
gap: it lands exactly on ADR-0052's *"then everyone else eligible"*.

### Two dispatches, not seven, and not one

- **Rung 1 is told immediately. Rungs 2–7 are told together ten minutes later.** An empty rung
  costs nothing — `3.1`'s *"a stage with no candidate is skipped instantly"* holds.
- Beyond that the ladder is **ordering**: it ranks the list, and it drives the leaver's *"who
  is invited, in order"* card.

Seven staged rungs is what this product becomes when volume earns it; adding delays to an
ordering that already exists is the whole migration. Today each rung below the first holds two
or three people, so six delays buy nothing but a seat still walking the ladder an hour later.

**One head start is not an optimisation, it is the standby promise.** Told in the same instant
as strangers with the same card, joining a waitlist buys **nothing** — the exact failure 0052
named when it refused pure fit ranking.

### One mode: the open call

**The exclusive offer does not ship.** With it go the one-hour hold, the cap of three held
offers, the twelve-hour backstop, and the *"a seat is being offered to you"* wording. Every one
of those exists to make one-at-a-time safe.

The product owner's hard constraint — **a seat that is gone must never be presented as an
exceptional card** — is kept by the **wording**, which is what it was always about: everyone is
told in the open-call voice, *a seat just opened, first to take it*, so no card ever claimed to
be exclusive and no card has to be retracted into a lie.

What actually decides it is **where the state lives**. One-at-a-time is a running process per
*candidate*: a hold, a clock each, a cap to enforce, a backstop for a phone that is off.
All-at-once puts every piece of state on the **vacancy** — an eligible set computed once, two
dispatch jobs, first-to-accept wins. Two timers per vacancy instead of a timer per person, and
nothing to reconcile when the seat fills mid-walk.

Two of 0052's rules are **not** exclusive-mode machinery and survive untouched: **delivery is
held to 08:00 local** unless the match starts inside twelve hours, and **several offers
dispatch as one notification**.

**Both price phases use this same ladder** — the full-price search from the moment of the
vacancy, and the 50 % rescue from the rescue deadline. `3.1`'s rule that the window gates *the
discount, not the notice* is what lets a stranger be told on Sunday about a Tuesday seat.

### Accepting, and the only exclusivity left

First to accept wins, and **accepting locks the seat for a short payment window** — the
prototype's five minutes, carried as a placeholder the money chain owns. **The card disappears
for everyone else for the duration, and returns if the payment lapses.** During that window the
seat is gone, provisionally, and the constraint says a gone seat must not look available. A
*"someone is paying for this"* state would be a third card state for a five-minute condition;
letting a second player tap and then telling them is the exceptional-card lie in miniature.

### The person on the other end

- **Permission is explained during onboarding, and the OS prompt is spent only on a yes.** The
  onboarding screen carries *Turn on* / *Not now*; only *Turn on* fires the system dialog, and
  *Not now* is asked again at the first standby join. iOS grants exactly one prompt per install,
  and an onboarding ask reaches everyone at the moment they have least reason to say yes. This
  amends 0052's *in context, not at launch* — with rungs 4–7 in the pool, most recipients never
  join a standby list, so an ask that only fires there leaves most of the ladder unreachable.
- **Refusing permission costs a player only exclusive offers** — which no longer exist. 0052's
  *"no offer is made to that player at all"* was reasoned entirely about holds. A quiet player
  still gets the card on Now.
- **One message, an opening clause per rung group** — *the seat you asked about* · *a match you
  looked at* · *a seat near you*. The lock screen carries **sport, time and travel time, never
  the venue**: *"A padel seat is free — Tue 19:00, 20 min away."* Travel time is what makes the
  line actionable for somebody who does not know the match; the venue is the part that is
  genuinely sensitive read over a shoulder.
- **No frequency cap in v1.** An eligible player who has said yes may be told as often as seats
  free. The cap is the first thing to add when a real player is reached daily.
- **An ignored offer is recorded and used for nothing.** The reliability record that would hold
  it ships dark, and a penalty invented inside a cascade would be invisible and unappealable —
  the objection that killed the repeat-opponent rating penalty.

## Consequences

**Easier**

- **The cascade is two queries and two jobs.** No per-candidate process, no hold to expire, no
  reconciliation when a seat fills mid-walk.
- **The ladder is cheap to grow.** Every rung's *order* is fixed now; a rung turns on when its
  feature ships, and staging turns on by adding delays.
- **The alerts feature got smaller before it was built.** Because a standing rule auto-joins
  waitlists, it needs no second consent path and no second place on the screen.

**Harder**

- **Everyone eligible is told about a seat only one of them gets.** Four seats and forty
  eligible players means thirty-nine people learn about a seat they will not get, every time —
  the "many disappointed" case 0052 spent its waves to make rare. It is affordable at launch
  volume and it is the first thing to revisit; the trigger is a real player being disappointed
  weekly.
- **[Raketa02/Raketa#28](https://github.com/Raketa02/Raketa/issues/28) got harder.** A filled
  seat now leaves **N−1** stale notifications instead of one, so whatever withdrawal mechanism
  it picks runs at fan-out.
- **The ladder needs a player location and there is none.** *Nearby*, a travel range, and the
  *"20 min away"* line all want a home location the product does not have. Rung 6 ships without
  it, which means the tail rung is everyone in the band **anywhere** — acceptable in one city,
  not for long.
- **`3.1`'s stage table is now two documents.** Its Stages 1–2 are this record's two dispatches;
  its Stages 3–5 (widen, shift, merge) survive untouched as the consent-gated things they always
  were.
- **A standby player's head start is ten minutes, and nothing shows it.** Somebody will feel
  they gained nothing, and the honest answer is that ten minutes is what the promise is worth at
  this volume.

**Neutral**

- The 50 % rescue price, the invisibility of a Rescue Seat, and the join cutoff that ends the
  search are untouched. This record governs **who is told, in what order, and by what
  machinery** — never what the seat costs.
