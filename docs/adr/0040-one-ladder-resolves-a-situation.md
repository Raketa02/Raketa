# ADR-0040 — One ladder resolves a situation; every other vocabulary projects off it

- **Status:** Accepted
- **Date:** 2026-08-20

## Context

The Now section arrived carrying what looked like three parallel state vocabularies over one
match record, and turned out to be four.

| Vocabulary | Size | Produced by | Read by |
| --- | --- | --- | --- |
| Context keys | 33 (after [ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)–[0033](0033-settlement-and-occupancy-are-independent.md)) | `matchState`'s fifteen-rung ladder | the card payload |
| Tags | 17 | the context's `tag` field | the status pill |
| `be` values | 15 | the context's `be` field | **nothing** |
| LIFE9 states | 9 | `lifeOf` — an independent ladder | *"the club console"* (`now-section-domain-spec.md` §D.15) |

The fourth is the only one that ships today. `backend/app/engines/matchmaking.py` defines
`MatchPhase` — `forming`, `locked`, `cancelled` — read as the ranker's hard filter, alongside
`SeatState` and `CourtHold`. Its docstring states its own terms: *"**Borrowed vocabulary.** …
This engine reads them; Matches will define them"*, and it declines to say more than it can
know — *"inventing members it can never tell apart would be this file guessing at a lifecycle
Matches will own."* Whatever is decided here is owed to a consumer already in the tree.

Three findings decide it.

**The cross-application contract has no counterparty.** §D.15 calls `lifeOf` *"the
cross-application contract"* and the nine states *"shared verbatim with the console"*.
`frontend_club/src/features/` contains one directory, `_template`; `backend/app/modules/` holds
`auth`, `rating` and `users`. There is no console feature, no Matches module, and no reader of
the nine anywhere in this repository. The contract is with a party that does not exist.

**The V36 claim that the tags are derived from the nine is false, and executing the prototype
says so.** The state-table research ran the resolver over 280 224 records
([`docs/specs/now/research/state-table.md`](../specs/now/research/state-table.md) §6.5): `lifeOf`
is an independent nine-rung ladder over the same facts, *"nothing in `matchState` reads it and
nothing in `lifeOf` reads `matchState`."* It also ignores `m.forced`, so on the one screen that
renders every context, `forming`, `cancelledIncomplete` and `playedShort` all report `HELD`. Two
derivations of one record, already disagreeing, before anybody built on them.

**They cannot be derived from each other, and not because anybody was careless.** The signatures
differ. `lifeOf(m, now)` takes no viewer; `matchState` takes one — rung 6 is
`!mySeat(m) && waitlists.includes(m.id)`, and
[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) already decided that *"the leaver's
card is the match's card rendered for somebody who used to hold a seat."* One is match-absolute,
the other viewer-relative. A lookup table from 33 keys to 9 states is not merely untested; for
`waitlisted` it is not well-defined, because the key alone does not say what the match is doing.

That last fact also bounds the problem. **Exactly one rung of fifteen reads the viewer.** Every
other viewer-dependence in the model is rendering and leaves the key alone: the non-member money
rewrite runs after the ladder (`UI` §B6.1), ADR-0030's leaver is the same key rendered for a
different audience, and the result affordance is suppressed for a standby player or a leaver
without moving them off `needsResult`.

The alternatives, and why they lost:

- **Bless the nine as canonical and make the 33 a presentation over them.** The 33 carry
  distinctions the nine cannot express, and the model paid for them deliberately: `heldStale`
  exists as a separate rung because *"a player told the wrong reason once stops believing the
  right ones."* Folding `heldReleased` and `heldStale` into `RELEASED` is that sentence
  reversed.
- **Keep two ladders and add a cross-application consistency suite.**
  [ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md) ranks two implementations
  of one rule as the first failure mode and records it having already happened once. A suite
  that catches disagreement is weaker than a structure that cannot produce it.
- **Give the console its own projection and retire the nine.** Nearly right, except that
  *retire* overstates what is there: no console reads them, so there is nothing to retire and
  no reason to bless nine particular names today.

## Decision

**We will keep one ladder, and give it an optional viewer.**

`situation(match, viewer | None, now) -> Situation` is the single resolver, over a single
enumeration of **33 members**. Called with a viewer it may yield `waitlisted`; called without,
it cannot. **The absolute form is the same function with the parameter absent, not a second
derivation** — so there is nothing for a consistency suite to catch, because there is nothing
that could disagree.

**`waitlisted` is the one situation only a viewer can be in.** That is a documented property of
the enumeration, not an accident of rung 6's position. A second viewer-reading rung would
re-open the split this ADR closes, and adding one is a decision, not a refactor.

**Everything else that varies by audience is rendering, and stays downstream of the resolver
where it already sits:** the non-member money rewrite, ADR-0030's leaver card, and the
suppression of the result affordance for anybody who did not play.

**We will make every other vocabulary a total projection off `Situation`, owned by the consumer
that needs it.** A projection is a table from all 33 members to the consumer's own smaller set,
spelled in the owner's words, asserted exhaustive at module load. It is never a second ladder
over the record.

- **`MatchPhase` keeps its three members and becomes the first projection.** It stops being
  borrowed vocabulary awaiting an owner; `LOCKED` continues to cover *"a match being played and
  one already played"* for exactly the reason its docstring gives — matchmaking cannot join
  either. The docstring's *"Matches will define them"* becomes a citation of this ADR. That is
  a `backend/` edit and is not made here.
- **`be` is deleted.** Fifteen values, produced by every context, read by nothing in 7 334
  lines. It does not reach production, the glossary, or the contract.
- **LIFE9 is neither blessed nor retired.** It is the club console's projection, and it will be
  written when a console screen asks for it, by the session building that screen, off the 33.
  No ADR fixes nine names today.

**We will not ship the absolute situation on the player surface.**
[ADR-0016](0016-modular-monolith-two-api-surfaces.md) gives the console its own surface, and the
console's projection ships there when the console exists. This is deliberately **the boundary of
[ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md)'s rule**: that rule ships
fields with no reader because *installed phones cannot be forced to update*, and a web console
is updated by deploying it. A field with no reader is a cost, and 0038 bought it with an
argument that does not reach here.

**We will make the generated type the fence, and narrow ADR-0021 accordingly.** ADR-0021
promised *"a cross-application contract suite: for every canonical state, both clients' rendered
state must equal the server's"* — a suite that presumes clients derive. Under this decision they
do not. The enumeration crosses as a generated union (`make gen-api`, [ADR-0006](0006-backend-owns-api-contract.md)),
so a client missing a row for a situation is a **compile error in an exhaustive switch, in that
client's own build**, needing no session that touches two apps. On the backend, every projection
asserts exhaustiveness at module load — the pattern `now-section-domain-spec.md` §E.2 already
asked for on the tone enum. **ADR-0021 is narrowed on this one point and stands otherwise.**

## Consequences

**Easier**

- The failure ADR-0021 ranks first becomes unreachable rather than tested for. There is one
  ladder, so two ladders cannot drift.
- The club console cannot describe a match differently from the player app, because it has no
  derivation of its own to disagree with — only a table off the same answer.
- `MatchPhase`, `SeatState` and `CourtHold` stop being borrowed against an unwritten future.
  The one of them this ADR reaches gets an owner and a definition.
- A new coarse vocabulary is cheap and safe: a table and an exhaustiveness assertion, with no
  argument about which ladder is authoritative.
- Deleting `be` removes fifteen values that would otherwise have been preserved by a future
  session on the grounds that somebody must have meant something by them.

**Harder**

- **Every client that renders a match carries a 33-arm exhaustive switch.** That is the fence
  working, and it is still 33 arms.
- **Adding a rung to the ladder is now a breaking change against every projection and every
  client table at once.** Correct — a new situation genuinely is a new thing to say — but the
  cost per rung has gone up, and the ladder is a place where rungs get added.
- **The console pays its 33-row table before it renders anything**, and cannot crib one from
  the prototype, because the prototype's nine are a different derivation rather than a
  projection.
- **The one-viewer-rung rule is enforced by review, not by types.** The signature permits any
  rung to read the viewer. A second one added quietly re-opens the split, and nothing fails.
- **ADR-0021's suite is narrowed before it was ever built.** If a client ever does hold a rule,
  the fence described here does not reach it and 0021's argument has to be made again from the
  start.
- **`lifeOf` was the only written sketch of what a backend-facing vocabulary looks like.**
  Declining to bless it means the console's projection starts from a blank page, with the
  research file as the only record that nine states were once proposed.
