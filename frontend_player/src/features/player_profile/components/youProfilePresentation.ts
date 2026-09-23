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
 * ## Two lines say less than the read holds, on purpose
 *
 * *Who you play with* says the preference and never the gender: the gender is on the read for
 * the screen behind the row to pre-select from, and the row, the header card and the record
 * draw neither (ADR-0179 §4). *Game suggestions* says the answer and its day, and leaves the
 * words it was given against to the card behind it, where the evidence is read whole.
 */

import { sportLabel } from '@/features/onboarding/types';
import { YOU_COPY } from '@/features/shell/types';
import { dayDate } from '@/shared/date/calendarDay';
import { platformDay } from '@/shared/date/platformZone';
import { counted } from '@/shared/formatting/counted';
import { intentLabel } from '@/shared/vocabulary/playIntentPresentation';
import { socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { GenderPreference } from '../domain/gender';
import type { PlayIntentRow } from '../domain/playIntentRows';
import type { ConsentSurface, RecordedProposalsOptIn } from '../domain/proposalsOptIn';
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

/**
 * `Matched with anyone` · `… women only` · `… men only` — **the preference only.**
 *
 * The gender is drawn on its own screen and nowhere else on the tab
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §4): the row, the header card and the record never carry it. Keyed by the preference, so a
 * fourth value has no line rather than a wrong one.
 */
const MATCHED_WITH: Readonly<Record<GenderPreference, string>> = {
  any: 'Matched with anyone',
  'women-only': 'Matched with women only',
  'men-only': 'Matched with men only',
};

export function whoYouPlayWithLine(preference: GenderPreference): string {
  return MATCHED_WITH[preference];
}

/**
 * The day an answer was given, as the tab says a date — `12 Aug`, in the platform's zone,
 * which is the one zone this platform reads a moment in (`platformZone`). An instant that is
 * not one is printed as it stands rather than guessed at.
 */
function answeredOn(answeredAt: string): string {
  return dayDate(platformDay(answeredAt) ?? answeredAt);
}

/** The standing answer's one word — `Yes` / `No` — on the card's tag and in the row's line. */
export function answerWord(accepted: boolean): string {
  return accepted ? 'Yes' : 'No';
}

/** `Yes — since 12 Aug` · `No — since 12 Aug`. */
export function gameSuggestionsLine(answer: RecordedProposalsOptIn): string {
  return `${answerWord(answer.accepted)} — since ${answeredOn(answer.answeredAt)}`;
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

/**
 * The spoken name of a *Save* that shares its screen with another — `Save — About you`. The
 * visible label stays `Save`; the group's own heading is what tells the two apart for a
 * listener, as a name rather than a hint, because a hint can be switched off (Part 13).
 */
export function groupSaveLabel(label: string, group: string): string {
  return `${label} — ${group}`;
}

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
export const LOADING_WHO_YOU_PLAY_WITH = 'Loading who you play with';
export const LOADING_GAME_SUGGESTIONS = 'Loading your answer';

/** *Where you play*'s one state, and the control under it. */
export const AREA_SET = 'Your area is set';
export const READ_AGAIN = 'Read my area again';

/** The answer card's label on *Game suggestions*, over the tag that says which. */
export const YOUR_ANSWER = 'Your answer';

/**
 * Where the standing answer was given, in the card's sentence — keyed by the surface, so a
 * third screen asking the question has no clause rather than a wrong one.
 */
const GIVEN_FROM: Readonly<Record<ConsentSurface, string>> = {
  onboarding: 'setting up',
  profile: 'this screen',
};

/**
 * `Given 12 Aug, against these words (proposals-opt-in.v3), from setting up.` — the evidence
 * beside the answer: when, against which words, and from which of the two screens. The version
 * is printed as the identifier it is, because it is what the record holds and the words are
 * on the card above.
 */
export function answerGivenLine(answer: RecordedProposalsOptIn): string {
  return (
    `Given ${answeredOn(answer.answeredAt)}, against these words (${answer.copyVersion}), ` +
    `from ${GIVEN_FROM[answer.surface]}.`
  );
}
