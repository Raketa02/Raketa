# ADR-0032 — Order is a property of the composed screen, not of the match

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

`3-enrolled_match_engine_architecture.md` §4.3 makes an interaction promise about the enrolled
strip: it **never reorders under the player's thumb**. That promise is the reason the strip is
safe to tap — a card cannot slide out from under a finger already moving toward it.

The architecture review (`5-now_screen_architecture_review.md` §B4) points out that the promise
rests on `start` being immutable, and it is not: `3.1-enrolled_match_states_and_transitions.md`
§6.4 describes a consent stage that **moves the entire match half an hour later**. If the strip
sorts on `start` and `start` can move, the strip can reorder.

Executing the prototype ([`Raketa02/Raketa#5`](https://github.com/Raketa02/Raketa/issues/5))
found the defect is real in the model and **latent in the code**: `netlify-deploy/index.html`
line 1607 sorts on `a.start - b.start`, but nothing in the file's 7 334 lines ever assigns
`m.start`. The `time_shift` consent request exists (lines 6357, 6855) and its acceptance changes
no field. So v37 has never had to honour the promise it makes.

The alternatives considered:

**Make `start` immutable — a moved match is a different match.** Clean, and it makes the sort
key trivially safe. But it turns rescheduling into cancel-and-rebook, which drags the entire
money model behind it: every seat refunded and re-paid, every commitment re-taken, and a
departure record for each player who was never going anywhere. A half-hour shift is the mildest
thing that can happen to a match and this is the most violent possible response to it.

**Sort on a separate stable key** — `enrolledAt`, or an explicit ordinal. Truthful and cheap.
But the strip stops being chronological, and chronological is the one thing it is for: the
enrolled strip answers *what is happening to me next*, and a strip ordered by when you happened
to join answers nothing.

**Compose the order server-side and ship it in the payload.** The one that keeps both `start`
mutable and the promise true — see below.

The insight the alternatives obscure is that §4.3's guarantee was never about `start` at all. It
is a statement about **when** reordering is permitted to happen, not about which values are
allowed to change.

## Decision

**We will make order a property of the composed screen rather than of the match.** `GET /now`
returns the enrolled strip as an ordered list, and that order is part of the payload. Clients
render the order they were given and do not re-derive it.

**We will sort by `start` at composition time**, ascending, so the strip stays chronological and
answers the question it exists to answer.

**We will break ties on match id**, deterministically, so two compositions over identical facts
produce identical order and a tie cannot flicker.

**We will compose only on open and on explicit pull-to-refresh — never on a live frame.** A live
frame may change a card's content, including its state, its facets and its tag; it may **never**
change a card's position. A match that moves half an hour later stays where it is until the next
composition.

This makes §4.3's promise true exactly as written, and it makes it true for a reason the player
can predict: the strip reorders when they ask it to, and at no other time.

`start` stays mutable. A moved match is the same match.

## Consequences

**A live frame can leave the strip visibly out of chronological order.** A match shifted to
15:00 continues to sit above one at 14:45 until the player refreshes. This is the cost, it is
deliberate, and it is the right side of the trade: an out-of-order strip is a cosmetic wrong
that corrects itself, a strip that reorders under a thumb is a mis-tap on a money-bearing card.

**Composition becomes a named act with a cost.** The wire contract must distinguish *compose*
(ordered, whole-screen, on open and refresh) from *update* (per-card, live). That distinction is
now a constraint on live delivery rather than a choice available to it, and it lands before that
ticket is worked.

**Both clients gain a rule they must not optimise away.** Sorting a list you were handed is the
kind of thing a client does reflexively — and `frontend_player/` and `frontend_club/` do not
share a shape, so the rule has to be stated in each. A client that re-sorts on `start` after a
live frame reintroduces the exact defect, silently, and no test on the backend can catch it.

**The order has to survive being a wire value.** It cannot be an implicit array position that a
mapper is free to re-key; if the DTO round-trips through a map or a normalised store, the order
must be carried explicitly.

**Ties on match id are stable but arbitrary.** Two matches at 14:30 are ordered by an opaque
value the player cannot predict. That is acceptable for a tie and unacceptable as a general
sort, which is why it is a tiebreak and not the key.

**This does not settle how often a client should refresh, or whether a stale composition should
expire.** A strip composed an hour ago is ordered correctly for facts an hour old, and nothing
here forces a recomposition. The timekeeper's per-match boundaries are the natural source of
that pressure and are not yet specified.
