# ADR-0141 — A game names the people on its court, and the court is the gate

- **Status:** Accepted — **amended in one sentence by
  [ADR-0161](0161-the-game-screen-draws-its-courts-pairing.md)**: the seat on `GET /games`
  still carries the handle and nothing else, and a seat's Level is read *beside* the game,
  through a port, for the duration of `AWAITING_ENTRY`. *No `player_card` to hang them on
  later* stays true.
- **Date:** 2026-09-06

## Context

`SeatingSchema` is a side and a `player_id`, and that was the whole of what `GET /games`
said about the people on a court. No handle, no Level, nothing. It was not an oversight —
`_game()` in `games/presentation/routes.py` carried the argument in its own docstring:
*"a card, a Level and an area belong to a search's answer, where a gate decided they may be
shown … a screen that re-published somebody's profile off the back of it would be a
directory with extra steps."* The client answered the contract honestly and named **sides**
throughout, and said so:
[ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) §4 forbids inventing a
familiar form, and there was nothing here to shorten because there was nothing here at all.

[#319](https://github.com/Raketa02/Raketa/issues/319), found while building
[#314](https://github.com/Raketa02/Raketa/issues/314), is what that costs. Two things, and
both are about the screens working rather than about the screens looking bare:

- **Two padel games are told apart by *arranged 4 days ago* and nothing else.** It is the
  only distinguishing fact on a row of *Your games*, and it is a duration because this
  platform has no calendar to print a date against. Three games in a week are three
  near-identical rows.
- **A result is agreed with nobody.** *That's right* settles a score against a person, and
  the screen could not say which person. That is the one tap in the app where anonymity is
  not a neutral default.

Three shapes were considered, and the shape was the decision rather than the field.

- **A `player_card` on the seat,** as `CandidateSchema` carries. Rejected on ADR-0107's own
  rule read forward: a card is what a *searcher* reads to decide about a game that might
  happen, and every value on one is as-of-now. Stapled to a record of an evening in the
  past it makes a Level, a band, a likely range and a run of form say something they do not
  mean. It is also the most expensive shape by a distance — card assembly is a profile read
  and an object-store `HEAD` per person, bounded today by a shortlist of twenty and here by
  the length of somebody's playing history.
- **A route that turns ids into names.** Rejected: a new surface with its own gate to argue
  about, a second round trip in front of a screen that already holds the ids, and a route
  keyed on a stranger's id answers *is this id real* — which is precisely what the single
  `you_were_not_on_this_court` code exists to refuse. Scoping it to *people you have played
  with* makes it this read wearing a different route.
- **Nothing, and keep sides.** The status quo, and the two costs above are what it is.

The part that had to be argued before any field was added is **whose gate it passes**. The
four fail-closed gates — a block either way, a hold, an account that may not be shown, and
the mutual gender preference — decide who a searcher may be shown, and a court somebody was
already on is not a search.

## Decision

**We will put the handle on the seat, and nothing else, and the court will be the gate.**

### 1. A handle, and the closed list is closed at one

`SeatingSchema` grows `nickname` and grows nothing else. No Level, no band, no likely
range, no area, no Social tags, no photograph, no Player Score, no run of form — and no
`player_card` to hang them on later. The test the field passes is not ADR-0107's *a card
says only what its subject published*; it is a narrower one this record owns: **a record of
a game may say what the people in it were already calling each other, and nothing that a
gate decided somebody may see.** A handle is what four people knew about each other by the
time they were on a court together. A Level is not.

ADR-0107 §4 applies unchanged and is the reason the field is a whole handle: **nothing may
derive a familiar form from it**, and every sentence naming somebody uses all of it or
names nobody.

### 2. The court is the gate, and nothing is re-evaluated against the reader

`GET /games` already answers about games you were on the court of. That scope is the whole
of the permission, and no seat's handle is re-gated against the reader.

This is not a new position; it is an existing one applied.
[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) §7 says a
block is **forward-looking**: *"It does not reach into a game already agreed or a chat
already open."* §8 closes the other direction — *"neither party is ever notified, and the
other side sees no trace anywhere in any response"* — and a handle that disappeared from a
row a reader has already seen **is** that trace. Re-gating would leak the thing it claims
to protect, while hiding a word rather than a person: the `player_id` stays in the list
either way, because a seat cannot be dropped without publishing a three-person doubles
game.

> **That last clause is narrowed 2026-09-12 by [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md).** A seat still cannot be dropped — and
> it can now be **open**: somebody who leaves the game before it is played has their seat
> drawn with `player_id: null`, in its place, so the court still says which side is short and
> a four with one seat open is still a four. The argument survives its conclusion; the
> conclusion was one word too narrow.

[ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) and
[ADR-0124](0124-the-matcher-gates-account-state-never-age.md) are gates on who may be
**introduced**. An evening you were both at is not an introduction.

### 3. `null` where `users` no longer has the account, and the seat stays

`PlayerHandles.handles_of` may answer about fewer people than it was asked about, and a
missing handle is `null` on the wire rather than a dropped seat. The shortlist does the
opposite — a card with no nickname is not a card, and the row goes — and the difference is
the point: a *seat* with no nickname is still a person who was on the court. The client
already draws this case, as the question mark a Play court gives a seat whose row the
record can no longer describe.

### 4. One set read, in the application layer, per response

`games` borrows the handle through a port of its own — `PlayerHandles` in
`games/domain/ports.py`, adapted onto `users`' published `find_nicknames_of` — so this
context does not become a second reader of somebody else's schema. `ReadGames` asks **once
for a whole list**, over the union of every court in it.

The two result acts ask once for the one game, and they ask **before the write**. The
tempting order is the other one: a game's court is frozen at the plan, so nothing either act
writes could change who is on it, and asking after the commit would not hold the transaction
open for a question about somebody else's context. It is wrong for one reason that outweighs
that — **after the commit, the score has already landed.** A `users` that cannot answer would
turn a successful entry into a `500`, and the retry a player makes is then refused with
`your_side_has_already_answered` about their own score. Asked first, the same outage is an act
that did not happen, which is the only failure this ADR's Consequences claim.

**The union is handed over sorted**, in both places. Nothing downstream could observe the
order — the answer is a mapping keyed by id — and
[ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md) §1 states its rule on the
collection rather than on what happens to be observable for exactly that reason: what is safe
today is what changes silently.

## Consequences

**Easier**

- The result conversation can name the person it is a conversation with, which is the tap
  the whole of [#314](https://github.com/Raketa02/Raketa/issues/314) was built around.
- A row of *Your games* has a distinguishing fact that is not a duration.
- The next surface that lists people you have a shared record with — a chat, a history
  screen — starts from §2 rather than re-deciding it, which is the thing ADR-0095 §7 asked
  for and left open.

**Harder**

- **`games` now depends on `users` being reachable to render a response it could
  previously render alone.** It is one set read on a port that already existed and is
  already on the search path, and a failure is a failed request rather than a nameless
  game — there is no soft answer here, because a games list that silently went anonymous
  would be indistinguishable from four erased accounts. §4's ordering is what keeps that claim
  true of the two **write** routes as well as the read.
- **Somebody will propose the card again**, and the argument will be *we already have
  `PlayerCardSource`, and the search route attaches one*. §1 is written so that proposal
  starts from the reason rather than from the field.
- **A `null` handle is a shape every client must draw**, and it is unreachable today: there
  is no erasure path in `users`, and every seat in a game came from a challenge whose
  line-up came from a search that had already dropped rows without nicknames. It is
  defensive, and the cost of it being unreachable is that nothing exercises it but a
  contract.

**Neutral**

- The contract change is **additive** — one nullable field on a shape both existing
  consumers already read — so no shipped client breaks on it.
