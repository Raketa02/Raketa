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

import {
  courtIsGiven,
  cutOffAhead,
  moneyLineOf,
  type BookedGame,
  type HomeGame,
  type MoneyLine,
} from '../domain/home';
import type { GameKind, HomeStatus } from '../domain/vocabulary';
import { weekdayAt, type GameDay } from '../domain/when';

import { clubName, gameDayWords, LINE_JOIN, timeWords } from './deckPresentation';
import type { FactWords } from './GameFacts';
import { HOME_GAME_COPY } from './homeCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = HOME_GAME_COPY;

/** A drawn line's parts aloud: the mocks' dots are commas to a listener. */
const SPOKEN_JOIN = ', ';

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
 * **The money line's parts** — the mechanics §14.1's table, word for word, one clause a part: drawn
 * joined by the mocks' dots (`moneyWords`), spoken joined by commas (`moneySpoken`), so neither is
 * cut out of the other.
 */
function moneyParts(line: MoneyLine): readonly string[] {
  const money = COPY.money;
  switch (line.kind) {
    case 'booked': {
      const share = formatZloty(line.shareGrosze);
      return [
        ...(line.paid ? [money.paid] : []),
        share,
        ...(line.freeToLeaveUntil === undefined
          ? []
          : [`${money.freeToLeaveUntil} ${shortMoment(line.freeToLeaveUntil)}`]),
      ];
    }
    case 'waiting':
      return [`${money.nobodyPaysUntil} ${line.club ?? money.theClub} ${money.confirms}`];
    case 'seatOpen': {
      const open = counted(line.seats, money.seatOpen, money.seatsOpen);
      return line.fillsBy === undefined
        ? [open, money.offeredToOthers, money.goesAhead]
        : [open, `${money.fillsBy} ${shortMoment(line.fillsBy)} ${money.orTheGameIsOff}`];
    }
    case 'calledOff':
      return [
        line.refundedGrosze === undefined
          ? money.nobodyPaid
          : `${money.refunded} ${formatZloty(line.refundedGrosze)}`,
      ];
  }
}

/**
 * **The line under a Home card**: *Paid · 30 zł · free to leave until Sat 17:00*, *Nobody pays until
 * Bonarka confirms*, *1 seat open · fills by Sat 17:00 or the game is off and everyone is refunded*,
 * *Refunded 30 zł*.
 */
export function moneyWords(line: MoneyLine): string {
  return moneyParts(line).join(LINE_JOIN);
}

/** The same line aloud: *Paid, 30 zł, free to leave until Fri 16:00*. */
export function moneySpoken(line: MoneyLine): string {
  return moneyParts(line).join(SPOKEN_JOIN);
}

/** The sport, and the kind only when it is a friendly — a card's sport word in parts. */
function sportParts(sport: Sport, kind: GameKind): readonly string[] {
  return kind === 'forFun' ? [sportLabel(sport), PROPOSALS_COPY.kind.forFun] : [sportLabel(sport)];
}

/** *Padel* · *Padel · For fun* — a card's sport word. */
export function sportWords(sport: Sport, kind: GameKind): string {
  return sportParts(sport, kind).join(LINE_JOIN);
}

/** *Padel · booked* — the details' second line: the sport, and the status in lower case. */
export function statusSubline(sport: Sport, status: HomeStatus): string {
  return `${sportLabel(sport)}${LINE_JOIN}${COPY.statusInLine[status]}`;
}

/**
 * *Court 2 · 3,1 km* — WHERE's aside: the court once it is given, and how far the club is when that
 * is known. Nothing when neither is.
 */
export function whereAside(
  game: Pick<HomeGame, 'status' | 'courtName'>,
  distanceKm: number | undefined,
): string | undefined {
  const parts = [
    ...(courtIsGiven(game.status) ? [game.courtName] : []),
    ...(distanceKm === undefined ? [] : [formatDistanceKm(distanceKm)]),
  ];
  return parts.length === 0 ? undefined : parts.join(LINE_JOIN);
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

/**
 * **The details' money row** (the screens A4.1), read off the card's own money line
 * (`moneyLineOf`): *PAID · 28 zł · your share · to the club*, with *· free to leave until Sat 10:00*
 * while the cut-off is ahead (`cutOffAhead`, the line's own fold); the share nobody pays yet while
 * the club decides; *Refunded*, or *nobody paid*, once the game is called off.
 */
export function moneyRow(
  game: Pick<BookedGame, 'status' | 'money' | 'where' | 'sides'>,
  seats: number,
  now: number,
): FactWords {
  const { money } = game;
  const words = COPY.details;
  const value = formatZloty(money.shareGrosze);
  const line = moneyLineOf({ ...game, club: game.where }, seats, now);

  if (line?.kind === 'calledOff') {
    return line.refundedGrosze === undefined
      ? { label: words.yourShare, value, aside: words.nobodyPaid }
      : { label: words.refunded, value };
  }
  if (line?.kind === 'waiting') {
    return {
      label: words.yourShare,
      value,
      aside: `${words.nobodyPaysUntil} ${line.club ?? COPY.money.theClub} ${COPY.money.confirms}`,
    };
  }

  const until = cutOffAhead(money, now);
  return {
    label: money.paid ? words.paid : words.yourShare,
    value,
    aside: [
      words.toTheClub,
      ...(until === undefined ? [] : [`${COPY.money.freeToLeaveUntil} ${shortMoment(until)}`]),
    ].join(LINE_JOIN),
  };
}

/** *Your check-in code: K 7 M 2 Q X* — the short code aloud, a character at a time. */
export function shortCodeSpoken(code: string): string {
  return `${COPY.details.codeSpoken}: ${[...code].join(' ')}`;
}

/**
 * **A Home card, spoken** — one element with no action, as the Classic card's body is: *Booked,
 * new. Padel. Bonarka Arena, Court 2. Saturday, 16:00 until 17:00. Paid, 30 zł. Chat open.* *Open
 * game* is an element of its own, so its verb is not here.
 */
export function homeCardLabel({
  game,
  fresh,
  day,
  money,
  chat,
}: {
  readonly game: Pick<HomeGame, 'status' | 'sport' | 'kind' | 'club' | 'courtName' | 'startsAt'>;
  /** Marked *new*. */
  readonly fresh: boolean;
  /** The game's day, or nothing for an instant that names no day. */
  readonly day: GameDay | undefined;
  /** The money line, or nothing. */
  readonly money: MoneyLine | undefined;
  /** The game's chat is open. */
  readonly chat: boolean;
}): string {
  const time = timeWords(game.startsAt);
  const where = courtIsGiven(game.status)
    ? `${clubName(game)}${SPOKEN_JOIN}${game.courtName}`
    : clubName(game);
  return [
    fresh ? `${statusWord(game.status)}${SPOKEN_JOIN}${COPY.newSpoken}` : statusWord(game.status),
    sportParts(game.sport, game.kind).join(SPOKEN_JOIN),
    where,
    [...(day === undefined ? [] : [gameDayWords(day)]), `${time.from} ${time.until}`].join(
      SPOKEN_JOIN,
    ),
    ...(money === undefined ? [] : [moneySpoken(money)]),
    ...(chat ? [COPY.chatOpenSpoken] : []),
  ]
    .map((sentence) => `${sentence}.`)
    .join(' ');
}
