/**
 * **Every sentence Discovery's rows say** — New in Raketa
 * ([#801](https://github.com/Raketa02/Raketa/issues/801); the words
 * [§31.1 and §31.7](../../../../../docs/specs/matchmaking/the-words.md#317-new-in-raketa)): the row's
 * heading and its *See all ›*, the tile's tag, sports and *Joined …*, and See all's title, pill and
 * empty line; Same competitive level ([#802](https://github.com/Raketa02/Raketa/issues/802); the
 * words [§31.5 and §31.6](../../../../../docs/specs/matchmaking/the-words.md#315-same-competitive-level--the-card)):
 * the card's pairing, *EVEN*, the bar's *YOU*, *N sports ›*, and the comparison sheet with its gap; and
 * Same vibe ([#803](https://github.com/Raketa02/Raketa/issues/803); the words
 * [§31.8](../../../../../docs/specs/matchmaking/the-words.md#318-same-vibe)): the tile's %, *+N more*,
 * the sheet's title and identity row. The round button's words are `friends'`, the bands' names
 * onboarding's (`BAND_NAMES`), *6 things in common* and the tags' own `shared/vocabulary`'s — the
 * request card says the count too, and one spelling serves both.
 *
 * ## Calls, for the product owner to overrule
 *
 * §31 gives every drawn word here but these, written in by #803:
 *
 * - **See all's spoken name**, *See all same vibe players*, for #801's reason below.
 * - **A tile's spoken name** reads it in the order drawn — *karol.t, 98%, 6 things in common* — and
 *   then **every tag they share**, *: Stays for a drink, Plays to win, …*, the ones under *+N more*
 *   too: a tag the tile draws is a clause in its name (the tag row's rule), and which ones are drawn
 *   is the screen's width, not a fact about the two of them.
 * - **See all with nobody**, *Nobody who shares your tags plays squash yet*, and with nobody at all,
 *   *Nobody shares your tags right now* — §31 words neither.
 * - **The pill's hint**, *Shows who shares your tags in another sport*.
 * - **The sheet's close**, *Close You and karol.t*, as the comparison sheet's.
 *
 * And these, written in by #802:
 *
 * - **See all's spoken name**, *See all players at your level*, for #801's reason below.
 * - ***N sports ›*'s spoken name**, *Compare with zofia.b in 2 sports* — it opens the comparison.
 * - **The pairing's spoken name**, *91% even in padel, You 2,71, zofia.b 2,69*, read in the order
 *   drawn — with no gap since the card stopped drawing it (#821); the bar's, *You 2,71 · zofia.b
 *   2,69*, the sheet's own line.
 * - **See all with nobody to compare**, *Nobody to compare in squash yet*, and with nobody at all,
 *   *Nobody to compare with right now* — §31 words neither: a sport the read offered can leave nobody
 *   by the time it is read.
 * - **The pill's hint**, *Compares everybody in another sport* (the mechanics §6.7's *re-compares*).
 *
 * And these, written in by #801:
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
import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import type { SportPillWords } from '@/shared/ui';
import { socialTagName, thingsInCommon } from '@/shared/vocabulary/socialTagPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import type { JoinedAgo, Joiner } from '../domain/joiner';
import type { LevelComparison, LevelGap } from '../domain/sameLevel';
import type { SameVibePlayer } from '../domain/sameVibe';
import type { SeeAllSport } from '../domain/seeAll';

export const DISCOVERY_COPY = {
  /** Every See all pill's first choice. */
  all: 'All',
  newInRaketa: {
    /** FOR YOU's line (#820) — its title, and what it is named: never *Rakieta*. */
    line: 'New in Raketa',
    seeAll: 'See all',
    seeAllLabel: 'See all new players',
    /** The volt tag, top-left on every tile. */
    tag: 'NEW',
    /** See all's title. */
    title: 'New in Raketa',
    back: 'Back to Home',
    pillHint: 'Shows new players in another sport',
    nobodyAtAll: 'Nobody new right now',
    reading: 'Reading new players…',
  },
  sameLevel: {
    /** FOR YOU's line (#820) — its title: the row was *SAME COMPETITIVE LEVEL PLAYERS*. */
    line: 'Players at your level',
    seeAll: 'See all',
    seeAllLabel: 'See all players at your level',
    /** See all's title — bold, two lines where it wraps (home rows 12). */
    title: 'Same competitive level players',
    back: 'Back to Home',
    /** The reader's side of the pairing. */
    you: 'You',
    /** Under the %, grey caps — always this word, whatever the % (§31.5). */
    even: 'EVEN',
    /** The bar's tall mark. */
    youMark: 'YOU',
    /** The gap when it rounds to 0,00 — the comparison sheet's, since the card says no gap (#821). */
    sameLevel: 'Same level',
    pillHint: 'Compares everybody in another sport',
    nobodyAtAll: 'Nobody to compare with right now',
    reading: 'Reading players at your level…',
  },
  sameVibe: {
    /** FOR YOU's line (#820) — its title: the row was *SAME VIBE PLAYERS*. */
    line: 'Players with your vibe',
    seeAll: 'See all',
    seeAllLabel: 'See all same vibe players',
    /** See all's title. */
    title: 'Same vibe players',
    back: 'Back to Home',
    pillHint: 'Shows who shares your tags in another sport',
    nobodyAtAll: 'Nobody shares your tags right now',
    reading: 'Reading same vibe players…',
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

/**
 * **The gap in words** (§31.6) — *0,02 below you*, *0,09 above you*, *Same level* — on the comparison
 * sheet's blocks; the card says none since #821. A switch over the kind, so a gap with no words fails
 * to compile.
 */
export function gapLine(gap: LevelGap): string {
  switch (gap.kind) {
    case 'below':
      return `${formatLevel(gap.gap)} below you`;
    case 'above':
      return `${formatLevel(gap.gap)} above you`;
    case 'same':
      return DISCOVERY_COPY.sameLevel.sameLevel;
  }
}

/** *2 sports* — the card's way to the comparison, its chevron drawn after it (§31.5). */
export function sportsCount(count: number): string {
  return `${count} sports`;
}

/** *Compare with zofia.b in 2 sports* — *N sports ›*'s spoken name (a call). */
export function compareLabel(nickname: string, count: number): string {
  return `Compare with ${nickname} in ${count} sports`;
}

/** *You vs zofia.b* — the comparison sheet's title (§31.6). */
export function comparisonTitle(nickname: string): string {
  return `You vs ${nickname}`;
}

/** The comparison sheet's close — named for the sheet, never just *Close* (`CloseControl`). */
export function closeComparisonLabel(nickname: string): string {
  return `Close ${comparisonTitle(nickname)}`;
}

/** *You 2,71 · zofia.b 2,69* — a block's levels (§31.6), and the bar's spoken name. */
export function levelsLine(comparison: LevelComparison, nickname: string): string {
  return `You ${formatLevel(comparison.yourLevel)} · ${nickname} ${formatLevel(comparison.theirLevel)}`;
}

/** *91% even* — a block's tag (§31.6). */
export function evenTag(percentEven: number): string {
  return `${formatPercent(percentEven)} even`;
}

/** The pairing, spoken in the order drawn (a call), with no gap (#821) — see the module note. */
export function pairingLabel(comparison: LevelComparison, nickname: string): string {
  return [
    `${evenTag(comparison.percentEven)} in ${sportInLine(comparison.sport)}`,
    `You ${formatLevel(comparison.yourLevel)}`,
    `${nickname} ${formatLevel(comparison.theirLevel)}`,
  ].join(', ');
}

/** *Nobody to compare in squash yet* — See all, a sport that leaves nobody (a call). */
export function nobodyToCompareIn(sport: Sport): string {
  return `Nobody to compare in ${sportInLine(sport)} yet`;
}

/** *+2 more* — the dashed tag in a tile's last place, for the tags it had no room for (§31.8). */
export function moreTags(count: number): string {
  return `+${count} more`;
}

/** A Same vibe tile, spoken in the order drawn, then every tag the two share (a call). */
export function vibeTileLabel(player: SameVibePlayer): string {
  const said = [
    player.nickname,
    formatPercent(player.vibePercent),
    thingsInCommon(player.inCommon),
  ];
  const tags = player.sharedTags.map(socialTagName);
  return tags.length === 0 ? said.join(', ') : `${said.join(', ')}: ${tags.join(', ')}`;
}

/** *You and karol.t* — the vibe sheet's title (§31.8). */
export function vibeTitle(nickname: string): string {
  return `You and ${nickname}`;
}

/** The vibe sheet's close — named for the sheet, never just *Close* (`CloseControl`). */
export function closeVibeLabel(nickname: string): string {
  return `Close ${vibeTitle(nickname)}`;
}

/** *Nobody who shares your tags plays squash yet* — See all, a sport that leaves nobody (a call). */
export function nobodySharesYourTagsIn(sport: Sport): string {
  return `Nobody who shares your tags plays ${sportInLine(sport)} yet`;
}

/** A choice's name on the pill — *All*, or the sport's. */
function choiceName(choice: SeeAllSport): string {
  return choice === 'all' ? DISCOVERY_COPY.all : sportLabel(choice);
}

/** A See all pill's words — *All* and each sport by its name — with the row's own hint. */
function pillWords(pillHint: string): SportPillWords<SeeAllSport> {
  return {
    sportName: choiceName,
    pillLabel: (choice) => `Sport: ${choiceName(choice)}`,
    pillHint,
  };
}

export const NEW_IN_RAKETA_PILL_WORDS = pillWords(DISCOVERY_COPY.newInRaketa.pillHint);
export const SAME_LEVEL_PILL_WORDS = pillWords(DISCOVERY_COPY.sameLevel.pillHint);
export const SAME_VIBE_PILL_WORDS = pillWords(DISCOVERY_COPY.sameVibe.pillHint);
