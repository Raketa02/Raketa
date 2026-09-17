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
 * ## Five rows land with their contract, and say so
 *
 * Photos, Tags, Intro, Who you play with and Game suggestions read fields the profile read
 * grows on [#466](https://github.com/Raketa02/Raketa/issues/466) and this client reads on
 * [#471](https://github.com/Raketa02/Raketa/issues/471) and
 * [#472](https://github.com/Raketa02/Raketa/issues/472). Until then each row draws a line
 * naming what it is, and the screen behind it says in one `tiny` line what it is and that the
 * edit lands with the read that carries the fact — 10.1's empty-state rule, and never *coming
 * soon*.
 */

import { sportLabel } from '@/features/onboarding/types';
import { counted } from '@/shared/formatting/counted';
import { intentLabel } from '@/shared/vocabulary/playIntentPresentation';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { PlayIntentRow } from '../domain/playIntentRows';
import { weekStanding } from '../domain/availabilityWeek';

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

// --- the screens' own sentences ---------------------------------------------------------------

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

/** A read that failed offers itself again — the control the failure belongs to. */
export const TRY_AGAIN = 'Try again';

/** The spinners' spoken names, one per read a screen waits on. */
export const LOADING_WEEK = 'Loading your week';
export const LOADING_RADIUS = 'Loading your radius';
export const LOADING_DISTANCES = 'Loading distances';

/** *Where you play*'s one state, and the control under it. */
export const AREA_SET = 'Your area is set';
export const READ_AGAIN = 'Read my area again';

/**
 * The five rows whose screens land on #471 and #472: the line on the row, and the one line
 * the screen behind it says. Keyed so a screen and its row cannot come apart.
 */
export const DEFERRED_ROW = {
  photos: {
    title: PHOTOS_TITLE,
    line: 'Up to three, on court',
    screenLine:
      'Your court photos — up to three, the first your profile photo — are edited here, ' +
      'once the profile read carries them.',
  },
  tags: {
    title: TAGS_TITLE,
    line: 'The tags other players recognise you by',
    screenLine: 'Your tags are edited here, once the profile read carries them.',
  },
  intro: {
    title: INTRO_TITLE,
    line: 'One line, in your own words',
    screenLine: 'Your intro is edited here, once the profile read carries it.',
  },
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
