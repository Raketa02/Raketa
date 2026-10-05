/**
 * **Every sentence *Post a game* composes from a value** — the chips, the grid's heads and cells, a
 * cell's sheet, the pick and the guards, each drawn and spoken
 * ([#558](https://github.com/Raketa02/Raketa/issues/558); the screens A5; mocks 15–35). The fixed
 * words are `postingCopy.ts`.
 *
 * A day and an hour are the club's (`shared/date/platformZone`), named as the court block names a
 * game's — *Today*, *Tomorrow*, *Saturday*, *Saturday 10 Oct* a week out — and a moment a line names
 * as the money line does, *Sat 15:00*: the Fill in rows' short form, so *book by* reads one way on
 * every surface. A counted phrase goes through `counted()`.
 */

import { sportLabel } from '@/features/onboarding/types';
import { dayDate } from '@/shared/date/calendarDay';
import { platformClock, weekdayOf } from '@/shared/date/platformZone';
import type { AppError } from '@/shared/errors';
import { codeMessage } from '@/shared/errors';
import { counted } from '@/shared/formatting/counted';
import { formatDistanceKm, formatLevel, formatZloty } from '@/shared/formatting/ratingFormat';
import { dayLabel } from '@/shared/vocabulary/availabilityPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import type { SeatToFill } from '../domain/fillIn';
import {
  cellFill,
  fitsShown,
  type FreeCourt,
  type Posted,
  type PostingCell,
  type PostingDay,
  type PostingWeek,
  type PostPick,
  type PostStillFilling,
  type SlotFit,
} from '../domain/posting';
import type { DayRange } from '../domain/vocabulary';
import { calendarDayOf, gameDayOf } from '../domain/when';

import { LINE_JOIN, clubName, gameDayWords, shortMoment } from './deckPresentation';
import { rowTitle } from './fillInPresentation';
import { POSTING_COPY } from './postingCopy';

const COPY = POSTING_COPY;

/** A drawn line's parts aloud: the mocks' dots are commas to a listener. */
const SPOKEN_JOIN = ', ';

// ---------------------------------------------------------------------------
// The controls
// ---------------------------------------------------------------------------

/** *Padel, 10 rated here* — a sport chip, spoken; the chip draws the count beside the name. */
export function sportChipSpoken(sport: Sport, rated: number): string {
  return `${sportLabel(sport)}, ${counted(rated, 'member', 'members')} rated`;
}

/** *2,56* — a bound. */
export function levelFigure(value: number): string {
  return formatLevel(value);
}

/** *This week* · *Next week*. */
export function weekTitle(week: PostingWeek): string {
  return COPY.weeks[week];
}

// ---------------------------------------------------------------------------
// The grid
// ---------------------------------------------------------------------------

/** A column's head: *Today* or *Fri*, over *18 Sep*. */
export function dayHead(day: Pick<PostingDay, 'day' | 'isToday'>): {
  readonly name: string;
  readonly date: string;
} {
  const weekday = weekdayOf(day.day);
  const name = day.isToday ? COPY.today : weekday === undefined ? day.day : dayLabel(weekday);
  return { name, date: dayDate(day.day) };
}

/** *Sat 3 Oct* — a column's head, spoken. */
export function dayHeadSpoken(head: { readonly name: string; readonly date: string }): string {
  return `${head.name} ${head.date}`;
}

/** *Morning, 07:00 to 12:00* — a row's label, spoken. */
export function rangeLabelSpoken(range: DayRange): string {
  const [from, to] = COPY.rangeHours[range];
  return `${COPY.ranges[range]}, ${from} ${COPY.hoursTo} ${to}`;
}

/** *07:00–* over *12:00* — a row's hours, drawn in two lines as the mocks draw them. */
export function rangeHoursLines(range: DayRange): readonly [string, string] {
  const [from, to] = COPY.rangeHours[range];
  return [`${from}–`, to];
}

/** *5* · *5+* — the number in a cell, or nothing on a dead one. */
export function cellCount(cell: Pick<PostingCell, 'fitsFree'>): string | undefined {
  const shown = fitsShown(cell);
  if (shown === undefined) return undefined;
  return shown.more ? `${shown.count}+` : String(shown.count);
}

/**
 * **A day's range named** — *Saturday evening*, *Tomorrow morning*, *This afternoon*, and *Saturday 10
 * Oct · evening* a week out: a sheet's title, and the start of a cell's name.
 */
export function rangeOfDay(day: string, range: DayRange, readAt: number): string {
  const named = calendarDayOf(day, readAt);
  if (named === undefined) return `${day} ${COPY.rangeInLine[range]}`;
  switch (named.kind) {
    case 'today':
      return COPY.thisRange[range];
    case 'dated':
      return `${gameDayWords(named)}${LINE_JOIN}${COPY.rangeInLine[range]}`;
    default:
      return `${gameDayWords(named)} ${COPY.rangeInLine[range]}`;
  }
}

/**
 * **A cell, spoken** — *Saturday evening, 5 of your best fits free, a court free and a full game, a
 * game already happening here, your pick*. The look's words, then each flag drawn over it.
 */
export function cellSpoken(cell: PostingCell, picked: boolean, readAt: number): string {
  const fill = cellFill(cell);
  return [
    rangeOfDay(cell.day, cell.range, readAt),
    ...(fill === 'dead' ? [] : [`${cell.fitsFree} ${COPY.sheet.fitsFreeSpoken}`]),
    COPY.fillSpoken[fill],
    ...(cell.happening ? [COPY.happeningSpoken] : []),
    ...(cell.outsideYourHours ? [COPY.outsideSpoken] : []),
    ...(cell.past ? [COPY.pastSpoken] : []),
    ...(picked ? [COPY.pickedSpoken] : []),
  ].join(SPOKEN_JOIN);
}

// ---------------------------------------------------------------------------
// A cell's sheet
// ---------------------------------------------------------------------------

/**
 * **The sheet's headline** (A5.3) — the count in its badge and *5 of your best fits free then*;
 * *only 2 fit · may not fill* where a court is free and fewer than a full game are; *Nobody who fits
 * is free then* with no badge — each with *· outside your hours* where the poster's week has none.
 */
export function slotHeadline(cell: PostingCell): {
  readonly count?: number;
  readonly words: string;
} {
  const outside = cell.outsideYourHours ? `${LINE_JOIN}${COPY.outsideSpoken}` : '';
  if (cell.fitsFree === 0) return { words: `${COPY.sheet.nobody}${outside}` };
  const words =
    cell.courtFree && !cell.fullGame
      ? `only ${cell.fitsFree} fit${LINE_JOIN}${COPY.sheet.mayNotFill}`
      : `${cell.fitsFree} ${COPY.sheet.fitsFree}`;
  return { count: cell.fitsFree, words: `${words}${outside}` };
}

/** *2,75 · 93* — a fit's Level and how even a game with them is forecast. */
export function fitLine(fit: SlotFit): string | undefined {
  const parts = [
    fit.level === undefined ? undefined : formatLevel(fit.level),
    fit.forecastPct === undefined ? undefined : String(fit.forecastPct),
  ].filter((part): part is string => part !== undefined);
  return parts.length === 0 ? undefined : parts.join(LINE_JOIN);
}

/** A fit's name — whole, never cut to a first name (ADR-0171); the unknown's mark without one. */
export function fitName(fit: SlotFit): string {
  return fit.name ?? '?';
}

/** *Karol Tomaszewski, level 2,75, a 93 % even game* — a fit, spoken. */
export function fitSpoken(fit: SlotFit): string {
  return [
    fitName(fit),
    ...(fit.level === undefined ? [] : [`level ${formatLevel(fit.level)}`]),
    ...(fit.forecastPct === undefined ? [] : [`a ${fit.forecastPct} % even game`]),
  ].join(SPOKEN_JOIN);
}

/** *27 zł each*. */
export function eachWords(shareGrosze: number): string {
  return `${formatZloty(shareGrosze)} ${COPY.each}`;
}

/** *4 free* — a court hour's own count of fits free then (Q77). */
export function fitsFreeTag(court: Pick<FreeCourt, 'fitsFree'>): string {
  return `${court.fitsFree} free`;
}

/** *2,4 km · 27 zł if it fills · book by Sat 15:00* — a free court's line. */
export function courtRowLine(court: FreeCourt): string {
  return [
    ...(court.distanceKm === undefined ? [] : [formatDistanceKm(court.distanceKm)]),
    `${formatZloty(court.shareGrosze)} ${COPY.ifItFills}`,
    `book by ${shortMoment(court.bookBy)}`,
  ].join(LINE_JOIN);
}

/** *17:00* — a free court's hour. */
export function courtHour(court: Pick<FreeCourt, 'startsAt'>): string {
  return platformClock(court.startsAt) ?? '';
}

/** **A free court, spoken** — the hour, the club, its line, its count and the share. */
export function courtRowSpoken(court: FreeCourt, picked: boolean): string {
  return [
    courtHour(court),
    clubName(court),
    courtRowLine(court),
    `${court.fitsFree} ${COPY.sheet.fitsFreeSpoken}`,
    eachWords(court.shareGrosze),
    ...(picked ? [COPY.pickedSpoken] : []),
  ].join(SPOKEN_JOIN);
}

/** *Padel · Sunday 20:00* — a game already happening here, as a Fill in row names it. */
export function happeningTitle(
  game: { readonly sport: Sport; readonly kind: SeatToFill['kind']; readonly startsAt: string },
  readAt: number,
): string {
  return rowTitle(game, gameDayOf(game.startsAt, readAt));
}

/** *Centrum Ruchu · Court 2 · 30 zł each* — a rescue's line: a booked court has its number. */
export function rescueLine(row: SeatToFill): string {
  return [clubName(row), row.courtName, eachWords(row.shareGrosze)].join(LINE_JOIN);
}

/** *Kuba Wiśniewski · Bonarka Arena · 32 zł if it fills* — a post's line: no court number (Q79). */
export function postLine(post: PostStillFilling): string {
  return [
    post.challenger?.name ?? COPY.sheet.group,
    clubName(post),
    `${formatZloty(post.shareGrosze)} ${COPY.ifItFills}`,
  ].join(LINE_JOIN);
}

/** *any level, you are free* — why a game already happening is listed, spoken. */
export function fitReasonsSpoken(): string {
  return [COPY.sheet.anyLevel, COPY.sheet.youAreFree].join(SPOKEN_JOIN);
}

/** *2 seats* — what is still open on a game already happening. */
export function seatsTag(open: number): string {
  return counted(open, 'seat', 'seats');
}

/** A game already happening, spoken — its title, its line and its open seats. */
export function happeningSpoken(title: string, line: string, open: number): string {
  return [title, line, `${seatsTag(open)} open`].join(SPOKEN_JOIN);
}

// ---------------------------------------------------------------------------
// The pick and the button
// ---------------------------------------------------------------------------

/** *Saturday 17:00 · Ogrody 33 · 27 zł each if it fills* — what the post will be, under the button. */
export function pickLine(
  pick: Pick<PostPick, 'startsAt'>,
  court: FreeCourt | undefined,
  readAt: number,
): string {
  const day = gameDayOf(pick.startsAt, readAt);
  const when = [day === undefined ? undefined : gameDayWords(day), platformClock(pick.startsAt)]
    .filter((part): part is string => part !== undefined)
    .join(' ');
  // The club and the share are the slot's read — until it is in, the hour the player chose.
  if (court === undefined) return when;
  return [when, clubName(court), `${eachWords(court.shareGrosze)} ${COPY.ifItFills}`].join(
    LINE_JOIN,
  );
}

/**
 * **Why a post was refused** (A5.4) — under the button, in the helper's place. The week the
 * poster's games are booked for; otherwise the route's code over the recovery sentence every
 * screen shares.
 */
export function postRefusal(error: AppError): string {
  if (error.code === 'games_per_week_booked') {
    const week = typeof error.details?.week === 'string' ? error.details.week : undefined;
    return week === undefined
      ? 'Your games that week are already booked.'
      : `Your games for the week from ${dayDate(week)} are already booked.`;
  }
  return codeMessage(COPY.refused, error);
}

/** *Posted — 5 of your best fits have it.* — the toast over Fill in. */
export function postedToast(posted: Posted): string {
  return `Posted — ${posted.dealtTo} of your best fits ${posted.dealtTo === 1 ? 'has' : 'have'} it.`;
}

/** The grid could not be read for these controls — said in its place, or the shared sentence. */
export function gridRefusal(error: AppError): string | undefined {
  return error.code === undefined ? undefined : COPY.gridRefused[error.code];
}
