/**
 * **Every sentence Courts & prices says** (the screens B3; the mechanics §16.4 and §16.5), and
 * how it writes a court's week, an exception's days and a price's share.
 */

import { sportName, type Sport } from '@/features/club-details/mappers';
import { clock, formatZloty } from '@/ui/format';
import { FALLBACK_REFUSAL } from '@/ui/copy';
import { sentenceAbout, sentenceFor, type RefusalAbout } from '@/ui/forms';
import type { SelectOption } from '@/ui/SelectField';

import { END_HOUR, FIRST_HOUR, type BandDays, type Court, type Exception } from './mappers';

/** The week's days, Monday first, as a cell is named and as a column is headed. */
export const DAYS = [
  { long: 'Monday', short: 'Mon' },
  { long: 'Tuesday', short: 'Tue' },
  { long: 'Wednesday', short: 'Wed' },
  { long: 'Thursday', short: 'Thu' },
  { long: 'Friday', short: 'Fri' },
  { long: 'Saturday', short: 'Sat' },
  { long: 'Sunday', short: 'Sun' },
] as const;

/** The months as a short date writes them: *12 Oct*. */
export const MONTHS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

function hourOptions(from: number, to: number): SelectOption[] {
  return Array.from({ length: to - from + 1 }, (_, index) => ({
    value: String(from + index),
    label: clock(from + index),
  }));
}

/** The hours a span of a day can start at, 07:00 to 22:00, and end at, 08:00 to 23:00. */
export const FROM_HOURS = hourOptions(FIRST_HOUR, END_HOUR - 1);
export const UNTIL_HOURS = hourOptions(FIRST_HOUR + 1, END_HOUR);

/** *Court 1*, *Court 1 and Court 3*, *Court 1, Court 2 and Court 3*. */
export function listed(names: readonly string[]): string {
  if (names.length <= 1) return names.join('');
  return `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`;
}

export const COURTS_COPY = {
  caption: 'What you sell through Raketa',
  title: 'Courts & prices',
  courts: {
    title: 'Courts',
    lead:
      'The courts you offer Raketa. Players never pick one: each game is given the first free ' +
      'court of its sport when it is booked.',
    add: '+ Add a court',
    none: 'No courts yet. Add each court you want to offer through Raketa.',
    columns: {
      court: 'Court',
      sport: 'Sport',
      indoor: 'Indoor or outdoor',
      raketa: 'Raketa',
      actions: 'Actions',
    },
    indoorOrOutdoor: { indoor: 'Indoor', outdoor: 'Outdoor' },
    offered: { on: 'on', off: 'off' },
    switchOff: 'Switch off',
    switchOn: 'Switch on',
    edit: 'Edit',
    form: {
      addTitle: 'Add a court',
      editTitle: (name: string) => `Edit ${name}`,
      name: 'Name',
      namePlaceholder: 'Court 1',
      sport: 'Sport',
      indoor: 'Indoor or outdoor',
      cancel: 'Cancel',
      add: 'Add court',
      adding: 'Adding…',
      save: 'Save',
      saving: 'Saving…',
      delete: 'Delete court',
    },
    confirmOff: {
      title: (name: string) => `Switch ${name} off?`,
      lead:
        'It stops being offered to Raketa: no new games are built on it. Games already booked ' +
        'on it are played as booked, and its hours are kept for when you switch it back on.',
      cancel: 'Cancel',
      confirm: 'Switch off',
    },
    confirmDelete: {
      title: (name: string) => `Delete ${name}?`,
      lead:
        'It goes, with its hours. A court with a game booked ahead of it can only be switched ' +
        'off.',
      cancel: 'Cancel',
      confirm: 'Delete',
    },
  },
  hours: {
    title: 'Weekly hours for Raketa',
    lead:
      'The hours of an ordinary week each court is offered, from 07:00 to 23:00: an hour ' +
      'outside them could never match a player. Tap an hour, or drag across several.',
    none: 'Add a court first; then paint the hours it is offered.',
    picker: 'Courts to set',
    allOf: (sport: Sport) => `All ${sportName(sport).toLowerCase()} courts`,
    differ: "These courts don't all have the same hours. Saving gives each of them the week below.",
    grid: (courts: string) => `Hours offered: ${courts}`,
    save: 'Save hours',
    saving: 'Saving…',
    saved: (names: readonly string[]) => `Hours saved for ${listed(names)}.`,
    copy: 'Copy to other courts',
    copyDialog: {
      title: (name: string) => `Copy ${name}'s week`,
      lead: (name: string) =>
        `The week above is saved on ${name}, and on each court you tick in place of its own.`,
      to: 'Copy to',
      cancel: 'Cancel',
      confirm: 'Copy',
    },
  },
  exceptions: {
    title: 'Exceptions',
    lead:
      'Close hours without changing the week: a tournament, a holiday, a repair. An hour with ' +
      'a game booked on it stays open: cancel the booking first.',
    add: '+ Add an exception',
    none: 'Nothing closed.',
    columns: { reason: 'Reason', when: 'When', courts: 'Courts', actions: 'Actions' },
    allCourts: 'All courts',
    remove: 'Remove',
    form: {
      scope: 'Which courts',
      all: 'All courts',
      some: 'Some courts',
      courts: 'Courts',
      when: 'When',
      day: 'A day',
      days: 'Several days',
      hours: 'Hours on a day',
      dayLabel: 'Day',
      first: 'First day',
      last: 'Last day',
      from: 'From',
      until: 'Until',
      choose: 'Choose',
      reason: 'Reason',
      reasonHint: 'For your own records: players never see it.',
      reasonPlaceholder: 'Tournament',
      cancel: 'Cancel',
      add: 'Add exception',
      adding: 'Adding…',
    },
    bookedThen: (court: string) => `${court} is booked then — cancel the booking first.`,
    seeBooking: 'See the booking',
  },
  prices: {
    title: 'Prices',
    lead:
      'What a court-hour costs, shared equally by its players. New prices apply to new cards ' +
      'only: a game already dealt or booked keeps its price.',
    price: 'Price per court-hour (zł)',
    unpriced: 'Not priced yet: its courts are offered once it is.',
    addBand: '+ Add a price band',
    band: (n: number) => `Price band ${n}`,
    days: 'Days',
    bandDays: { WEEKDAYS: 'Weekdays', WEEKEND: 'Weekend' } satisfies Record<BandDays, string>,
    from: 'From',
    until: 'Until',
    bandPrice: 'Price (zł)',
    removeBand: 'Remove band',
    save: 'Save prices',
    saving: 'Saving…',
    saved: 'Prices saved.',
  },
} as const;

/** *140 zł ÷ 4 = 35 zł each*: what each player pays of a price (the screens B3). */
export function shareLine(priceGrosze: number, seats: number): string {
  return `${formatZloty(priceGrosze)} ÷ ${seats} = ${formatZloty(priceGrosze / seats)} each`;
}

/** *12 Oct*, from a local day `2026-10-12`. */
function dayMonth(day: string): { day: number; month: string } {
  const [, month = '1', date = '1'] = day.split('-');
  return { day: Number(date), month: MONTHS[Number(month) - 1] ?? '' };
}

/**
 * **When an exception closes**: *12 Oct*, *4–5 Oct*, *30 Oct – 2 Nov*, and its hours after a
 * dot when it closes only some: *12 Oct · 09:00–12:00*.
 */
export function closedWhen(exception: Exception): string {
  const first = dayMonth(exception.firstDay);
  const last = dayMonth(exception.lastDay);
  const days =
    exception.firstDay === exception.lastDay
      ? `${first.day} ${first.month}`
      : first.month === last.month
        ? `${first.day}–${last.day} ${last.month}`
        : `${first.day} ${first.month} – ${last.day} ${last.month}`;
  const { hours } = exception;
  return hours === null ? days : `${days} · ${clock(hours.from)}–${clock(hours.until)}`;
}

/** *All courts*, or the courts it closes by name, in the club's order. */
export function closedCourts(exception: Exception, courts: readonly Court[]): string {
  if (exception.courtIds === null) return COURTS_COPY.exceptions.allCourts;
  return courts
    .filter((court) => exception.courtIds?.includes(court.id))
    .map((court) => court.name)
    .join(', ');
}

/** A court's refusals, under the field they name. */
export const COURT_REFUSALS: Readonly<Record<string, string>> = {
  court_name_invalid: "A court's name is 1 to 40 characters.",
  court_name_taken: 'Another of your courts has this name.',
  court_sport_required: "Choose the court's sport.",
  court_sport_not_offered: 'Your club no longer offers that sport. Tick it on Details first.',
  court_indoor_required: 'Say whether it is indoor or outdoor.',
};

/** What can be refused about one court, said about it by name: an edit, a switch, a delete. */
const ABOUT_A_COURT: Readonly<Record<string, (name: string) => string>> = {
  court_not_found: (name) => `${name} isn't one of your courts any more.`,
};

/** An edit's refusal over its form: a court with a booking ahead keeps its sport. */
export function courtFormRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, {
    ...ABOUT_A_COURT,
    court_has_bookings: (name) =>
      `${name} has a booking ahead, so it keeps its sport until that game is played.`,
  });
}

/** A switch's or a delete's refusal, over the table. */
export function courtActRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, {
    ...ABOUT_A_COURT,
    court_has_bookings: (name) =>
      `${name} has a booking ahead, so it can't be deleted. Switch it off instead.`,
  });
}

/** A save that names a court the club no longer has: deleted from another browser. */
const COURT_GONE = "One of those courts isn't yours any more.";

export const HOURS_REFUSALS: Readonly<Record<string, string>> = {
  court_not_found: COURT_GONE,
};

/** An exception's refusals, under the field they name. A booking's is said with its court. */
export const EXCEPTION_REFUSALS: Readonly<Record<string, string>> = {
  exception_reason_invalid: 'Give a reason, up to 80 characters.',
  exception_day_required: 'Choose when it closes.',
  exception_days_invalid: "The last day can't come before the first.",
  exception_in_the_past: 'That day is over already.',
  exception_hours_invalid: 'Choose hours between 07:00 and 23:00, ending after they start.',
  exception_courts_required: 'Tick at least one court.',
  court_booked_then: 'One of those courts is booked then — cancel the booking first.',
  court_not_found: COURT_GONE,
  exception_not_found: 'That exception was removed already.',
};

/** A price's refusal, said under its sport; a split is said with the sport's seats. */
export function priceRefusal(code: string, sport: Sport, seats: number): string {
  const name = sportName(sport).toLowerCase();
  switch (code) {
    case 'price_invalid':
      return 'Type a price in złoty, like 120 or 142,50.';
    case 'price_required':
      return 'Price the court-hour before its bands.';
    case 'price_out_of_range':
      return 'A court-hour costs 10 zł to 1000 zł.';
    case 'price_does_not_split':
      return `A ${name} price splits evenly among ${seats} players, to the grosz.`;
    case 'price_band_hours_invalid':
      return "A band's hours are within 07:00–23:00, ending after they start.";
    case 'price_bands_overlap':
      return "Two bands of the same days can't overlap.";
    case 'price_sport_not_offered':
      return `Your club no longer offers ${name}. Tick it on Details first.`;
    default:
      return sentenceFor(code, {}) ?? FALLBACK_REFUSAL;
  }
}
