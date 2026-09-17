/**
 * **The You tab's words this feature owns** — `the-words.md` §27, the profile's rows.
 *
 * The tab is onboarding laid out flat
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)),
 * so nearly every sentence on it is a step's own, cited — the grid's footnote, the radius'
 * reading, the location step's permission states. What is new, and here, is the tab's own
 * vocabulary: each row's title, the **live line** under it, the one line a screen gained on
 * the way from a step to a row, and the *Save* labels a step never had.
 *
 * ## A live line is drawn from a read
 *
 * The line under a row is a fact off `GET /players/me/profile` or `GET /ratings`, never a
 * template: *10 slots ticked* is the week's count, *12 km · Across your town* is the radius
 * through the step's own reading. The one static line is the area's, because the area is the
 * one fact with a single state — a profile cannot be committed without one.
 *
 * ## Two rows land with their contract, and say so
 *
 * Who you play with and Game suggestions read fields the profile read grew on
 * [#466](https://github.com/Raketa02/Raketa/issues/466) and this client reads on
 * [#472](https://github.com/Raketa02/Raketa/issues/472). Until then each row draws a line
 * naming what it is, and the screen behind it says in one `tiny` line what it is and that the
 * edit lands with the read that carries the fact — 10.1's empty-state rule, and never *coming
 * soon*. Photos, Tags and Intro drew the same lines until
 * [#471](https://github.com/Raketa02/Raketa/issues/471) read them; their live lines are below.
 */

import { sportLabel } from '@/features/onboarding/types';
import { YOU_COPY } from '@/features/shell/types';
import { counted } from '@/shared/formatting/counted';
import { intentLabel } from '@/shared/vocabulary/playIntentPresentation';
import { socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { PlayIntentRow } from '../domain/playIntentRows';
import { weekStanding } from '../domain/availabilityWeek';
import { PHOTO_CEILING, type UploadedPhoto } from '../domain/photoCollection';

import { RADIUS_LABEL, radiusFigure, radiusWords } from './radiusPresentation';

// --- the rows' titles -------------------------------------------------------------------------

export const WHAT_KIND_OF_GAME_TITLE = 'What kind of game';
export const YOUR_WEEK_TITLE = 'Your week';
/** The radius step's own label, cited. */
export const HOW_FAR_TO_LOOK_TITLE = RADIUS_LABEL;
export const WHERE_YOU_PLAY_TITLE = 'Where you play';
export const WHO_YOU_PLAY_WITH_TITLE = 'Who you play with';
export const GAME_SUGGESTIONS_TITLE = 'Game suggestions';
export const PHOTOS_TITLE = 'Photos';
export const TAGS_TITLE = 'Tags';
export const INTRO_TITLE = 'Intro';

// --- the live lines ---------------------------------------------------------------------------

/**
 * `10 slots ticked`, or what a blank week means.
 *
 * The blank line names no cost, for the footnote's reason: a week nobody gave is *absent*, left
 * out of the matching rather than counted against the player.
 */
export function weekLine(week: readonly WeekCell[]): string {
  const standing = weekStanding(week);
  if (standing.kind === 'empty') return 'Nothing ticked — we do not know when you play';
  return counted(standing.count, 'slot ticked', 'slots ticked');
}

/** `12 km · Across your town` — the figure and the step's reading, joined as the tab joins facts. */
export function radiusLine(radiusKm: number): string {
  return `${radiusFigure(radiusKm)} · ${radiusWords(radiusKm)}`;
}

/** The one state the area has, and the rule the tab's sentence carries in full behind the row. */
export const AREA_LINE = 'Area set · updates when you open Raketa';

/** A rated sport with no answer, in the line's own register — never *Not set* with a capital. */
const NOT_SET_IN_LINE = 'not set';

/**
 * `Padel Competitive · Tennis For fun · Squash not set` — one clause per rated sport, in the
 * registry's order, the intent words `playIntentPresentation`'s.
 */
export function kindOfGameLine(rows: readonly PlayIntentRow[]): string {
  return rows
    .map(
      ({ sport, intent }) =>
        `${sportLabel(sport)} ${intent === undefined ? NOT_SET_IN_LINE : intentLabel(intent)}`,
    )
    .join(' · ');
}

/**
 * `2 of 3 · profile photo on court`, `1 of 3 · profile photo not checked as on court`, or what
 * no photo means.
 *
 * *On court* only of a profile photo the check **passed**: a flagged one and one nobody looked
 * at ([ADR-0138](../../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md))
 * both read as *not checked as on court* — a sentence about the check, never about the
 * photograph. The ceiling is the row's, cited.
 */
export function photosLine(photos: readonly UploadedPhoto[]): string {
  const leading = photos[0];
  if (leading === undefined) return 'None — a court poster stands in';
  const verdict = leading.review === 'allowed' ? 'on court' : 'not checked as on court';
  return `${photos.length} of ${PHOTO_CEILING} · profile photo ${verdict}`;
}

/**
 * `4 of 6 · Stays for a drink, Plays to win, +2` — the count against the **served** ceiling,
 * the first two by name and the rest as a count. The names and never the emoji: a live line is
 * one line of `tiny`, and the glyph is what makes a chip findable, not a sentence readable.
 */
export function tagsLine(tagIds: readonly SocialTagId[], maximum: number): string {
  const count = `${tagIds.length} of ${maximum}`;
  const named = tagIds.slice(0, 2).map(socialTagName);
  if (named.length === 0) return count;
  const rest = tagIds.length - named.length;
  return `${count} · ${named.join(', ')}${rest > 0 ? `, +${rest}` : ''}`;
}

/** The step's title, quoted, where no line was written. */
export const NO_INTRO_LINE = 'None — say it in your own words';

/** `“Will travel for a hard game.”` — the line as written, in quotes; or the step's invitation. */
export function introLine(intro: string | undefined): string {
  return intro === undefined ? NO_INTRO_LINE : `“${intro}”`;
}

// --- the screens' own sentences ---------------------------------------------------------------

/**
 * A screen's eyebrow under *On your card*: the group the row was opened from, and the step's
 * rule beside it where the step's eyebrow carried one — *On your card · Pick 2 to 6*, *On your
 * card · On-court only — up to three* — the steps' own composition with the group in place of
 * the position. The group title alone until a served rule is in, for the tags step's reason.
 *
 * The shell's words read inside the function and never at load: this feature's rows are
 * imported by the shell's surface, and a value taken while that module is still evaluating
 * would be `undefined`.
 */
export function onYourCardEyebrow(rule?: string): string {
  const group = YOU_COPY.groups.onYourCard;
  return rule === undefined ? group : `${group} · ${rule}`;
}

/**
 * The one line under *What kind of game*'s title — what the section's heading and body said,
 * in one sentence (ADR-0179 §2, §9).
 */
export const KIND_OF_GAME_LINE = 'This changes how people find you';

/** The buttons a step never had. `Saved` is the label while nothing has changed. */
export const SAVE = 'Save';
export const SAVED = 'Saved';
export const SAVING = 'Saving…';
export const SAVE_YOUR_WEEK = 'Save your week';
export const CLEAR_ALL = 'Clear all';
/** The intro's withdrawal — beside *Save*, offered only while a line is held (ADR-0179 §6). */
export const REMOVE_INTRO = 'Remove intro';
export const REMOVING = 'Removing…';

/** A read that failed offers itself again — the control the failure belongs to. */
export const TRY_AGAIN = 'Try again';

/** The spinners' spoken names, one per read a screen waits on. */
export const LOADING_WEEK = 'Loading your week';
export const LOADING_RADIUS = 'Loading your radius';
export const LOADING_DISTANCES = 'Loading distances';
export const LOADING_PHOTOS = 'Loading your photos';
export const LOADING_TAGS = 'Loading tags';
export const LOADING_YOUR_TAGS = 'Loading your tags';
export const LOADING_INTRO = 'Loading your intro';

/** *Where you play*'s one state, and the control under it. */
export const AREA_SET = 'Your area is set';
export const READ_AGAIN = 'Read my area again';

/**
 * The two rows whose screens land on #472: the line on the row, and the one line the screen
 * behind it says. Keyed so a screen and its row cannot come apart.
 */
export const DEFERRED_ROW = {
  whoYouPlayWith: {
    title: WHO_YOU_PLAY_WITH_TITLE,
    line: 'Who we match you with',
    screenLine:
      'Your own answer, and who you are matched with, are changed here, once the profile ' +
      'read carries them.',
  },
  gameSuggestions: {
    title: GAME_SUGGESTIONS_TITLE,
    line: 'Whether Raketa may suggest you games',
    screenLine: 'Your answer is changed here, once the profile read carries it.',
  },
} as const;

export type DeferredRowKey = keyof typeof DEFERRED_ROW;
