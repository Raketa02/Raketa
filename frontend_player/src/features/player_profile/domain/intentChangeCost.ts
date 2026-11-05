/**
 * **What an answer on You › *What kind of game* costs**, said before the tap
 * ([ADR-0201](../../../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
 * §6, [#742](https://github.com/Raketa02/Raketa/issues/742)).
 *
 * Since Q127 a change of intent takes the player off the cards they have not answered of a kind
 * they dropped, in every group, and keeps their yeses (§3). So an answer either **drops** a kind,
 * and the line says how many of its cards go, or **widens** to *Either suits me*, and the line
 * says nothing goes:
 *
 * - **To a single kind**, from the other kind or from *Either suits me*, the other kind goes, and
 *   the count is that kind's: *Either suits me* → *For fun* counts the competitive cards.
 * - **To *Either suits me***, from one kind, that kind is kept and the other added. No count.
 * - **The answer held** costs nothing, and **an undeclared sport** deals nothing, so no answer to
 *   it takes anything away — and nothing is counted for it.
 *
 * A card's kind is a **Mode** — `GameKind`, the deck's own two — and never a Play intent with one
 * value taken out: an intent is a standing declaration with three values, a kind is one game's,
 * and the glossary keeps them separate types so confusing them is a compile error.
 */

import type { GameKind } from '@/features/proposals/types';
import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayIntentDeclarations } from './PlayerProfileSurface';

/**
 * **How many cards each kind deals the player now in one sport, summed over their groups** —
 * each group's number exactly the count its switch shows. A kind the intent does not show is 0.
 */
export type DeckCounts = Readonly<Record<GameKind, number>>;

export type IntentChangeCost =
  | {
      readonly change: 'drops';
      /** The kind that goes. */
      readonly kind: GameKind;
      /** `undefined` while the counts are not in hand — loading, or failed — and never 0. */
      readonly count: number | undefined;
    }
  | { readonly change: 'widens'; readonly keeps: GameKind; readonly gets: GameKind };

/** The kind an answer of one kind names. */
const KIND_NAMED: Readonly<Record<Exclude<PlayIntent, 'NO_PREFERENCE'>, GameKind>> = {
  COMPETITIVE: 'competitive',
  FOR_FUN: 'forFun',
};

const THE_OTHER: Readonly<Record<GameKind, GameKind>> = {
  competitive: 'forFun',
  forFun: 'competitive',
};

/**
 * The cost of answering `answer` while `held` is the answer, or `undefined` where it changes
 * nothing. `counts` is absent until `GET /players/me/deck-counts` has answered, and after it fails.
 */
export function intentChangeCost(
  held: PlayIntent | undefined,
  answer: PlayIntent,
  counts: DeckCounts | undefined,
): IntentChangeCost | undefined {
  if (held === undefined || held === answer) return undefined;
  if (answer === 'NO_PREFERENCE') {
    if (held === 'NO_PREFERENCE') return undefined;
    const keeps = KIND_NAMED[held];
    return { change: 'widens', keeps, gets: THE_OTHER[keeps] };
  }
  const goes = THE_OTHER[KIND_NAMED[answer]];
  return { change: 'drops', kind: goes, count: counts?.[goes] };
}

/**
 * **The sport whose cards are counted** — the open row's, while it is declared. No row open, or an
 * undeclared one, counts nothing: its answers cost nothing, so there is no request to send.
 */
export function sportToCount(
  open: Sport | undefined,
  declarations: PlayIntentDeclarations | undefined,
): Sport | undefined {
  return open !== undefined && declarations?.[open] !== undefined ? open : undefined;
}
