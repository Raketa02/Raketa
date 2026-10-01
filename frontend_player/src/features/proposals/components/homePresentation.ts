/**
 * **Every sentence Home's booked cards and a booked game's details compose from a value**
 * ([#556](https://github.com/Raketa02/Raketa/issues/556)) — the money line, the details' second
 * line and money row, WHERE's aside, and a card spoken as one element. The fixed words are
 * `homeCopy.ts`.
 *
 * **Every day and hour here is the club's** (`shared/date/platformZone`), as the court block's are:
 * *free to leave until Fri 16:00* is the club's Friday, on every phone that reads it.
 */

import { sportLabel } from '@/features/onboarding/types';
import { counted } from '@/shared/formatting/counted';
import { formatDistanceKm, formatZloty } from '@/shared/formatting/ratingFormat';
import { platformClock } from '@/shared/date/platformZone';
import { dayLabel } from '@/shared/vocabulary/availabilityPresentation';
import { theme, type ButtonVariant } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { BookedGame, HomeGame, MoneyLine } from '../domain/home';
import type { HomeStatus } from '../domain/vocabulary';
import { weekdayAt } from '../domain/when';

import { HOME_GAME_COPY } from './homeCopy';
import { clubName, timeWords } from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = HOME_GAME_COPY;

/** The mocks' middle dot. */
const DOT = ' · ';

/** *Fri 16:00* — a moment the line names, on the club's calendar. */
function shortMoment(instant: string): string {
  const weekday = weekdayAt(instant);
  const day = weekday === undefined ? '' : `${dayLabel(weekday)} `;
  return `${day}${platformClock(instant) ?? ''}`;
}

/**
 * **The status's colour** — the tag's dot and the facts' accent line (A4.1, A8): *Waiting for the
 * club* and *Seat open* amber, *Booked* mint, *Called off* red, and the result states as today's
 * cards draw them (`STAGE_DOT`: needs a result and confirm amber, counted mint, the other two ends
 * hairline). On the dark card the amber is `arranging` and the red `gameRed`, each the shade that
 * carries on that ground.
 */
export const STATUS_INK: Readonly<Record<HomeStatus, string>> = {
  WAITING_FOR_THE_CLUB: theme.color.arranging,
  BOOKED: theme.color.mint,
  SEAT_OPEN: theme.color.arranging,
  NEEDS_RESULT: theme.color.arranging,
  CONFIRM_THE_RESULT: theme.color.arranging,
  COUNTED: theme.color.mint,
  UNCOUNTED: theme.color.onDarkHair,
  NEVER_PLAYED: theme.color.onDarkHair,
  CALLED_OFF: theme.color.gameRed,
};

/**
 * **A Home card's *Open game*** — the settled fill on every game still ahead of its end, the
 * on-dark one on an ending: the Classic card's own two (`ACCENT`), so one rail does not draw two
 * languages of button.
 */
export const OPEN_GAME_VARIANT: Readonly<Record<HomeStatus, ButtonVariant>> = {
  WAITING_FOR_THE_CLUB: 'settled',
  BOOKED: 'settled',
  SEAT_OPEN: 'settled',
  NEEDS_RESULT: 'settled',
  CONFIRM_THE_RESULT: 'settled',
  COUNTED: 'onDark',
  UNCOUNTED: 'onDark',
  NEVER_PLAYED: 'onDark',
  CALLED_OFF: 'onDark',
};

/** *Booked* · *Waiting for the club* · … — the status tag's word. */
export function statusWord(status: HomeStatus): string {
  return COPY.status[status];
}

/**
 * **The line under a Home card** — the mechanics §14.1's table, word for word: *Paid · 30 zł · free
 * to leave until Sat 17:00*, *Nobody pays until Bonarka confirms*, *1 seat open · fills by Sat 17:00
 * or the game is off and everyone is refunded*, *Refunded 30 zł*.
 */
export function moneyWords(line: MoneyLine): string {
  const money = COPY.money;
  switch (line.kind) {
    case 'booked': {
      const share = formatZloty(line.shareGrosze);
      const paid = line.paid ? `${money.paid}${DOT}${share}` : share;
      return line.freeToLeaveUntil === undefined
        ? paid
        : `${paid}${DOT}${money.freeToLeaveUntil} ${shortMoment(line.freeToLeaveUntil)}`;
    }
    case 'waiting':
      return `${money.nobodyPaysUntil} ${line.club ?? money.theClub} ${money.confirms}`;
    case 'seatOpen': {
      const open = counted(line.seats, money.seatOpen, money.seatsOpen);
      return line.fillsBy === undefined
        ? `${open}${DOT}${money.offeredToOthers}`
        : `${open}${DOT}${money.fillsBy} ${shortMoment(line.fillsBy)} ${money.orTheGameIsOff}`;
    }
    case 'calledOff':
      return line.refundedGrosze === undefined
        ? money.nobodyPaid
        : `${money.refunded} ${formatZloty(line.refundedGrosze)}`;
  }
}

/** *Padel · booked* — the details' second line: the sport, and the status in lower case. */
export function statusSubline(sport: Sport, status: HomeStatus): string {
  return `${sportLabel(sport)}${DOT}${statusWord(status).toLowerCase()}`;
}

/** *Court 2 · 3,1 km* — WHERE's aside: the court, and how far the club is when that is known. */
export function whereAside(courtName: string, distanceKm: number | undefined): string {
  return distanceKm === undefined ? courtName : `${courtName}${DOT}${formatDistanceKm(distanceKm)}`;
}

/** *10:00* and *until 11:00* — a booked game's TIME, its end the read's own `ends_at`. */
export function bookedTime(
  startsAt: string,
  endsAt: string,
): { readonly from: string; readonly until: string } {
  return {
    from: platformClock(startsAt) ?? '',
    until: `${PROPOSALS_COPY.game.until} ${platformClock(endsAt) ?? ''}`,
  };
}

/** One fact of the details' accent line: its label, its value and the words after it. */
export interface FactWords {
  readonly label: string;
  readonly value: string;
  readonly aside?: string;
}

/**
 * **The details' money row** (the screens A4.1): *PAID · 28 zł · your share · to the club*, with
 * *· free to leave until Sat 10:00* while the cut-off is ahead of `now`; the share nobody pays yet
 * while the club decides; *Refunded*, or *nobody paid*, once the game is called off.
 */
export function moneyRow(
  game: Pick<BookedGame, 'status' | 'money' | 'where'>,
  now: number,
): FactWords {
  const { money } = game;
  const words = COPY.details;
  const value = formatZloty(money.shareGrosze);

  if (game.status === 'CALLED_OFF') {
    return money.paid
      ? { label: words.refunded, value }
      : { label: words.yourShare, value, aside: words.nobodyPaid };
  }
  if (game.status === 'WAITING_FOR_THE_CLUB') {
    const waiting = moneyWords({
      kind: 'waiting',
      ...(game.where.name === undefined ? {} : { club: game.where.name }),
    });
    return {
      label: words.yourShare,
      value,
      aside: waiting.charAt(0).toLowerCase() + waiting.slice(1),
    };
  }

  const until = money.freeToLeaveUntil;
  const free =
    until !== undefined && Date.parse(until) > now
      ? `${DOT}${COPY.money.freeToLeaveUntil} ${shortMoment(until)}`
      : '';
  return {
    label: money.paid ? words.paid : words.yourShare,
    value,
    aside: `${words.toTheClub}${free}`,
  };
}

/**
 * **A Home card, spoken** — one element with no action, as the Classic card's body is: *Booked,
 * new. Padel. Bonarka Arena, Court 2. Saturday, 16:00 until 17:00. Paid, 30 zł. Chat open.* The
 * mocks' dots are commas aloud. *Open game* is an element of its own, so its verb is not here.
 */
export function homeCardLabel({
  game,
  fresh,
  day,
  money,
  chat,
}: {
  readonly game: Pick<HomeGame, 'status' | 'sport' | 'club' | 'courtName' | 'startsAt'>;
  /** Marked *new*. */
  readonly fresh: boolean;
  /** DAY's words, or nothing for an instant that names no day. */
  readonly day: string | undefined;
  /** The money line as drawn, or nothing. */
  readonly money: string | undefined;
  /** The game's chat is open. */
  readonly chat: boolean;
}): string {
  const time = timeWords(game.startsAt);
  const when = [day, `${time.from} ${time.until}`].filter((part) => part !== undefined).join(', ');
  return [
    fresh ? `${statusWord(game.status)}, ${COPY.newSpoken}` : statusWord(game.status),
    sportLabel(game.sport),
    `${clubName(game)}, ${game.courtName}`,
    when,
    ...(money === undefined ? [] : [money.split(DOT).join(', ')]),
    ...(chat ? [COPY.chatOpen.charAt(0).toUpperCase() + COPY.chatOpen.slice(1)] : []),
  ]
    .map((sentence) => `${sentence}.`)
    .join(' ');
}
