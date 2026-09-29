# ADR-0102 — Silence is never scored: the availability grid is required, and a blank one is absent rather than zero

- **Status:** Accepted
- **Date:** 2026-08-26
- **Amended 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)**: the grid becomes hours per weekday (07:00–23:00). A blank week is still absent, never zero, and onboarding still needs at least one hour.

## Context

[`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md)
§10 is the property that lets the matcher ship: a term with no evidence returns `NoEvidence`,
is dropped from the sum, and the remaining weights renormalise. **No record is not a bad
record.** [ADR-0098](0098-matcher-demands-as-executable-contracts.md) sharpened it into an
invariant every later context inherits — *a gate may be honestly empty; a term may never be
honestly neutral* — where the test is whether a zero would be **measured** or **invented**.

Resolving [#167](https://github.com/Raketa02/Raketa/issues/167) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
found that one field already breaks it, in shipped code, and that the breach lands exactly
where it does the most damage — at the quality floor, which decides whether a player is shown
somebody or shown an apology.

**A player may commit a profile with nothing ticked on the 7 × 3 availability grid**, and the
same fact currently carries three different meanings:

| Where | What blank means | Worth |
|---|---|---|
| `backend/app/modules/player_profile/domain/availability.py` | *"no preference … it scores no overlap"* — a zero | −15 of 100 |
| [ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md) | the searcher's availability term is `NoEvidence` | the term stands down |
| The phrase itself | *any time suits me* | +15 of 100 |

The root [`CONTEXT.md`](../../CONTEXT.md) carries the first reading as a stated invariant of
the Player profile context. The spread between the readings is roughly fifteen points of a
hundred — comfortably enough to move a candidate across the floor in either direction, on a
question nobody was ever asked.

This is not a matcher bug that can be fixed inside the matcher. The scoring rule and the
onboarding form disagree about what an empty form field is, and only one of them can be right.

## Decision

**We will require at least one slot, and we will treat a blank grid as absent rather than as
zero.**

Three parts, and they are one decision:

1. **The grid becomes required at profile commit.** At least one ticked cell of the twenty-one.
   A commit with none is refused with a code, the same way a tag selection below its floor is
   refused today. This is a sport application; when a player usually plays is not optional
   information.

2. **The minimum is exactly one.** One tick is a real answer — a player who only ever plays
   Saturday mornings must be able to say precisely that, and the near-total absence of overlap
   that follows is a **measured** near-zero, which is all the invariant asks for. A higher
   minimum would be the platform telling people what their week looks like.

3. **Where a blank grid is nevertheless encountered, the availability term returns
   `NoEvidence`.** Requiring the field at commit does not make blank grids impossible: a player
   may clear their grid afterwards through `AvailabilityChanged`, and profiles committed before
   this record may already hold one. The matcher's standing rule is therefore *blank means we do
   not know*, and it is the rule the engine is built to, not a migration artefact.

**`availability.py`'s sentence "it scores no overlap" is wrong and is withdrawn**, along with
the matching clause in the root `CONTEXT.md`. Its neighbour — *"an unanswered field is never a
negative filter"* — **survives and is strengthened**: requiring the field removes the unanswered
case, so nothing has to be read negatively in the first place.

The rejected readings, and why:

- **Blank scores no overlap** (today's code) invents a zero out of silence. The player did not
  say they are never free; they said nothing. This is the precise move
  [ADR-0098](0098-matcher-demands-as-executable-contracts.md) forbids, and it costs the quietest
  player fifteen points for their quietness.
- **Blank means any time** rewards saying nothing with a perfect score on the term, which makes
  the empty grid the optimal play and poisons the one signal that says *a game between you two
  can actually be arranged*.

## Consequences

- **The matcher's strongest day-one honesty claim survives contact with a real form.** Five of
  the eight terms work against the backend as it stands; a term that fabricates a zero out of an
  unanswered question would have been the first counter-example to §10, in the shipped code,
  before the matcher existed.

- **Onboarding gets stricter, and that is a real cost.** One more thing to answer before a
  profile commits, on a flow whose completion rate nobody has measured yet. The falsifier is
  ordinary: profile-commit completion rate before and after. If requiring one tick of twenty-one
  measurably costs sign-ups, this is the record to come back to — and the fix is the form, not
  the scoring rule, because the scoring rule is right either way.

- **It is a public API behaviour change.** `CommitPlayerProfileCommand.availability` stops
  accepting an empty sequence, which is a refusal a client can now receive and must render. The
  onboarding screen has to enforce it and say why. This lands as its own implementation ticket
  across both apps; **this map decides it and does not build it.**

- **Profiles committed before the change are not migrated.** Nothing backfills a preference
  nobody expressed. They keep their blank grid, and part 3 already says what the engine does
  with one — which is why part 3 is a rule and not a transitional clause.

- **The evidence rule from [#167](https://github.com/Raketa02/Raketa/issues/167) is left with
  almost nobody to judge, on purpose.** With the grid required, every new profile produces
  evidence on every day-one term, so the *minimum evidence about a specific person* rule
  excludes no one today. It is standing insurance: the day a new term turns on, *we know nothing
  about this person* must not quietly become a passing score.

- **The three-way disagreement is now a one-way statement.** The input document's §9.3.5, this
  record and the glossary agree; the shipped docstring is the only thing left to correct, and it
  is named here so the correction is not archaeology.
