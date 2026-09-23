# ADR-0152 — A mutual mints again once the last one it minted is finished with

- **Status:** Accepted
- **Date:** 2026-09-07
- **Answers [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §1's filed question** — *may a pair with an unplayed game arrange a second one?* — **for the
  mutual path only**, which is the path that could not survive leaving it open.
- **Confirms 0142 §1 for the send path.** This record builds the port onto `games` that §1 said
  `challenges` did not have, and then **declines to use it on the send**. The block released on
  `ON` stays released.
- **Does not touch 0142 §2.** `ON` still reaches no conclusion and gets no exit; what is released
  here is a *guard*, never a challenge.
- Settles [#371](https://github.com/Raketa02/Raketa/issues/371), and **bounds**
  [#370](https://github.com/Raketa02/Raketa/issues/370) without deciding it.

## Context

0142 §1 released the one-open-challenge-per-pair rule on `ON`, and in doing so took the only guard
out from under the **mutual mint**. `express_interest` opens a game on the **mutual** rather than
on whether this tap wrote a row — deliberately, because a repeat tap is the one occasion the
platform ever gets to retry a mint a gate refused — and a singles mutual is `ON` the instant it
exists. So the mint was given a question of its own, `standing_pairs_among`: *does a challenge
already stand between these two, in this sport or any other?*

**That question never stops answering yes.** A mutual-born singles challenge has both seats
accepted at birth, so it can never lapse and can never be declined; 0142 §2 gives the withdraw
exit to `LINE_UP_INCOMPLETE` and denies it to `ON` in as many words — *"`ON` has become a game,
and ending the challenge would not touch it."* Nothing in the codebase ends it. Folded forward,
the guard holds a pair for the life of the database:

```
standing now         : Standing.ON
standing +1yr        : Standing.ON
stands +1yr          : True
mint refused +1yr    : True
```

**The stated reason and the implemented rule do not line up.** `CONTEXT.md` justifies the guard's
reach with *"a repeat tap is the same yes pressed twice"* — an **idempotence** argument. But an
`Interest` is keyed `(from, to, sport)` and **expires**, while the guard it justifies is
cross-sport and eternal. A padel yes is not the same yes as a tennis yes pressed twice, and a yes
that expired eighteen months ago is not being pressed at all. The rule outran its own reason.

The consequence is the shape 0142 §1 had just removed one method along: a pair whose tennis game
was minted from a mutual can never be given a padel one by a second mutual, ever. What made it
hard to see is that it is **not** the permanence of #343 — the deliberate path is untouched, and
either of them may still send the other a court from a search. They are not cut off. They are
shown a mutual the platform will never honour, which is #370.

## Decision

### 1. The guard's job is idempotence, and the pair rule is somebody else's job

**One mutual mints one game.** That is the whole of what this guard is for, and it is what the
glossary's own justification argues for. *Are these two already arranging something* is a
substantive rule about two people, it already exists, and it belongs to the send path's
`open_pairs_among`.

Conflating the two is what produced a rule with no release: a question about **whether an act has
already been performed** was answered with a question about **what state two people are in**, and
those have different natural endings. An idempotence guard ends when the act it is protecting is
finished; a state question ends when the state does. Reading one for the other is why the guard
inherited `ON`'s eternity, which is a property of the *state* and has no business bounding an
*act*.

### 2. The mint asks both questions, and is therefore strictly stricter

Narrowing the guard to a pure idempotence key would open a gap: A sends B a tennis challenge, it
sits `AWAITING_ANSWERS`, both then tap *Let's play*, the mutual has minted nothing, and a second
tennis challenge is created between two people already arranging one. So the mint asks:

1. **Are these two already arranging a game?** — `open_pairs_among`, the ordinary pair rule.
2. **Has a mutual between these two, in this sport, already minted something unfinished?**

Both must pass. Today's superset caught case 1 by accident; from here it is deliberate. **The
glossary's *asymmetry is the point* survives and is sharpened**: the mutual path is stricter than
the send because it is the union of the send's rule and one more, rather than because it happens
to read a larger set. *Let's play* being the cheaper act must never make it the more permissive
route.

### 3. The key is a mutual-born challenge, for this pair, in this sport

`ChallengeOpenedFromMutualInterest` is already a distinct event, and `Challenge.sport` is already
a field set from it. So *did a mutual between these two in this sport already mint something* is
answerable from the streams as they stand — **no new event, no migration, no addition to the
durable name list**.

The rejected alternatives are worth recording. **A marker written back onto the `Interest` row**
would cross a context boundary to write, put the mint's bookkeeping inside the matcher's
aggregate, and — if written on *attempt* rather than on success — silently kill the retry that §6
depends on. **Adding a third `ChallengeOrigin` variant** is refused by that type's own rule: origin
is *"per seat, never per challenge"* and *"two answers, and never a third"*, and a mutual-born
challenge's seats correctly carry no origin because nobody was invited.

### 4. *Finished with* means the arranging stopped and the game is settled

The hold is on a mutual-born challenge that is **unfinished**, which is either of:

- it is **still being arranged** — a doubles mutual mints a `LINE_UP_INCOMPLETE` court with a side
  still to fill, and no game exists yet; or
- it produced a game and **that game is not settled**.

`games` already derives `SETTLED = {NEVER_PLAYED, CONFIRMED, UNSCORED}` — *nothing more will
happen to this game* — and that is exactly the condition the hold is waiting on.

Two readings are decided here because both are natural and only one is right. **A ghost game
releases the pair.** `NEVER_PLAYED` is settled: the entry window closed and nobody ever said it
happened, so nothing more will happen to it, and two people whose arranged game evaporated may try
again. *Settled* is not *played*, and reading it as *played* would hold a pair on the strength of
a game that never occurred — the same blocked-by-nothing shape this record exists to remove. **A
mutual-born challenge that ended without ever producing a game releases them too**: once #325's
withdraw ships, a withdrawn half-built court has finished with nothing to show for it, and holding
the pair on its memory would recreate the permanence one branch over.

> **Amended 2026-09-12 by [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md).** `SETTLED`
> is `{NEVER_PLAYED, CONFIRMED, UNSCORED, CALLED_OFF}`: a game called off with a seat open is
> finished with on the same reading as a ghost — nothing more will happen to it — and releases
> the pair as a ghost does. Its challenge is `WITHDRAWN`, which the paragraph above already
> releases, so a mutual whose game was called off may mint again.

### 5. The release is a port onto `games`, and the send path does not get one

`challenges` grows `SettledGameQuery.settled_among(challenge_ids) -> frozenset[UUID]` in
`domain/settled_game.py`, answered by an adapter in `infrastructure/games_settled_game.py` and
wired in the composition root. This is **not a new dependency edge**: the arrow already runs
`challenges -> games`, stated in `games_planned_game.py`, and `OpenChallengeFromMutualInterest`
already holds `PlannedGameOpening`. The use case that opens a game is now also the one that asks
whether the last one is finished, which is one responsibility rather than two.

It is **bulk and keyed by challenge id** — bulk because a pair may hold several mutual-born
challenges across sports and one-read-per-challenge is the shape this codebase refuses in writing;
by challenge id rather than by pair so that `games` never learns what a pair is. The
`challenges`-side read is **pair-shaped**, not `…_among`: the mint has exactly two people, and the
bulk shape exists to answer the send's six pairs on one court. A method that takes a collection
but is only ever called with two invites somebody to pass three.

**The send path does not get the settle-hold, and this record had the port in hand when it decided
that.** Extending it would mean two people with an unplayed game could not send each other a
second challenge — re-adding, by a side door and one ADR later, the block #343 argued for removing.
The mutual hold is idempotence of an *automatic* act; a send is a person deliberately choosing a
court, and 0142 §1's *nothing replaces the block* stands as a decision rather than as a deferral.
Recording the refusal matters more than the refusal: without it, the next reader finds a
`challenges → games` port and assumes nobody thought to use it here.

### 6. A read that cannot answer refuses the mint, and the retry is why that is safe

The mint runs inside `express_interest`'s transaction, and it may not raise — *"a raise would roll
back the yes, which was somebody's own act and is not the thing being refused."* So a
`settled_among` that cannot answer **fails closed**: no game, `None`, silently, exactly as
`TheGatesCouldNotBeEvaluated` already does.

Failing closed is only defensible **because a repeat tap retries**. That property — the mint
hanging off the mutual rather than off `created` — was load-bearing before this record and is
load-bearing in a second way now: it is what turns a transient read failure into a delay instead
of a game two people never get. It is therefore not available to be traded away for simplicity
later, and this is where that is written down.

**This is deliberately the opposite of the send's rule.** `open_pairs_among` documents that a read
which cannot complete *raises what it raised*, because *"what must never appear is the other
answer — an implementation that returned no pairs when it could not tell."* The two differ because
their failures cost different things: the send has a person waiting on a press and its own
transaction to fail, and the mint has somebody's yes to protect and another tap coming.

### 7. `standing_pairs_among` and `players_seated_at` go

Both were added four weeks ago for this one caller, and the mint stops using them. They are
deleted in the same commit rather than left in place, because a second, subtly-wrong answer to
*does a challenge stand between these two* sitting on a public port is what the next person
reaches for. The aggregate returns to one membership plus the arranging predicate.

## Consequences

- **The mint's question can no longer be answered inside `challenges`.** Every mint now performs a
  two-context read. That is the price of §4's release, and it is precisely the cost 0142 §1 named
  when it filed the question instead of taking it. What made it affordable was finding the seam
  already built: the port, the direction, the adapter pattern and the use case that holds it all
  existed for `PlannedGameOpening`.
- **Behaviour changes in two directions, and only one of them is a loosening.** Cross-sport mints
  and post-settlement mints now succeed. But the mint also begins refusing deliberately in a case
  it previously refused only by reading a superset, which means the rule now says what it does.
- **#370 is bounded, not fixed.** Between the mint and the result settling, a repeat tap still
  returns `mutual: true`, still lands both people in each other's *Let's play* mutual list, and
  still opens nothing. That window is now finite where it used to be permanent — but a finite
  dishonest surface is still a dishonest surface, and what the screen should say about a pair whose
  mint was **correctly** refused is a product decision that must not be smuggled into a record
  about domain scope. It is named here so that it cannot be lost, which is the failure mode #343
  demonstrated: `games_match_history.py` stated the correct behaviour as settled fact for the whole
  time nothing implemented it.
- **The rule is now three sentences instead of one**, and its cost is that reading the mint's
  refusal requires holding both questions at once. The alternative — one question that happened to
  cover both — is what shipped a permanence nobody chose.
- **Nothing on the wire moves.** `standing_pairs_among` and `players_seated_at` are internal, the
  matcher's `OpenChallenge` is an internal port type and not a schema in `openapi.player.json`, and
  `mutual` keeps reporting what the two rows say. No client regenerates.
- **`local` is the only environment that runs**, so there is no live data on which the newly
  released pairs would appear. On any future restore, existing mutual-born challenges whose games
  have settled release the moment the code ships — correctly, and with no backfill.
