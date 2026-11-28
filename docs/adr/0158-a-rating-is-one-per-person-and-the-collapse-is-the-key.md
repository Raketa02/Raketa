# ADR-0158 — A rating is one per person, the collapse is the key, and the matcher never reads it

- **Status:** Accepted
- **Date:** 2026-09-08
- **§6's last sentence and the 2026-09-08 band amendment amended by [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §5** — the
  published figure and its count cross to the subject too, and `sportsmanship_band` retires. The
  subtraction §6 names is accepted, and written beside the reversal.

## Context

`the-decisions.md` §5 settles a whole new bounded context, and
[#373](https://github.com/Rakieta02/Rakieta/issues/373) prices it: **sportsmanship is the
first part of the player record that stores anything.** Every other zone on that sheet
derives — the metered rows are folds over `games` and `challenges`, opponent variety is a
walk over a history that already exists, the skill card is a rating already recorded. This
one has an input surface, and an input surface needs somewhere to put what people type.

Three forces shape it, and none of them is *how do we store a number*.

**The thing being collected is an opinion about a person, and opinions can be farmed.**
Two friends who partner every week play ten games with the same two opponents and produce
twelve ratings, ten of them one person's. An average over those twelve is not *what people
think of Karol*; it is *what Karol's regular partner thinks of Karol, plus a rounding
error*. The row on the sheet claims to be the first thing, and the count printed beside it
claims to say how much evidence is behind it — so both are false the moment repetition
counts.

**The thing being collected is the one strand a person can weaponise.** The other three
rows on the record card are counted by the platform: did you turn up, did you answer, did
you respond to a score. Nobody types those and nobody can lie in them. This one is typed by
somebody who may have just lost 6-2 6-1, and there is no appeal route behind it — no
moderation queue, no dispute, no *this rating was unfair* form, and none is in scope.

**The thing being collected must never be shown to the person it is about, individually.**
A published average plus a published count is a subtraction: an average moving from 4,80
over ten to 4,73 over eleven names the new rating as a 4, and the subject knows exactly who
they played. Every answer would be identifiable by the one person who must never see it,
and the failure mode is somebody being confronted about it at the club — after which
nobody answers honestly again.

There is a fourth force, and it is a property of this repository rather than of the
product. **Every aggregate here is event-sourced.** `users`, `rating`, `player_profile`,
`challenges` and `games` all replay a stream, and ADR-0137 wrote the argument for the most
recent one. `backend/CLAUDE.md` is explicit that a new context does **not** inherit the
matcher's four-ledger exemption: *it needs the same argument made in an ADR.* This is that
argument.

## Decision

### 1. You rate everybody else who was on the court, and nobody else

In doubles that is three people: both opponents **and your partner**. In singles it is the
one opponent. The person who saw you play closest was on your own side of the net, and a
design that collected opinions only from across it would be missing the best-informed one
in the game.

There is therefore no *side* in this context. A `SettledCourt` carries the game, the rater
and **the others** — a tuple in the line-up's own order, so a walk over it is the same walk
under every `PYTHONHASHSEED` (ADR-0105) — and the distinction the result cares about does
not survive the crossing. **Rating yourself is refused by the same rule that refuses a
stranger**, because the rater is not among the others; a second refusal for it would be a
second place for *everybody else* to be true.

### 2. One card per game, and submitting closes it

Everybody from one game is answered together. Two cards for a doubles game would turn a
busy month into a chore list, and forcing an answer about all three is how default-fives
are collected.

**Any of them may be left blank, and a blank stays blank for ever.** **A card with everybody
blank is an answer** and closes the card too: an explicit *I am not rating anyone* is a
thing somebody decided, and leaving it to expire would park a dead card in the list for a
week. A second submission is refused — there is no correction path, and no route that
amends one.

**Not rating costs nothing.** No strand, no obligation, no penalty, and — this is the part
that shapes the schema — **no record of the omission**. Somebody left blank is not a row
with a null in it; they are not in the table at all.

That is why there are **two tables and not one**. `sportsmanship_card` records *this player
answered for that court*, and `sportsmanship_rating` records *this player currently thinks
that of that person*. The all-blank card is the case that makes the first table
unavoidable: it has no ratings, and it still has to close.

### 3. Only a rater's most recent rating of a person counts — and the collapse is the primary key

`sportsmanship_rating` is keyed on **`(rater_id, subject_id)`**, not on the game. A later
card **replaces** the earlier answer.

We considered keying it on `(game_id, rater_id, subject_id)` and collapsing at read time,
which is the shape that keeps the history. We rejected it. A read-time collapse is a rule
every future reader has to remember, and the first reader to forget hands the farming
problem straight back — silently, with a plausible-looking number. Keyed on the pair, the
rule is a fact about the schema: it is the same move `0013` makes for interest, where *the
primary key is the idempotency rule*, pointed at a different problem.

Collapsed, ten games with one partner and two opponents give **three** ratings rather than
twelve, and the count printed beside the figure then means *how many different people have
an opinion* — which is the number a reader actually wants.

**The earlier answer is not archived.** Individual ratings reach nobody on any route, there
is no appeal route behind the figure, and a history kept for nobody to read is a history
somebody eventually reads.

A blank is **the absence of an opinion, not the withdrawal of one**: leaving somebody out
of tonight's card keeps whatever you last said about them, because the delete is scoped to
the pairs this card actually answers.

### 4. This context stores, and it is the first aggregate here that is not event-sourced

`SportsmanshipCard` is an aggregate: the card and every answer on it are written together,
and every rule about who may be on it holds across the whole of it. It is enforced in the
constructor, so a card that exists is a card that was legal.

It is **persisted, with no events and no outbox**, and the argument is the one
`backend/CLAUDE.md` demands rather than the matcher's exemption borrowed:

- **There is no life story to fold.** A card is born answered. There is one act, it happens
  once, and nothing may amend it — so a stream would be one event per card and a replay
  would be a `SELECT` with extra steps.
- **Nothing subscribes.** The published figure is a fold over rows computed at the moment
  somebody opens a record; nobody is notified, least of all the person rated. An outbox row
  would be a row no handler is waiting for.
- **Nothing derives a standing from it.** The reason `games` is event-sourced is that a
  standing is folded from a record and a clock; there is no clock here and no standing —
  a card is closed or it does not exist.

The exemption is for this context and does not travel, on exactly the terms the matcher's
does: the next context that wants it makes the argument again.

### 5. The matcher never reads any of it — the floor and the term

Not as a term in Match Fit, not in `QUALITY_FLOOR`, not as a tie-break, not as a filter.

A reader seeing `3,1 / 5 · 12 players` and deciding for themselves is the product working.
The app halving somebody's exposure on the same evidence, silently, with nothing they can
answer, is not — and this is the one strand where the evidence is a human opinion with no
appeal route behind it. Exposure is the thing this platform actually rations, so a hidden
demotion on typed evidence is the heaviest sanction it has, applied on the lightest.

**This is enforced, not stated.** `.importlinter` forbids `app.modules.matchmaking` from
importing `app.modules.sportsmanship`, and that contract is the only thing that would go
red: a Match Fit term reading a star average would look like every other term beside it,
and no test would fail. The engines need no arm, because `engines-are-pure` already forbids
them `app.modules` outright.

**Therefore the reliability pill is the counted-only number.** This follows from the
mechanism rather than being a second decision: a star average is not a ratio out of a
hundred, so it cannot be a strand in a weighted mean over ratios. The pill is *shows up ·
answers challenges · answers about results*, and it is exactly what the matcher acts on —
which keeps intact the stated reason the floor reads the published number at all: **a
player who works their visible score back up must be able to see the penalty lift.** Had
the pill included opinions the matcher ignores, the number a player can see would not be
the number that demotes them, and the penalty would become the unexplainable kind that rule
exists to forbid.

### 6. No individual rating is returned to anybody, on any route, in any shape

The write route answers `204`, on the pass's argument: *there is no shape a pass may cross
the wire in*, and there is none here either. The use case returns `None` for the same
reason — a use case that answered something would be a shape a route could be tempted to
render.

**`SportsmanshipLedger` has no method that answers *what did somebody say about me*, or
*what did I say about them*.** That is `InterestLedger`'s shape and a stronger version of
its argument: an inbox there was a query nobody wanted, and here a leak is the failure the
whole design exists to prevent. A route wanting to leak one would have to grow a read
first.

What may be published, in the tickets that follow this one, is an **average** beside the
count of distinct people behind it — and to the **subject**, a coarse band with no count at
all.

### 7. What this context borrows, and what it does not

One inward port, `SettledCourts`, one method wide. It asks `games` *is this a settled court
of mine, and who else was on it* and answers with the court or with nothing. The adapter
lives in **this** context's infrastructure, which is the shape `games` itself takes for
`PlayerHandles`: a provider publishes what it knows about its own subject, and the context
that wants it narrower does the narrowing.

*Settled* is `games`' word, **narrowed**. Over there a plan nobody ever claimed is settled
too, and there is nobody to rate for an evening that did not happen. Here it means
`SETTLED ∩ PLAYED`: confirmed, or unscored because two sides disagreed and both windows
closed. **An unscored game is in, on purpose** — two people who cannot agree what the score
was were still on a court together for two hours, and how that went is the thing this
context exists to collect.

The read asks *which games are mine* and never *which game is this*, so a game the caller
did not play in is **not findable through it at all**: *you may only rate a court you were
on* is the shape of the query rather than a check somebody remembered to write.

**Nothing is re-gated against anybody**, and this is a decision rather than an omission. The
four fail-closed gates decide who may be *introduced*; ADR-0095 §7 already settled that a
block is forward-looking and does not reach into a game already agreed, and ADR-0141 applied
that to the seats of a game. It applies here for the same reason and one more of its own: a
block that stopped somebody rating you would make blocking the way to dodge a bad rating, and
everybody who had just played badly would reach for it. The card also returns nothing about
anybody — it is a `204` — so there is nothing here for a gate to withhold.

**One refusal covers three cases** — no such game, not yours, not settled — byte-identical,
naming nothing. It is `games`' own argument: separating them would answer *is this id real*
about four strangers' evening. Nobody legitimately reaches it, because the card is drawn
from a read that lists only games this player may rate, so arriving there is a stale screen
or a race and all three have one remedy.

### 8. The range lives in the domain and not on the wire

One to five whole stars. **No zero**: a rating that reads as *worthless* is a weapon out of
proportion to a tap, and one star already dents an average about as hard. **No halves**:
five taps, one number.

The wire declares a plain integer deliberately. A Pydantic bound restating `1..5` would be
a second copy of the rule, and the first of the two to be edited would win silently for
whichever callers went through it. It is refused rather than asserted — a star count
arrives from a person tapping it, so a bad one is somebody's client and not a broken
precondition, which is `games`' own split for a score applied to the one other value in
this repository a player composes by hand.

## Consequences

**A schema change is now the thing that would have to be argued for.** The collapse cannot
be forgotten by a reader, quietly weakened by an optimisation, or reintroduced through a
window function somebody got wrong; undoing it means writing a migration, and a migration
is read.

**Nothing can be recomputed from a corrected rule.** The history is gone by design, so if
the collapse turns out to be the wrong shape — say a decayed average over every rating ever
given turns out to be better — the data to build it does not exist and will not for as long
as it takes to accumulate again. This is the cost, and it is accepted rather than hedged:
storing a history for a hypothetical rule is how the subject-identifiability problem gets
reintroduced through a table nobody remembers is there.

**The published figure has no minimum and can be one person's opinion.** `3,0 / 5 · 1
player` will appear on real records. The count carries that, and the card's existing
discipline — a figure is always printed beside its denominator — is doing the work.
Trimming outliers was refused because trimming is the platform deciding which raters were
wrong, which is a larger claim than publishing the number.

**Nobody is obliged to rate, so the figure will be sparse for a long time.** That is
deliberate — making a voluntary opinion compulsory harvests exactly the low-quality answers
this design avoids — but it means a reader will often find the block absent, and a player
with no ratings has the field absent entirely rather than showing a zero.

**A player can be rated badly by somebody who has nothing else against them, for ever.**
There is no appeal, no moderation and no way to answer it. What bounds the damage is that
it does not touch exposure, and the fifty-rater window means a bad patch eventually falls
out. That is the whole of the mitigation, and it is worth being clear that it is not much.

**One rater's opinion can be moved after the fact by playing again.** Somebody who rated 5
in August and 1 in November has said 1 — and, symmetrically, somebody who wants to soften an
angry rating can play the person again and revise it. Both follow from the key. The second
is a feature and the first is the price of it.

***Most recent* means most recently answered, not most recently played**, and the two can
disagree. A card stays open for seven days, so somebody who answers Tuesday's card on Friday
and Monday's card on Saturday has their opinion of Monday standing. This is the only place
the key could surprise, and it is the right reading of the two: what the average is asking
is *what does this person currently think*, and the answer to that is the last thing they
said — not the last court they stood on.

**The context is stored, and this repository now has two persistence styles.** A reader who
learns *aggregates are event-sourced here* from `games` will find one that is not, and the
docstrings on `card.py` and `card_model.py` carry the argument at the site rather than only
in this record. That is the cost of the exemption, and it is why the next context asking
for it makes the case again.

**A guardrail exists for a decision that has no code behind it yet.** The import contract
refusing the matcher this context is green today because nothing in the matcher has ever
wanted a star average. That is the point — it is armed before the first person reaches for
one — but it is also a contract that will look like decoration until it fires.

## Amendment — 2026-09-08: the port answers at two arities, and the read that grew leaks nothing

Building the games-list card ([#378](https://github.com/Rakieta02/Rakieta/issues/378)) needed
the one thing this record described as absent: *which of my games are still waiting for my
stars*. Two sentences above are corrected here rather than in place, because this record is
immutable once accepted.

**§7's "one method wide" is now two, and it is still one question.** `SettledCourts` gains
`courts_of(player_id, now)` beside `court_of(game_id, player_id, now)`. Both ask *is this a
settled court of mine, and who else was on it* — the plural draws the list a player is
offered and the singular is the gate on the act — and the narrowing (`SETTLED ∩ PLAYED`) is
applied in one private place so a list cannot offer an ending the act would refuse. The
adapter is unchanged in shape: the directory only ever answered *which games are mine*, so
the singular was always the plural with one id kept, and the two arities cost the same thing.

**§6's "a route wanting to leak one would have to grow a read first" was a rule, not a
prediction, and the rule held.** `GET /api/v1/sportsmanship` is that read, and it carries a
game id and the people on that court — an evening, and nothing anybody said about it.
`SportsmanshipLedger`'s `has_been_answered` became `answered_among(rater_id, game_ids)`, a
set of *closed cards*: still a fact about an act, with no method anywhere on the port that
answers *what did somebody say*. What the write route returns is unchanged and is still a
`204`.

**The card's week is enforced on the read and deliberately not on the write.** *Not until
the day after, and for seven days* lives in `sportsmanship/domain/window.py`, and it decides
when somebody is **asked**. `AnswerTheCard` refuses on *whose evening it was* and *has it
been answered*, neither of which is a clock: a player who opened the card at six days and
twenty-three hours and tapped submit a minute later would otherwise be told their opinion was
too late, and nothing is protected by that — nobody is docked for a card that lapsed, and
§4's collapse already means only a rater's most recent answer about a person counts. The
window is the prompt; it is not the permission, and the difference is pinned by a test rather
than left to be re-derived.

**Both edges run from `games`' `played_at`**, which is *the moment somebody said we played*
and never the hour on court — this platform records no such hour. It is never earlier than
the game, so the day-after rule holds conservatively. The cost of not anchoring the close to
a settlement is that a game two sides argued over settles up to a day into its week and its
card is drawn for six days rather than seven; the alternative is an argument over a score
restarting somebody's week, which would make the card's life a property of the argument
rather than of the evening.

**Nothing else moves.** No rating crosses the wire, the collapse is untouched, the matcher
still reads none of it, and the context still stores exactly the two tables §3 describes.

## Amendment — 2026-09-08: the figure is published, and the band's edges are whole stars

[#382](https://github.com/Rakieta02/Rakieta/issues/382) built the read §6 called *what may be
published, in the tickets that follow this one*. Everything that record decided held; what
follows is what shipping it added, and one thing it did not decide.

**A third port, and it is the only one pointed outward.**
`PublishedSportsmanshipQuery` answers `published_for` — the figure and how many different
people it rests on — and `band_for`, three steps wide. It is **not a method on
`SportsmanshipLedger`**: that port is this module's store, a consumer holding it could write
through it, and §6's silence is about what a store may be asked rather than about a table.
`player_record` declares its own `SubjectSportsmanship` beside it and translates in an
adapter, on ADR-0159 §6's rule.

**Two methods rather than one answer a caller narrows, and that is the whole of §2 made
structural.** A use case that received the figure and coarsened it itself would already be
holding the subtraction — the rule is about what crosses the seam, not about what is
rendered. So the sheet about *you* calls a method with no figure in its return type, and the
one that has a figure is never called on that path. `PlayerRecord` refuses the pair beside
`is_self` outright, so a branch taken the wrong way is loud rather than a screen quietly
showing somebody the arithmetic of their own ratings.

**The band's edges are whole stars, and this record did not decide them.** `GOOD` from 4,0;
`MIXED` from 3,0; `POOR` below. Whole stars over a one-to-five scale is the coarsest
three-step reading that is still about the scale a person taps, and the coarseness is the
safety: at one or two ratings it cannot be informative about any individual, and even at
fifty a step this wide moves for a change of habit rather than for one evening. **It is
coarsened from the published figure and never from the raw mean**, so a subject's band cannot
land on the other side of an edge from what a reader is shown — one record, read at two
resolutions, with one rounding between them.

**The collapse cost the fold nothing, which is what §4's key bought.** There is no `GROUP
BY`, no `DISTINCT ON` and no window function in the adapter: one row already is one person,
so *the fifty most recent raters* is a `LIMIT` on an ordering rather than a collapse
performed at read time. The order is total — `rated_at` then `rater_id` — because two rows
written in one transaction carry the same instant and two processes must fold one record to
one figure (ADR-0105).

**Halves round up, at one decimal, and the rule is spelled in this context.** `round` rounds
to even, so 4,25 would print 4,2 and 4,35 would print 4,4 — a rule nobody reading a figure
out of five expects. `player_score` makes the same argument for percentages; the two are
separate because a context importing the other's rounding would be importing the other's
scale with it.

**The word `stars` does not reach the wire.** The forbidden-fact sweep refuses that property
name outright, and §6 said so about itself: *it catches nothing about a figure published
under an honest name*. What crosses is `average` and `raters` under `sportsmanship`, and
`sportsmanship_band` for the subject — and a test walks the emitted contract to assert those
words reach exactly one response type, which is where *it is not on search result cards*
stopped being a promise.

**The coarseness argument does not hold at the bottom of the window, and that is worth
recording rather than repeating.** §2 says *at one or two ratings the band is deliberately too
coarse to be informative about any individual*. It is not: stars are whole, so a subject with
exactly one rater who is shown `MIXED` has been told their rating is exactly 3, and they know
who they played. What protects them at n=1 is the other half of the rule — **no count
crosses**, so they are not told they have one rater, and the inference needs them to work it
out from their own settled games, which somebody with one game can. This is the same class of
cost §2 already accepts and it does not change the decision; the mitigation *the band is too
coarse* simply starts working further up the window than that sentence claims, and the
sentence should be read as the intent rather than as the arithmetic.

**Nothing else moves.** No individual rating crosses on any route, the matcher still reads
none of it, the pill is still the counted-only number, and the context still stores exactly
the two tables §3 describes.
