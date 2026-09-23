# ADR-0094 — Play intent is declared per sport, in its own aggregate, and edited where the player searches

- **Status:** Accepted — **the Amendment's *it reads the declaration and is refused with
  `play_intent_not_declared`* superseded 2026-09-14 by [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)** §2: the deck reads no
  declaration and deals under one ruler. `DECK` stays in the closed five for the events that
  carry it.
- **Date:** 2026-08-26

> **Overrules two recommendations in the matchmaking input document**
> ([`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md)):
> §6.2's *"the profile carries a `Mapping[Sport, PlayIntent]`"* and §23 Q16's *"it is the
> first per-sport fact on `PlayerProfile`"*. §6.1, §6.3, §6.4 and §6.5 transfer unchanged.
> Recorded in that document's [conflict table](../specs/matchmaking/README.md#conflicts-with-an-accepted-adr).

> **Amended 2026-08-29 by [The prompt that asks again after you said no](https://github.com/Raketa02/Raketa/issues/237):
> the suppression keeps its window, its scope and its refusal of an event, and stops living in
> Redis.** The Decision below says a decline is *"held in the sweeper's Redis with a TTL"*. That
> one clause becomes **a durable row in `matchmaking`, with the live suppression derived from
> it** — [ADR-0128](0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)'s shape, on
> ADR-0128's argument: `prompts.py`'s own two constants are falsified by *take-up rate* and
> *acceptance rate on the offer*, and a lapsed TTL leaves no trace the player was ever asked.
> Everything else stands **literally**: *for that sport*, *30 days*, and *declining a prompt is
> not a domain fact and earns no event* — a pass earns no event either, and is still a row.
> The amendment also **discharges one of this record's own stated costs**: *"two things now have
> to agree about the same suppression window, and a change to one that forgets the other
> produces either nagging or silence."* There is now one store and one filter, read where every
> prompt already converges, so the two halves have no way to disagree.

## Context

The matchmaking engine's strongest term per unit of cost — **Intent alignment** — reads a
field the platform does not store. Today, choosing *Competitive* or *For fun* changes only
which weights *your own* search uses: it reshuffles the same pool and never asks whether the
other person wants the same kind of evening. The failure shows up on court, and neither
player comes back.

Three forces shape where the fix can go, and the third was not visible when the input
document proposed its answer.

**1. The founding rule.** *A level is proved, never declared* ([`CONTEXT.md`](../../CONTEXT.md)).
Handing players a self-declared field one screen after refusing them a self-declared level
needs an argument, and there is a clean one (§6.1): a level is a claim about a fact, reality
checks it every Saturday, and misdeclaring it **pays** — a sandbagger farms wins against
people promised a fair game. Intent is a preference, there is no true answer to check it
against, and misdeclaring it costs only the declarer an evening. A field that cannot be gamed
to anyone else's cost is safe to hand over.

**2. `PlayerProfile` is deliberately not per sport.** ADR-0089 made it the first aggregate in
the racket-sport domain without a sport dimension, and its docstring spends a paragraph
resisting the pull toward one. A `Mapping[Sport, PlayIntent]` field would be the first
per-sport fact on it — a precedent, set to save one aggregate.

**3. The ordering constraint, which decides it.** Onboarding is two parts (ADR-0090). Part 1
rates **up to four sports** — `onboardingPass` holds a `queue: readonly Sport[]` — and part 2
is **one** client-held draft committed in a single idempotent `POST` at the end. A profile
therefore does not exist until every rating already does. Put intent on the profile and it
can only be asked in part 2, which permanently welds *"the sports I have an intent for"* to
*"the sports I had rated the day I finished onboarding"*. There is no in-app route to rate a
further sport today (`entryDecision` has four destinations and none of them is one), and no
profile-edit endpoint exists yet — `profile_routes.py` exposes exactly one `POST`. The
coverage hole would have no floor and no lid.

### Alternatives considered

- **A field on `PlayerProfile`, asked as a seventh social step** — §6.2's proposal. Cheapest
  to build and it sets the precedent ADR-0089 resisted, in exchange for the coverage hole
  above. A sport rated after onboarding could never acquire an intent.
- **No declaration at all: the live *Competitive / For fun* toggle is the intent.** Attractive
  — it can never go stale, and it deletes the drift detector, the prompt and a sweeper loop.
  It cannot work, because matching is one live person against **N absent people**: a candidate
  in a shortlist is not searching and has no live toggle. The only things to compare a
  searcher's mode against would be the candidate's *last* search mode — behavioural inference,
  which §23 Q14 rules out permanently — or a live queue, which is a different product and
  returns nothing in a new city. It also makes `NO_PREFERENCE` unreachable (there is no third
  search tab), destroys *"just for this search"*, and leaves every player who has not yet
  searched unreadable on day one, which is the exact hole §6 exists to close. **Its one true
  insight is kept**: a settings screen is the wrong place to change intent.
- **One intent stream per player, folding to a `Mapping[Sport, PlayIntent]`.** Off the
  profile, fewer streams, one read gets all four sports. Rejected because it puts two sports'
  declarations on one stream — contending on one version, and giving *something* in the system
  a reason to hold two sports at once.
- **The rating context.** The moment coincides — intent is declared at a rating run's tail —
  and `SkillRating` is already keyed `(player, sport)` with a deterministic id. Rejected
  because that context's founding rule is *proved, never declared*, and putting the platform's
  one declared per-sport fact inside it invites exactly the conflation §6.1 exists to prevent.

## Decision

We will model **Play intent** as a declared, per-sport preference in its **own event-sourced
aggregate**, inside the **Player profile** context.

- **`PlayIntent`** is a closed enum of three values — `COMPETITIVE`, `FOR_FUN`,
  `NO_PREFERENCE` — with **no nullable alternative on the wire**. `NO_PREFERENCE` is an
  explicit answer; the matcher cannot otherwise distinguish *"either suits me"* from *"I never
  opened that screen"*, and those are different facts. Nobody is ever backfilled to it.
- **`PlayIntentDeclaration`** is the aggregate, one stream per `(player, sport)`, its id a
  deterministic `uuid5` from that pair in the shape `skill_rating_id` established
  ([ADR-0019](0019-deterministic-assessment-stream-ids.md),
  `app/modules/rating/domain/ids.py`). *Levels never transfer between sports, and intent does
  not either* becomes structural: **no object in the system holds two sports' intent at once,
  so there is nothing to transfer.**
- **It is declared at the tail of every rating run that produced a rating** — required, no
  skip, all three values offered. A run that was abandoned asks nothing: a rating is what makes
  a player matchable in a sport, and without one there is nothing to be matchable *for*. The
  coverage rule is therefore exactly *you have an intent for every sport you have a level in*.
- **One event: `PlayIntentDeclared` — `player_profile.play_intent_declared` / v1**, carrying
  the sport, the value and a **`surface` code** (`RATING_TAIL` / `SEARCH_SWITCH` /
  `DRIFT_PROMPT` / `PROFILE_SCREEN`), following `ConsentSurface`'s precedent in the same
  context. It obeys the **preference** rule, not the consent rule: **a transition to the value
  already held records nothing.** Intent is a preference and §6.1's whole argument is that it
  is not a consent — there is no wording to evidence it against, which is precisely why
  `ProposalsOptInAnswered` is that aggregate's exception and this is not.
- **The write path is `PUT /api/v1/play-intents/{sport}`, unkeyed.** The Profile commit needs
  an idempotency key because it *creates* an aggregate out of six answers and a duplicate
  would be a second profile. This creates nothing duplicable: the resource is one player's
  intent in one sport, the same request twice lands the same state, and the no-op rule means
  the second appends nothing. Concurrency is the stream version, as everywhere else.
- **The search screen is the edit surface, not a settings screen.** Switching the
  *Competitive / For fun* toggle away from the declared value offers, inline and at that
  moment, *make this my intent for this sport* or *just for tonight*. Declining suppresses the
  offer for that sport for **30 days**, held in the sweeper's Redis with a TTL — declining a
  prompt is not a domain fact and earns no event. §14.5's daily drift loop stays at **N = 5
  consecutive disagreeing searches**, demoted from the mechanism to the **backstop** for the
  sticky-tab case: switch once, decline once, then search in the new mode for a month with no
  further switch to hang an offer on.
- **The matcher never reads drift and never writes a declaration.** This is the one place the
  platform watches, notices, and deliberately declines to act. It asks, and it accepts whatever
  answer comes back.
- **A search requires a Skill rating in that sport**, and a searcher with a rating but no
  declaration is gated by a **one-tap interstitial**. This is permanent, not a migration path:
  it is what makes the coverage rule true rather than merely intended, and it closes a sport
  rated before this shipped, a restored account, and a bug in the tail with one screen. It
  guarantees every **searcher** has declared; it does **not** guarantee every **candidate**
  has, so `NoEvidence` and the stand-down renormalisation stay a common path.
- **`SearchMode` and `PlayIntent` are two distinct types** and never one. Mode is the search's
  setting — which tab you are on, right now, two values. Intent is the player's declaration —
  three values. The arities differ, so they cannot be unified even by someone hunting
  duplication, and §5's collision becomes a type error rather than a paragraph. The
  Intent alignment term's signature is `(my_mode: SearchMode, their_intent: PlayIntent)` and
  **receives no tags at all**; a structural test asserts `app/engines/matchfit/` does not
  import the social tag vocabulary, in the shape of the existing tripwire in
  `tests/unit/test_social_tag_vocabulary.py`. Reading `HERE_TO_COMPETE` as intent would
  double-count six strings across three terms; a tag is *why you are here at all*, intent is
  *what tonight's game is*, and somebody tagged `HERE_TO_COMPETE` who declared `FOR_FUN` wants
  a hard-fought friendly.
- **Intent crosses the wire as its machine code and is shown on a candidate's card.** It is the
  player's own word about themselves, carries no protected attribute, and is the single fact
  that makes a low Fit score legible rather than insulting. Per
  [ADR-0022](0022-kernel-negative-space-and-constant-homes.md) the backend emits `FOR_FUN` and
  the client renders the sentence; the engine never emits a string a human reads.
- **The alignment table is settled here**, as §6.4 proposes it — searcher's live mode against
  the candidate's declaration, the searcher's own declaration not consulted:

  | Searching | They declared `COMPETITIVE` | `FOR_FUN` | `NO_PREFERENCE` |
  | --- | --- | --- | --- |
  | **Competitive** | 1.00 | **0.00** + `intent_opposed` modifier | 0.85 |
  | **For fun** | 0.35 | 1.00 | 0.85 |

  It is 2 × 3 *because* mode has two values and intent has three, and that shape is the
  argument. These six cells are the term's own lookup and belong with the term, not with the
  eight cross-term weights. The asymmetry is deliberate: a social player in a competitive game
  is mildly bored; a competitive player in a game where nobody keeps score has been cheated of
  the only thing they came for. It is a **weight, not a gate** — but **intent alignment is
  never relaxed** on any rung of the ladder.
- **The declared-versus-proved argument is discharged in the interface, in two places** — on
  the intent step, and wherever the app refuses a self-declared level. The wording is the
  client's (ADR-0022); that both exist is a requirement on the spec. One without the other is
  what makes a product look arbitrary: the app already tells players it will not take their
  word for a level, then takes their word for something else one screen later.

## Consequences

**Easier**

- Intent exists for every sport a player is rated in, forever, including sports rated years
  after onboarding — the coverage hole §6.2 would have created has no way to open.
- `PlayerProfile` keeps the property ADR-0089 argued for. Nothing about it becomes per sport,
  and the next person tempted to add a sport dimension finds no precedent to cite.
- Nobody visits a settings screen to change their mind. The control that expresses *what I want
  tonight* is the control that offers to update *what I am*, at the moment the player has
  already shown which one they meant.
- The mode/intent collision — the single most likely bug in the engine — is unrepresentable
  rather than documented.

**Harder**

- **A second aggregate in the Player profile context**, with its own repository, its own
  deterministic id function and its own registration. Bought deliberately, and it is the price
  of the coverage rule.
- **The rating tail gains a required screen**, so part 1's exit is no longer purely the rating
  result. A player rating four sports answers four times — one tap each, but four.
- **A drift mechanism with two halves.** The inline offer catches drift at the switch; the
  daily loop catches the sticky tab. Two things now have to agree about the same suppression
  window, and a change to one that forgets the other produces either nagging or silence.
- **`surface` is client-asserted** and a client could lie about it. Accepted: it is the only
  party that knows which screen it was, and nothing load-bearing reads it.
- **An undeclared candidate is normal, not exceptional.** Every player between *rated* and
  *first search in that sport* is one, so the `NoEvidence` stand-down and weight
  renormalisation are on the common path and need a test, not a comment.

**Neutral**

- §6.2's durable event name survives intact. The correction is about which aggregate, not which
  context, so the one artifact the document fixed permanently is unchanged.
- The searcher's own declaration is never read when they search, which was already §6.4's rule
  and is unchanged here. What is new is only where the declaration is *edited*.
- Nothing here is event-sourced that was not already: the aggregate joins the same store, the
  same catalog and the same dispatcher as every other.

## Amendment — 2026-09-01: the deck is a surface, and the set widens rather than renaming

Building the deck ([#270](https://github.com/Raketa02/Raketa/issues/270)) gave the `surface`
code a **second Play screen** that the closed four could not name. `POST /api/v1/deck` carries
no mode in either direction, so it reads the declaration and is refused with
`play_intent_not_declared` exactly as a search is; its sport chips land on rated, undeclared
sports exactly as the search screen's do; and it therefore draws this record's one-tap
interstitial. That made the interstitial a component with two callers, and it shipped reporting
`SEARCH_SWITCH` from both — a small untruth in the one field whose entire job is to say which
screen it was, introduced deliberately and filed as
[#280](https://github.com/Raketa02/Raketa/issues/280) rather than left to be noticed.

**`PlayIntentSurface` gains `DECK` and is now a closed five.** The Decision's event bullet
above still spells the closed four, and is left standing: this record is immutable once
accepted, so the list is read through this section rather than corrected in place.

The alternative argued was a **rename**: `SEARCH_SWITCH` becomes `PLAY_SWITCH`, one value
honestly true of both Play surfaces rather than two that each name one. It is the better name and it lost anyway, on a
cost this record's own design imposes. The code is stored **verbatim** on `PlayIntentDeclared`
and read back through `PlayIntentSurface(event.surface)` at replay, so renaming it is an event
migration — a codec mapping that must outlive the rename, carried for ever — bought on a field
that by this record's own Consequences *nothing load-bearing reads*. A widening costs one enum
member and leaves every code already in a stream meaning exactly what it meant when it was
written. Where the price of honesty is a migration on a field nothing branches on, the additive
answer wins.

Nothing else moves, and **nothing beyond this case is decided.** `surface` stays
client-asserted and stays safe to be, for the reason given above: the client is the only party
that knows which screen it was, and nothing branches on the answer. What carries forward is the
**cost, not a rule**: a member already written into a stream is expensive to respell and cheap
to sit beside, so the additive answer starts ahead. A future rename is not forbidden here — it
is the option that has to show what it buys against that cost, which is exactly what this one
was asked to do and could not.

**The cost is that the set is no longer a partition anybody can hold in their head as *the
screens that matter analytically*.** Five is still small, but the argument that four buckets
were enough — *a sport switch on a Play screen is one bucket* — was real and is being traded
away for a field that reports what actually happened. If the set reaches a size where nobody
reads it, that is the falsifier: this field is analytics, and analytics nobody consults is a
write with no reader.

**What would reverse it.** A reader of `surface` who genuinely wants the two Play surfaces
totalled and never split. That would be an argument for one value across both — and it would be
answered with a `GROUP BY` over two codes, not by narrowing the vocabulary back.
