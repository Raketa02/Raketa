/**
 * **Every sentence New in Raketa says** ([#801](https://github.com/Raketa02/Raketa/issues/801); the
 * words [§31.1 and §31.7](../../../../../docs/specs/matchmaking/the-words.md#317-new-in-raketa)) —
 * the row's heading and its *See all ›*, the tile's tag, sports and *Joined …*, and See all's title,
 * pill and empty line. The round button's words are `friends`'.
 *
 * ## Calls, for the product owner to overrule
 *
 * §31 gives every drawn word here but these, written in by #801:
 *
 * - **See all's spoken name**, *See all new players* — three *See all*s on Home would otherwise be one
 *   name for three places (the row frame's rule).
 * - **A tile's spoken name** reads it in the order drawn: *bartek.l, Padel 2,35, Badminton 2,10,
 *   Joined 2 days ago*. *NEW* is not read: every tile says it.
 * - **See all with nobody at all**, *Nobody new right now* — §31.7 words a sport that leaves nobody,
 *   and *All* can too, once everybody's 30 days ran out between the row's read and this one.
 * - **The pill's spoken name and hint**, *Sport: All*, *Shows new players in another sport*,
 *   Rankings' register (§30).
 * - **The back button's name**, *Back to Home*, Rankings' own.
 *
 * ## Read it inside a component, never at module load
 *
 * The sports' names are onboarding's, through its barrel, and that barrel reaches the shell and back
 * into this feature's components: a component that reads `DISCOVERY_COPY` at module scope finds it
 * undefined when this module is the first loaded (`groups`' #800 gotcha, `friendsCopy`'s).
 */

import { sportInLine, sportLabel } from '@/features/onboarding/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import type { SportPillWords } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { JoinedAgo, Joiner, SeeAllSport } from '../domain/joiner';

export const DISCOVERY_COPY = {
  newInRaketa: {
    /** Drawn uppercase by the row frame: *NEW IN RAKETA* — never *Rakieta*. */
    heading: 'New in Raketa',
    seeAll: 'See all',
    seeAllLabel: 'See all new players',
    /** The volt tag, top-left on every tile. */
    tag: 'NEW',
    /** See all's title. */
    title: 'New in Raketa',
    back: 'Back to Home',
    all: 'All',
    pillHint: 'Shows new players in another sport',
    nobodyAtAll: 'Nobody new right now',
    reading: 'Reading new players…',
  },
} as const;

/** *Padel 2,35* — one sport on a tile, its dot drawn before it. */
export function sportLevelLine(sport: Sport, level: number): string {
  return `${sportLabel(sport)} ${formatLevel(level)}`;
}

/**
 * *Joined 2 days ago* — the tile's last line (§31.7). A switch over the rung, so a rung with no words
 * fails to compile.
 */
export function joinedLine(ago: JoinedAgo): string {
  switch (ago.kind) {
    case 'today':
      return 'Joined today';
    case 'yesterday':
      return 'Joined yesterday';
    case 'days':
      return `Joined ${ago.days} days ago`;
    case 'lastWeek':
      return 'Joined last week';
    case 'weeks':
      return `Joined ${ago.weeks} weeks ago`;
  }
}

/** A tile, spoken in the order it is drawn — see the module note. */
export function tileLabel(joiner: Joiner, joined: string): string {
  return [
    joiner.nickname,
    ...joiner.sports.map((held) => sportLevelLine(held.sport, held.level)),
    joined,
  ].join(', ');
}

/** *Nobody new plays squash yet* — See all, a sport that leaves nobody (§31.7). */
export function nobodyNewPlays(sport: Sport): string {
  return `Nobody new plays ${sportInLine(sport)} yet`;
}

/** A choice's name on the pill — *All*, or the sport's. */
function choiceName(choice: SeeAllSport): string {
  return choice === 'all' ? DISCOVERY_COPY.newInRaketa.all : sportLabel(choice);
}

/** The pill's words — *All* and each sport by its name. */
export const SEE_ALL_PILL_WORDS: SportPillWords<SeeAllSport> = {
  sportName: choiceName,
  pillLabel: (choice) => `Sport: ${choiceName(choice)}`,
  pillHint: DISCOVERY_COPY.newInRaketa.pillHint,
};
