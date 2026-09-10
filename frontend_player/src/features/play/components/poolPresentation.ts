/**
 * Everything the pool says, and the ladder's own vocabulary — **the one screen either belongs
 * to** ([#272](https://github.com/Raketa02/Raketa/issues/272)).
 *
 * The control labels are `searchPresentation`'s, because a rung's *label* is the search's
 * vocabulary and is written from `RelaxationAsk` like a window is written from `Window`
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §17). What is here is
 * what the **screen** says around them: what the list is worth, what a rung costs, what is
 * left when there is nothing to offer, and the standing statement a taken rung leaves in the
 * header.
 *
 * ## Three refusals hold this file together
 *
 * **The count is never a delta.** `candidatesAboveFloor` is the total who would clear the
 * floor at a rung, and subtracting the rows on screen from it is the arithmetic error
 * `run_shortlist_search.py` names by hand — two populations, one of which is not even a
 * superset. So the copy is *"{n} to choose from"* and never *"{n} more"*
 * ([#223](https://github.com/Raketa02/Raketa/issues/223) §1).
 *
 * **The rung's letter is never printed**, in any spelling. It is not a parameter of a single
 * function here, which is the same protection `relaxationOffer` takes.
 *
 * **Nothing says *widen* to somebody who cannot.** Where the ceiling bit, the copy states the
 * reach as a fact and *what changes it* is honestly the player's times or waiting — because
 * suppressing the sentence silently would leave them staring at a short list with no account
 * of why there is nothing to do (§5).
 *
 * ## And one rule about the header
 *
 * There is no way back to the strict list: two search rows joined by `offered_by_search_id`
 * are one screen, and a player holding both would be diffing two lists to find the people that
 * differ, which is the engine's job. What replaces *back* is `takenRungLine` — a **standing
 * statement** naming the widening and the profile it did not touch — and the way out is
 * changing the ask again (§6).
 */

import { counted } from '@/shared/formatting/counted';

import type { RelaxedAsk } from '../domain/candidate';
import type { Window } from '../domain/vocabulary';

import { windowLabel } from './searchPresentation';

/** The screen's title. It says what the player is here to do, and the court says the rest. */
export const POOL_TITLE = 'Pick players';

/**
 * What this answer was worth, in one line above the ladder.
 *
 * *Clears the bar* rather than *found*, because the rows are the people above the quality
 * floor and not the people in range — the two numbers are on screen together and must not read
 * as one. `counted` carries both forms, since *1 person clear the bar* is what a hardcoded `s`
 * produces.
 */
export function poolLadderTitle(pool: {
  readonly rows: number;
  readonly radiusKmUsed: number;
}): string {
  const who =
    pool.rows === 0 ? 'Nobody clears' : counted(pool.rows, 'person clears', 'people clear');
  return `${who} the bar at ${pool.radiusKmUsed} km.`;
}

/**
 * The ladder's own body — the mechanism, and the reversibility said **before** the act.
 *
 * *For this search only* is §F1 rule 9 in the one place it matters most: taking a rung and
 * changing the saved radius are deliberately different acts, one search against every future
 * search, and a screen that let them read as the same thing would undo the reason ADR-0099
 * exists.
 */
export const POOL_LADDER_BODY =
  'The engine ranked everybody inside your radius whose week meets yours. What you asked for ' +
  'can move, for this search only:';

/**
 * What a line-up costs when the list is replaced — the other half of rule 9's reversibility.
 *
 * A widened search is a **new** search, and `POST /forecasts` refuses a four whose members did
 * not all appear in the search it cites. So somebody added off the strict list cannot be
 * carried onto the widened one, and that is said before the tap rather than discovered by the
 * court emptying itself afterwards.
 */
export const POOL_LINEUP_COST =
  'Widening runs a new search. Anybody you have added came off this one, so the court starts ' +
  'again on the new list.';

/**
 * A rung's price — **the total above the floor**, and the window if this rung would move it.
 *
 * The window clause is dropped where the rung's own window equals the pool's, because then it
 * costs nothing, and where it is a code this build has never seen, which is §3's drop: the
 * count and the label are both still true without it.
 *
 * @param poolWindow the window the search on screen ran under.
 */
export function rungCount(
  offer: {
    readonly candidatesAboveFloor: number;
    readonly window: Window | null;
  },
  poolWindow: Window | null,
): string {
  const choose = `${offer.candidatesAboveFloor} to choose from`;
  const { window } = offer;
  return window === null || window === poolWindow ? choose : `${choose} · ${windowLabel(window)}`;
}

/**
 * A rung priced at nobody, as a **sentence rather than a control**.
 *
 * ADR-0099 §5's *"its count is printed on the button"*, narrowly amended: a button that
 * provably returns an empty list is a control lying about being useful. The count is still
 * said — which is that record's own *"widening to 20 km would still find nobody is the honest
 * empty state said in a number"*, said in a sentence instead of a tap.
 */
export function zeroRungLine(offer: RelaxedAsk): string {
  const reach = offer.ask === 'TIMES' ? 'outside your week' : `at ${offer.radiusKm} km`;
  return `Even ${reach}, nobody clears the bar.`;
}

/**
 * The reach, when there is no ask left to move — **three sentences for three different
 * reasons, none of which asks for anything.**
 *
 * | | |
 * | --- | --- |
 * | the slider's ceiling bit | the reach is a fact, and the times are the other ask |
 * | a radius rung was taken | one climb per search screen, and the profile is unchanged |
 * | neither | nothing was left to offer, and what moves the pool is other people |
 *
 * The second is written from **state**: `radius_clamp` plus the rung this screen knows it
 * sent, rather than a second copy of the engine's bound — *"a rule in TypeScript is a rule a
 * second client gets wrong"*, which is why the bound lives in `_ladder` (§7).
 *
 * @param reach.tookRadiusFrom the radius the **offering** search ran at, when this list is a
 *   radius rung's answer. That is the profile's own number, because a search that took a rung
 *   is offered none — so the search that made the offer can only have been the strict one.
 */
export function terminalReachLine(reach: {
  readonly radiusKmUsed: number;
  readonly playersInRange: number;
  readonly radiusClamp: boolean;
  readonly tookRadiusFrom: number | undefined;
}): string {
  const inRange = counted(reach.playersInRange, 'player is', 'players are');

  if (reach.tookRadiusFrom !== undefined) {
    return (
      `One widening is as far as a search reaches, and your profile still asks for ` +
      `${reach.tookRadiusFrom} km. ${inRange} in range at ${reach.radiusKmUsed} km.`
    );
  }

  if (reach.radiusClamp) {
    return (
      `You are searching ${reach.radiusKmUsed} km, which is as wide as the app goes, and your ` +
      `times are the other ask. ${inRange} in range; the pool moves as people declare their weeks.`
    );
  }

  return (
    `${inRange} in range at ${reach.radiusKmUsed} km, and there is no ask left to move for ` +
    `this search. The pool moves as people declare their weeks.`
  );
}

/**
 * The header once a rung has been taken — **a standing statement, and what replaces *back***.
 *
 * It names two things in one sentence: what this list is, and what the profile still asks for.
 * The second half is the whole point — a rung is one search, and *"taking a rung and widening
 * in You stay deliberately different acts"*.
 *
 * **The added cell is not named**, on a times rung. The engine adds one slot as
 * `availability_override` for this search alone, and the control that offered it says *look
 * outside your week* rather than naming a Saturday morning; a header that named the cell would
 * be the one place in the feature that prints a slot the player never ticked.
 */
export function takenRungLine(
  taken: ({ readonly ask: 'TIMES' } | { readonly ask: 'RADIUS'; readonly radiusKm: number }) & {
    readonly profileRadiusKm: number;
  },
): string {
  return taken.ask === 'TIMES'
    ? 'Searching outside your week for this search. Your profile is unchanged.'
    : `Searching ${taken.radiusKm} km for this search. Your profile still asks for ` +
        `${taken.profileRadiusKm} km.`;
}

/**
 * What the seat this visit was opened against is holding — **said, rather than assumed.**
 *
 * The pool is opened *against a seat*, and where that seat is occupied the add is a
 * replacement. Naming whom it replaces is what keeps the act legible: the court is one screen
 * away and the player cannot see it, so a silent swap of one handle for another is a
 * destruction they would find out about afterwards.
 */
export function replacingLine(name: string): string {
  return `Whoever you add takes ${name}’s place.`;
}

/**
 * The header's count — **how many of the court's seats have somebody in them**.
 *
 * `counted` is not reached for because there is **no noun here to inflect**: *seated* is a
 * participle describing the seats, and the sentence names them nowhere. That is a fact about
 * this line rather than a licence — the same court spoken aloud does carry the noun, and
 * `courtSummaryLabel` counts it (*"3 of 4 seats filled"*). The two registers differ, and the
 * drawn one is the terse one ([#297](https://github.com/Raketa02/Raketa/issues/297)).
 */
export function poolSeatedLine(court: { readonly filled: number; readonly seats: number }): string {
  return `${court.filled} of ${court.seats} seated`;
}

/*
 * **`awaitingBalanceLine` stood here** — *Add somebody to their side and a running balance
 * appears here*, in two court shapes, promising the figure that would arrive once the far
 * half had somebody in it.
 *
 * It is removed (2026-09-09), and the header draws nothing where a reading has not landed.
 * The act it named is the entire purpose of the screen it sat on: a list of people with an
 * *Add to the court* on every row is directly beneath it, and the court above it draws its own
 * empty seats. A sentence explaining the absence, under a picture of the absence, over a list
 * offering to end it, was the screen saying one thing three times — and *hidden, never blank*
 * is the discipline every other absence on these screens already takes.
 *
 * The rule it promised against, `theirSideSeated`, is untouched: the reading is still gated on
 * somebody being across the net rather than on a full court, because a forecast over a
 * one-sided court is the engine's empty-seat assumption talking.
 */

/**
 * The control back to the court — **the pool's only way back**.
 *
 * `ShellScreen` draws no chevron and passes none through, so this is not a convenience beside
 * the platform's own gesture: it is the affordance. A noun rather than *Back*, because what it
 * returns to is the thing the header is a picture of.
 */
export const POOL_COURT_LABEL = 'Court';

/** What the pool says when the search it was opened on is no longer held. */
export const POOL_NO_RECORD_TITLE = 'This list is no longer here';

export const POOL_NO_RECORD_BODY =
  'The search it came off has gone, so there is nobody to pick from it. Running a new one ' +
  'starts a fresh court.';

/** The one act this screen offers over a row, and the wait on the list being re-read. */
export const READ_AGAIN_LABEL = 'Read the list again';

export const READING_AGAIN_LABEL = 'Checking the list is still good…';
