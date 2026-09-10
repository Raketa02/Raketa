# ADR-0154 — A mutual names the game it has, and names nothing when it has none

- **Status:** Accepted
- **Date:** 2026-09-10
- **Fixes [#370](https://github.com/Raketa02/Raketa/issues/370)**, the defect
  [ADR-0152](0152-a-mutual-mints-again-once-the-last-one-is-finished-with.md) **bounded and
  deliberately declined to decide** — *"a finite dishonest surface is still a dishonest
  surface, and what the screen should say about a pair whose mint was correctly refused is a
  product decision that must not be smuggled into a record about domain scope."* This is that
  record.
- **Extends [ADR-0130](0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)** from the
  read-back to the mutual: *a withholding is stated; the gate that withheld it is not named.*
- **Does not touch `mutual`.** It still reports what the two rows say, and reporting it `false`
  because a gate refused stays refused. 0095, 0096 and 0124 are untouched — nothing about who
  or why crosses.
- **Does not touch 0152.** What changes is what the mint *answers with*, never what it refuses.

## Context

Two people tap *Let's play* on each other. `express_interest` reads the two rows, finds them
facing each other, calls `open_from_mutual_interest`, **throws the answer away**, and tells
both of them `mutual: true`. When the mint refused, nothing is opened and nothing is said. The
product knew, and did not say.

0152 removed the permanence — the guard now releases when the game settles — and named what it
had left behind rather than fixing it. What is left is small and exactly stated: between the
mint and the settlement, a repeat tap reports a mutual and opens nothing.

### The mint already knows, and the caller discards it

`OpenChallengeFromMutualInterest.execute` returns `UUID | None`, and there are four ways
through it:

1. it **minted** a challenge and returns its id;
2. `open_pairs_among` says the two are **already arranging something else** — `None`;
3. the mutual's **own earlier challenge is not finished with** — `None`;
4. a safety gate **refused, or could not be read** — `None`.

`express_interest` writes `await self._challenges.open_from_mutual_interest(...)` with no
assignment. Case 1 is a game the player is not shown a door to, and cases 2 and 3 are a game
they already have that nobody mentions. **The defect is not that the mint refuses. It is that
the answer is discarded**, so a tap that opened a game and a tap that could not are the same
silence.

### Two things are not available, and they bound everything below

**`mutual: false` is not available.** `express_interest.py` is explicit: *"Reporting the mutual
as `False` because a gate refused would tell the sender something about the other person that
no refusal here is allowed to say."* That reasoning is sound and survives this record intact.

**Naming the cause is not available.** Case 4 collapses a block in either direction, a hold, an
account `users` may not show, and the mutual gender preference. 0130 refused to publish that
spelling on the read-back and the refusal transfers verbatim: 0095 says a block leaves *no
trace anywhere in any response*, 0124 says a hold and an unshowable account are told to nobody,
and 0096 says a gender preference is readable only by its owner.

### What 0130 does make available

0130 did not conclude that the read-back must stay silent. It concluded that **the fact of a
withholding is publishable and its cause is not**:

> Four causes … reach the wire as **one indistinguishable statement**.

The searcher was already shown the row; the only new fact is that the product will no longer
show it. The same holds here. The sender chose this person and tapped on them — the mutual has
already told them the other person said yes. Saying *and here is your game*, or saying nothing,
adds no person and no gate to what they hold.

## Decision

### 1. The mint answers with the game the two of them have, not with what this call minted

`MutualChallengeMinting.open_from_mutual_interest` keeps `UUID | None` and **its meaning
moves**: it is *the challenge this mutual has open* — the one minted by this call, or the one
minted by an earlier tap that is not yet finished with — and `None` when there is none.

The signature does not change because there is nothing new to say: the id was already the
answer and the second case was already read. Case 3's guard calls
`mutual_born_challenges_that_became_games` and holds the ids in its hand before returning
`None`. **Returning one of them instead is the whole of the mechanism.**

This is the mint's own bookkeeping answering about its own act, which is what 0152 §1 named it:
*one mutual mints one game.* Having established that the guard is idempotence, the natural
answer to a repeat performance of an idempotent act is **the thing the first performance
produced** — not silence.

### 2. It names the mutual's own challenge and never somebody's send

Case 2 — the two are already arranging something else — answers `None`, and that is a decision
rather than a limitation of the read.

It could be otherwise. `ChallengeHistoryQuery.open_challenges_with` returns `SharedChallenge`
rows carrying `challenge_id`, so the id exists one port over. It is not taken, for three
reasons that compound:

- **`open_pairs_among` answers pairs and not ids by decision.** 0150 §3 grew exactly one id
  onto exactly one port for exactly one reader, and called the growth *"the honest price"* of a
  fill naming the challenge it completes. A second reader wanting a second id is how a bulk
  mask keyed on pairs turns into a directory.
- **A send is not this mutual's doing.** *Let's play* pointing at a court somebody deliberately
  chose would conflate two acts the product has kept apart everywhere else, and it would put
  the matcher's answer in the business of narrating the challenge context's inbox.
- **Nothing is hidden from them.** A challenge they are arranging is already on their own inbox
  and their own Now. The player is not being kept from a fact; they are being told, by this
  route, only about what this route did.

### 3. Absence covers two unrelated causes, and that is what makes it publishable

Under §2 the answer is `None` when the pair are **already arranging something else** or when a
gate **refused or could not be read**. One of those is wholly innocent and already visible to
the player on two other screens. The other is the one 0095 says leaves no trace.

**The fold is the safety property, not an artefact of it.** 0130 could publish `withheld: true`
because four causes arrived as one statement; this field crosses on the same grounds and on no
others. It is a weaker disclosure than 0130's, because 0130's `withheld` is attached to a named
row and attributes the withholding to that person, while this says only *no game was opened for
you here*.

**This is the constraint on every future change to this field, and it is why it is a numbered
paragraph.** If a later change gave case 2 a challenge id — the obvious tidy-up, and §2 is one
port read away from it — absence would mean *a gate refused about one of you* and nothing else.
At that moment the field becomes exactly the trace 0095 forbids, and **the field must go, or
the case must be folded back in.** A reader who takes §2 for conservatism and removes it will
have re-created the leak this record exists to avoid.

### 4. There is at most one, and when there is more than one the newest is named

0152's guard makes a second mutual-born challenge impossible while the first is unfinished, so
the set §1 draws from has one element. *In practice.* A database restore, a clock moving
backwards or two taps racing can leave two, and `frozenset[UUID]` has no order to pick from —
`min()` over uuids is deterministic and meaningless, which is the worst of the options
available.

So `mutual_born_challenges_that_became_games` answers `tuple[UUID, ...]`, **newest first**, the
same shape and the same reason as `pairwise_counterparts`. Ordering becomes part of the demand
rather than a property today's adapter happens to have, and the mint names the first unfinished
row. The guard's `minted <= settled` reads over the tuple unchanged in meaning.

Determinism is [ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md)'s subject
and this is the ordinary case of it: an answer a player sees may not depend on set iteration
order.

### 5. The wire carries the id, and the client renders a door

`ExpressedInterestResponse` gains `challenge_id: UUID | None` — *the game the two of you now
have, when there is one.*

**An id rather than a boolean**, because it is the same read and strictly more product: the
player gets a door to the game rather than a fact about it, and a singles mutual is `ON` from
birth so the game is there to be opened the moment the sentence appears.

**It teaches the matcher's contract no new word.** `mutual_challenge.py` already says *"the
challenge that now stands between them"*; the matcher carries an opaque id and still never
learns what a Challenge is.

The client's sentence splits. Today's *"You both said yes — {name} sees it the next time they
open Raketa"* is kept **exactly** for the absent case: it is a true sentence about a mutual and
it promises no game. When the id is present the sentence says the game is there and the row is
a door to it. **The absent case must not be rendered as a distinct negative state** — no *no
game was opened*, no empty slot where a door goes — which is §3 arriving at the screen.

### 6. `GET /interest`'s mutual list is not given it, and the reason is that it is not lying

`InterestListResponse.mutual` is documented as *"yeses you sent that came back — both of you
said it"*, which is true in all four cases. It promises no game and never did.

Carrying the game there is a different and much larger thing: a bulk *which of these pairs have
a challenge standing, and which one* read that `matchmaking` does not have.
`MatchHistoryQuery.open_challenges` cannot answer it — *"open means being arranged, and a
completed line-up is not"* (0142 §1), and a mutual-born singles challenge is a completed
line-up from birth, so the rows this needs are precisely the ones that read excludes. It would
be a **new outward demand**, with a `FAIL_POSTURE` entry and a `tests/demands/` case, bought
for a list `frontend_player` does not render today.

**Filed, not taken** — and named here rather than left to be noticed, because *stating correct
behaviour as settled fact while nothing implements it* is the failure #343 demonstrated and
0152 called out by name. The list stays honest by saying less, and gains a door when something
renders it.

### 7. `mutual` does not move

It is what the two rows say. Every reason 0142, 0152 and `express_interest` give for that
stands, and this record adds one: with §1 in place, `mutual` no longer carries the weight of
implying a game, because the thing beside it now answers that question directly.

## Consequences

- **The tap stops being silent about a game that exists.** #370's observable closes for the
  case that produced it — a repeat tap after a mutual-born game — and case 1 gains a door it
  never had, so the *first* mutual is better off too. That was not the ticket's ask and is the
  larger share of the benefit.
- **Absence still covers a gate refusal, and no contract can stop a client rendering it as
  one.** §5 says what the screen must not do and §3 says why, but a renderer that draws *no
  game* as its own state re-creates the leak in a repository the backend does not own. This is
  the negative consequence that matters, it is not enforceable from here, and the review of the
  client change is where it gets caught.
- **A port's meaning moved without its signature moving.** `-> UUID | None` said *what I
  minted* and now says *what you have*. A reader who trusts the type over the docstring will be
  wrong, and there is no compiler between them and that mistake. The alternative — a named
  return type carrying the same one field — was refused as a type invented to make a sentence
  unmissable, but the trade is real and it is recorded here rather than defended.
- **`mutual_born_challenges_that_became_games` answers a tuple where a set said what it
  meant.** A set was the honest shape for a subset test; ordering is now demanded of every
  adapter and asserted in its tests, bought for §4's edge case. The guard reads no differently.
- **Every mint now has a caller that uses its answer**, which is a constraint on future
  refusals: a fifth way through `execute` has to decide what it answers with, and §3 says it
  may not be a fifth distinguishable one.
- **`openapi.player.json` moves and the client's types regenerate** — one `make gen-api`
  commit, per [ADR-0006](0006-backend-owns-api-contract.md). `openapi.dev.json` is untouched.
- **`local` is the only environment that runs**, so no live data is affected and there is no
  backfill. On any future restore the field is answered from the streams as they stand.
- **#370's list half is filed rather than fixed**, by §6, and the ticket says so.
