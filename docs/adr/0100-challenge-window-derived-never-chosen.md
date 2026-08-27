# ADR-0100 — The challenge window is derived from the grid the search ran on, and is never chosen

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

A challenge in
[`docs/specs/matchmaking/social-prototype-v1.html`](../specs/matchmaking/social-prototype-v1.html)
carries a **window** — *tonight*, *tomorrow*, *this weekend*, *next week*, *whenever suits* —
so the person answering knows roughly what they are agreeing to. `avWindow` at `:1300` derives
it from the searcher's availability grid, `S.mm.window` shows it as a tag on the Play screen,
and `newMU` stamps it on the match-up. **The player is never asked for it.**

The design document has no such field. Its `POST /v1/lineups` sketch (§16) carries `grid`,
`grid_updated_at` and `availability_override` and nothing that names a window. That silence
carries no weight: [ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)
**discarded §16 entirely**, and the contract is being written from scratch by
[#170](https://github.com/Raketa02/Raketa/issues/170). What survives the discard is the
question, and it is the third rule for reading these documents — *the prototype wins on
surface* — that keeps it alive rather than letting an omission delete a screen behaviour. This
record settles part of [#164](https://github.com/Raketa02/Raketa/issues/164) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**The obvious alternative is to ask.** A picker on the challenge sheet is more expressive: it
lets a player who ticked eleven slots say *actually, this weekend*. It was rejected, and the
reason is not economy of taps. A chosen window is **a second availability declaration, free to
contradict the first** — the player has just described their week to the matcher, the matcher
has ranked the entire pool against that description, and a picker then invites them to say
something else on the way out. The two can disagree, nothing reconciles them, and the
disagreement is invisible to everybody: the recipient sees *this weekend*, the engine matched
on a grid that says Tuesday evening.

Three constraints already stand, and each says something about where this can live.

- **[ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md):** *availability overlap is
  evidence that a game can be arranged; it is never a proposed time.* A window sits close to
  that line and must be argued past it, not waved past.
- **`backend/app/modules/player_profile/domain/availability.py` carries a standing refusal**,
  written to be argued with: *"The grid is never rendered to anybody as a calendar. Only the
  count of shared slots and the name of the next shared one are ever shown, because overlap is
  a fact about a pair where a calendar is a fact about a person. Nothing in this module serves
  one; the invariant is recorded here so that the first thing that tries has to argue with
  it."* **The window is the first thing trying.**
- **[ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md):** a client derives only
  by comparison. `avWindow` is a rule with thresholds — `≤ 2` slots on one day, `≥ 12` slots
  overall — so no client may compute it, whatever it would cost the backend to serve it.

The same module's docstring adds a fourth: *"nothing in this module has a duration, a date or a
timezone in it."* `TODAY` and `TOMORROW` are relative to what day it is.

## Decision

We will **keep the window, derive it, and never ask for it.**

1. **Derived, never chosen.** There is no window picker anywhere. A player changes their window
   by changing their grid, which is the same act that changes their matches — one control, one
   meaning.

2. **Its source is the grid the search actually ran on**, including a rung-A
   `availability_override` under ADR-0099 — never the profile grid, and never a third grid. The
   window's whole job is to say what the person answering is agreeing to, and that must be the
   week the match was found in.

3. **Each relaxation rung offer carries its own window** beside its real candidate count. ADR-0099
   made rungs offered rather than applied precisely so a player can see what widening costs
   before taking it; a rung that silently moves a challenge from `WEEKEND` to `THIS_WEEK` is
   part of that cost.

4. **The function is `window_of(grid, today: IsoWeekday) -> Window`**, and it lives beside
   `AvailabilityGrid` in `player_profile`. `IsoWeekday` is kernel vocabulary that module already
   imports, and is neither a date nor a timezone — the **caller** resolves what day it is, so
   the module's negative space is intact.

5. **The window crosses the wire as a code**, never a sentence:
   `TODAY | TOMORROW | WEEKEND | THIS_WEEK | ANY`. *"Tonight"* is the client's word
   ([ADR-0022](0022-kernel-negative-space-and-constant-homes.md)).

6. **Two constants, with a falsifier of their own kind.** `WINDOW_SINGLE_DAY_MAX_SLOTS = 2` and
   `WINDOW_ANY_MIN_SLOTS = 12`, adopted from the prototype as starting positions. Their
   falsifier is **not** return rate — a window is a label, not a ranking input. It is **the rate
   at which a challenge is answered with a counter-proposal outside its stated window**: if
   `WEEKEND` challenges are counter-proposed to a Tuesday as often as `THIS_WEEK` ones are, the
   label carries no information and is **removed rather than tuned**, which is the disposal rule
   §24 already applies to a relaxation rung that never converts. Measurable only once `matches`
   exists.

7. **The weekend is Saturday and Sunday, hardcoded, and recorded as a locale assumption rather
   than a constant.** It is not a number to tune. Its falsifier is the first shard where the
   weekend is somewhere else.

8. **The matcher never emits a window.** It matches players and stops. The backend derives the
   window at challenge creation from the search's own grid; **storing it on a challenge is a
   demand on `matches`**, alongside the origin key ADR-0098 already made non-nullable.

9. **The argument against the calendar refusal is recorded in `availability.py` itself** when
   the function is built, next to the invariant it answers — not in a spec that the next reader
   will not find. The argument: **a window is strictly coarser than what the module already
   permits to be shown.** The name of the next shared slot renders as *"Thursday evening"*,
   which is more precise than *"this weekend"*. A rule that already allows the sharper
   disclosure cannot forbid the blunter one.

## Consequences

**A player cannot say *this weekend* while their grid says Tuesday.** This is the cost, and it
is real: expressiveness is genuinely lost. It is accepted because the alternative is two
records of the same fact with no reconciliation, and because the grid is the record the whole
engine reads — a product that lets you tell the matcher one thing and your opponent another has
two availabilities and no truth.

**The stale grid gets a second consequence, which makes the "Keep these times?" sheet worth
more.** A grid three months old already quietly ruins every match it touches; now it also
mislabels every challenge sent from it. The sheet that offers to save a changed search grid
back to the profile is the mitigation, and it is specced in the same resolution.

**The window is coarse at the boundaries and stays coarse.** A player ticking Thursday evening
at nine on Thursday night gets `TODAY`. The label is a preference summary rather than a slot,
the challenge carries its own creation time, and the players agree the actual hour between
themselves — which ADR-0099 already established is the only place it can be agreed.

**`player_profile` gains a function that `matchmaking` and `matches` both call.** That is the
right home — the grid's vocabulary is there, and the alternative was a fourth spelling of the
week — but it means a context with no stake in the outcome owns a rule two other contexts
depend on. It is one pure function over a value object, which is the cheapest form that
dependency takes.

**`IsoWeekday` in, no date.** Callers must resolve *today* in the player's own timezone before
calling. That work does not disappear; it moves to a caller that already has a request context,
and it stays out of a module that has spent its whole existence keeping dates out.

**A rung offer gets wider.** Every rung now carries a window as well as a count, which is more
contract surface and one more thing a client renders. Cheap, and it is the difference between
offering a widen and offering an informed widen.

**Nothing here is reversible cheaply once challenges exist.** A stored chosen window cannot be
un-chosen: the moment a `matches` row holds a player-picked window, deriving it instead means
either discarding real answers or carrying two provenances forever. That asymmetry is why this
is a record rather than a spec line.
