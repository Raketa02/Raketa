/**
 * **The You tab's words this feature owns** — `the-words.md` §27, the record's rows and the
 * two read-only screens ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 *
 * The passport is the result card once per rating and the reliability screen is the record
 * card under a ring, so their sentences are the result's and `recordPresentation`'s, cited.
 * What is new is small on purpose: the two rows' titles and live lines, the passport's chip
 * and its two cards, the word the tone ladder gives a score, and the one sentence a player
 * nothing has fallen due for is told.
 */

import { sportLabel } from '@/features/onboarding/types';
import { counted } from '@/shared/formatting/counted';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import type { TagVariant } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { RatedSport, Reliability } from '../domain/playerRecord';
import type { ScoreTone } from '../domain/scoreTone';

import { OWN_RECORD_TITLE, PLAYER_SCORE_BLOCK, scorePillLabel } from './recordPresentation';

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
 * `92 of 100 · 3 things counted`, or what an absent record is.
 *
 * *Things counted* is the strands the record has — the rows the score is the mean of — and
 * never a nought: a player nothing has fallen due for has no `reliability` at all, and the
 * line says so in words rather than drawing `0 of 100` over nothing.
 */
export function reliabilityLine(reliability: Reliability | undefined): string {
  if (reliability === undefined) return NOTHING_COUNTED_LINE;
  const things = counted(reliability.strands.length, 'thing counted', 'things counted');
  return `${reliability.playerScore} of ${SCORE_SCALE} · ${things}`;
}

const SCORE_SCALE = 100;
const NOTHING_COUNTED_LINE = 'Nothing counted yet';

// --- the reliability screen ---------------------------------------------------------------------

/** The tone ladder's three steps, said — one word for each of `scoreTone`'s answers. */
export const SCORE_TONE_WORD: Readonly<Record<ScoreTone, string>> = {
  good: 'Reliable',
  neutral: 'Holding',
  poor: 'Under the bar',
};

export const OUT_OF_100 = 'Out of 100';

/** The two screens' spinners. The sheet's says *their*; these are your own. */
export const READING_OWN_RECORD = 'Reading your record';
export const LOADING_RATINGS = 'Loading your ratings';

/** The ring's spoken name: the block's word and the scale, exactly as the sheet's pill says it. */
export function scoreRingLabel(score: number): string {
  return scorePillLabel(score);
}

/** The eyebrow under the header card's ring — the one place the ring is labelled *Score*. */
export const SCORE_LABEL = 'Score';

/**
 * A player with no record, told what that is — and that it is not a low score. The one
 * sentence on the reliability screen that is not the record card's.
 */
export const NOTHING_COUNTED =
  'Nothing has fallen due for you yet — no plan has settled and nobody has asked you anything ' +
  'with a deadline. There is no score to draw, and that is not a low one.';

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
