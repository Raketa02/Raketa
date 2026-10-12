/**
 * **The You tab's words this feature owns** — `the-words.md` §27, the record's rows and the
 * two read-only screens ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 *
 * The passport is the result card once per rating and the reliability screen is the record
 * card under a ring, so their sentences are the result's and `recordPresentation`'s, cited.
 * What is new is small on purpose: the two rows' titles and live lines, the passport's chip
 * and its two cards, the band said in full beside the figure, and the one sentence a new player
 * is told.
 */

import { sportLabel } from '@/features/onboarding/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import type { TagVariant } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { RatedSport, ReliabilityFigure } from '../domain/playerRecord';

import {
  OWN_RECORD_TITLE,
  PLAYER_SCORE_BLOCK,
  reliabilityHead,
  reliabilityMark,
  scorePillLabel,
} from './recordPresentation';

// --- the rows -----------------------------------------------------------------------------------

export const SKILL_PASSPORT_TITLE = 'Skill passport';

/** The block's own word for the number, cited — *Score* beside a Level would read as a rating. */
export const PLAYER_RELIABILITY_TITLE = PLAYER_SCORE_BLOCK;

/** The sheet's title about yourself, cited: the row opens exactly that sheet. */
export const HOW_OTHERS_SEE_YOU_TITLE = OWN_RECORD_TITLE;

export const HOW_OTHERS_SEE_YOU_LINE = 'Your player record, as a stranger reads it';

/** What pressing the header card does — the door its one press is. */
export const OPENS_OWN_RECORD_HINT = `Opens ${OWN_RECORD_TITLE.toLowerCase()}`;

/** `Padel 2,71 · Tennis 3,10` — one clause per rating, in the registry's order. */
export function passportLine(ratings: readonly RatedSport[]): string {
  return ratings
    .map(({ sport, level }) => `${sportLabel(sport)} ${formatLevel(level)}`)
    .join(' · ');
}

/**
 * `75 · High` · `100 · New` — **the sheet's own head, written in** (`the-words.md` §27,
 * [#660](https://github.com/Raketa02/Raketa/issues/660)).
 *
 * It read `92 of 100 · 3 things counted`, the strands behind a blended score, and *Nothing
 * counted yet* for a player with none. Everyone has a figure from the start now, so there is no
 * second arm: a player nothing has happened to reads `100 · New`.
 */
export function reliabilityLine(reliability: ReliabilityFigure): string {
  return reliabilityHead(reliability);
}

// --- the reliability screen ---------------------------------------------------------------------

/**
 * **The band said in full, beside the figure** — *Very high*, *High*, *Medium* or *Low
 * reliability*, keyed by the served band — or *New* in its place. Nothing where this build could
 * not name the band: the figure is drawn alone rather than beside a guessed word.
 *
 * It replaced the tone ladder's *Reliable*, *Holding* and *Under the bar*, which this phone worked
 * out from its own 70 and 90 and which named a bar nothing applies.
 */
export function reliabilityWord(figure: ReliabilityFigure): string | undefined {
  const mark = reliabilityMark(figure);
  return figure.isNew || mark === undefined ? mark : `${mark} reliability`;
}

export const OUT_OF_100 = 'Out of 100';

/** The two screens' spinners. The sheet's says *their*; these are your own. */
export const READING_OWN_RECORD = 'Reading your record';
export const LOADING_RATINGS = 'Loading your ratings';

/** The ring's spoken name: the block's word and the scale, exactly as the sheet's block says it. */
export function scoreRingLabel(score: number): string {
  return scorePillLabel(score);
}

/** The eyebrow under the header card's ring — the one place the ring is labelled *Score*. */
export const SCORE_LABEL = 'Score';

/**
 * **What a new player is told** — where the figure starts and what *New* beside it means. The
 * one sentence on the reliability screen that is not the record card's, drawn only while they
 * are New.
 *
 * It spoke of plans that had not settled and of a score there was none of (`the-words.md` §27,
 * retired by ADR-0195): everyone has a figure from the start now, and *New* is the word for a
 * figure nobody has tested yet. It names no price and no filter — the explanatory cards stayed
 * gone (`the-you-screen.md` §3.2), and the counts under it are the account.
 */
export const NEW_PLAYER_NOTE =
  'Everyone starts at 100. Yours reads New until you’ve played 3 games through.';

// --- the passport -------------------------------------------------------------------------------

/**
 * The status chip across a card's top — a `Tag`, not a row, because a list of three cards is
 * scanned by its chips. On-dark for an Initial estimate, amber while calibrating (reversible,
 * not yet settled), mint once stable; a status this build has no words for is drawn plainly,
 * as `ratingStatusLabel` draws its label.
 */
export function statusChipVariant(status: string): TagVariant {
  if (status === 'calibrating') return 'warn';
  if (status === 'stable') return 'ok';
  return 'onDark';
}

export const ADD_A_SPORT = 'Add a sport';
export const ADD_A_SPORT_BODY = 'One questionnaire, one rating. Nothing you already hold changes.';

/** The chip that begins a pass of one sport (ADR-0179 §3). */
export function rateSportChip(sport: Sport): string {
  return `Rate ${sportLabel(sport)}`;
}

export const THE_LADDER = 'The ladder';

/** `Established · you (padel, squash)` — the band's name, and the player's sports on that rung. */
export function ladderRung(bandName: string, sports: readonly Sport[]): string {
  if (sports.length === 0) return bandName;
  return `${bandName} · you (${sports.map((sport) => sportLabel(sport).toLowerCase()).join(', ')})`;
}
