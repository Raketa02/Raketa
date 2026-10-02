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
import { codeMessage, type AppError } from '@/shared/errors';
import { counted } from '@/shared/formatting/counted';
import { formatDistanceKm, formatZloty } from '@/shared/formatting/ratingFormat';
import { platformClock } from '@/shared/date/platformZone';
import { theme, type ButtonVariant } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  courtIsGiven,
  cutOffAhead,
  moneyLineOf,
  type BookedGame,
  type HomeGame,
  type Leaving,
  type MoneyLine,
} from '../domain/home';
import type {
  CalledOffReason,
  ClubCancelReason,
  GameKind,
  HomeStatus,
  LeavingKind,
  ProposalStatus,
} from '../domain/vocabulary';
import type { GameDay } from '../domain/when';

import { clubName, gameDayWords, LINE_JOIN, shortMoment, timeWords } from './deckPresentation';
import { seatWhen } from './fillInPresentation';
import type { FactWords } from './GameFacts';
import { HOME_GAME_COPY } from './homeCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = HOME_GAME_COPY;

/** A drawn line's parts aloud: the mocks' dots are commas to a listener. */
const SPOKEN_JOIN = ', ';

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
 * **A game still filling's status, coloured** — its details' dot and accent line: the stage still
 * being arranged while it fills and while its club decides (`arranging`), mint once booked, red when
 * the club turned it down, the hairline on the three ways it ended unfilled — the colours above, for
 * the same facts on a game that has not filled.
 */
export const PROPOSAL_STATUS_INK: Readonly<Record<ProposalStatus, string>> = {
  FILLING: theme.color.arranging,
  WAITING_FOR_THE_CLUB: theme.color.arranging,
  FILLED: theme.color.mint,
  EXPIRED: theme.color.onDarkHair,
  WITHDRAWN: theme.color.onDarkHair,
  COURT_HOUR_LOST: theme.color.onDarkHair,
  TURNED_DOWN: theme.color.gameRed,
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
        ...(line.reason === undefined ? [] : [calledOffWhy({ ...line, reason: line.reason })]),
        line.refundedGrosze === undefined
          ? money.nobodyPaid
          : `${money.refunded} ${formatZloty(line.refundedGrosze)}`,
      ];
    case 'seatEmpty':
      return [money.seatEmpty, money.noLevelMoved];
    case 'noShow':
      return line.yours
        ? [money.youWereMarked, money.sayIfYouWere]
        : [money.somebodyDidNotCome, money.noLevelMoved];
  }
}

/**
 * *A seat was still empty at the cut-off* · *Kazimierz Padel couldn't take it* · *Bonarka Arena
 * cancelled it because of the weather* — why a game is off: the club named for the three that are
 * the club's, with its own reason after a cancel (#547).
 */
function calledOffWhy({
  reason,
  club,
  clubCancelReason,
}: {
  readonly reason: CalledOffReason;
  readonly club?: string;
  readonly clubCancelReason?: ClubCancelReason;
}): string {
  const why = COPY.money.calledOff[reason];
  if (reason === 'SHORT_AT_THE_CUT_OFF') return why;
  const clause =
    reason === 'CANCELLED_BY_THE_CLUB' && clubCancelReason !== undefined
      ? COPY.money.clubCancelled[clubCancelReason]
      : undefined;
  return [club ?? COPY.money.theClubLead, why, ...(clause === undefined ? [] : [clause])].join(' ');
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
    ...(courtIsGiven(game.status) && game.courtName !== undefined ? [game.courtName] : []),
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
 * the club decides; and on a game a player left, one called off or one that started short, the card's
 * own line beside the share — *1 seat open · fills by Fri 16:00 or the game is off…*, why it is off
 * with what came back, *A seat was empty* (§14.1). **A rescue seen from outside** (A4.3) is the share
 * *I'm in* would pay and how long the seat is offered — the *Seats to fill* row's own words.
 */
export function moneyRow(
  game: Pick<
    BookedGame,
    | 'status'
    | 'money'
    | 'where'
    | 'openSeats'
    | 'calledOffReason'
    | 'clubCancelReason'
    | 'uncountedReason'
    | 'needsYou'
    | 'rescue'
  >,
  now: number,
): FactWords {
  const { money } = game;
  const words = COPY.details;
  const value = formatZloty(money.shareGrosze);
  const share = money.paid ? words.paid : words.yourShare;

  if (game.rescue !== undefined) {
    return { label: words.yourShare, value, aside: seatWhen(game.rescue) };
  }

  const line = moneyLineOf({ ...game, club: game.where }, now);
  switch (line?.kind) {
    case 'calledOff': {
      const why = line.reason === undefined ? [] : [calledOffWhy({ ...line, reason: line.reason })];
      return line.refundedGrosze === undefined
        ? { label: words.yourShare, value, aside: [...why, words.nobodyPaid].join(LINE_JOIN) }
        : {
            label: words.refunded,
            value: formatZloty(line.refundedGrosze),
            ...(why.length === 0 ? {} : { aside: why.join(LINE_JOIN) }),
          };
    }
    case 'waiting':
      return {
        label: words.yourShare,
        value,
        aside: `${words.nobodyPaysUntil} ${line.club ?? COPY.money.theClub} ${COPY.money.confirms}`,
      };
    case 'seatOpen':
    case 'seatEmpty':
    case 'noShow':
      return { label: share, value, aside: moneyWords(line) };
    case 'booked':
    case undefined: {
      const until = cutOffAhead(money, now);
      return {
        label: share,
        value,
        aside: [
          words.toTheClub,
          ...(until === undefined ? [] : [`${COPY.money.freeToLeaveUntil} ${shortMoment(until)}`]),
        ].join(LINE_JOIN),
      };
    }
  }
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
  const where =
    courtIsGiven(game.status) && game.courtName !== undefined
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

// ---------------------------------------------------------------------------
// Leave the game (the mechanics §13; #557)
// ---------------------------------------------------------------------------

/**
 * **The line under *Leave the game*** — what leaving costs at this moment, from the read: *Refunded
 * 27,18 zł if you leave now* before the cut-off, *Refunded 27,18 zł only if someone takes your seat*
 * after it, *Nobody has paid yet* while the club decides.
 */
export function leavingLine(leaving: Leaving): string {
  const refund = formatZloty(leaving.refundGrosze);
  switch (leaving.kind) {
    case 'BEFORE_THE_CUT_OFF':
      return `Refunded ${refund} if you leave now`;
    case 'AFTER_THE_CUT_OFF':
      return `Refunded ${refund} only if someone takes your seat`;
    case 'WHILE_WAITING_FOR_THE_CLUB':
      return COPY.leave.nobodyPaidYet;
  }
}

/** **The sheet's words** — the mechanics §13's table, a line a clause, the sums the read's. */
export function leavingSheetBody(leaving: Leaving): readonly string[] {
  const words = COPY.leave;
  const refund = formatZloty(leaving.refundGrosze);
  switch (leaving.kind) {
    case 'BEFORE_THE_CUT_OFF':
      return [
        `You’ll be refunded ${refund} now (the ${formatZloty(leaving.cardFeeGrosze)} card fee isn’t returned).`,
        words.offered,
        words.onRecordIfCalledOff,
      ];
    case 'AFTER_THE_CUT_OFF':
      return [
        words.offered,
        `You’ll be refunded ${refund} when someone takes it; if nobody does, you won’t be.`,
        words.onRecordIfNobody,
      ];
    case 'WHILE_WAITING_FOR_THE_CLUB':
      return [`${words.nobodyPaidYet}.`, words.withdrawsYourYes];
  }
}

/**
 * **The toast once the player has left** — which of the three the server says it was, and the
 * refund the sheet quoted, with how long it takes to arrive (§12.3: *shown when it is issued*).
 */
export function leftToast(left: LeavingKind, quoted: Leaving): string {
  const words = COPY.leave;
  switch (left) {
    case 'BEFORE_THE_CUT_OFF':
      return `${words.left} ${formatZloty(quoted.refundGrosze)} is on its way back — ${words.refundTakes}`;
    case 'AFTER_THE_CUT_OFF':
      return `${words.left} ${words.offered}`;
    case 'WHILE_WAITING_FOR_THE_CLUB':
      return `${words.left} ${words.yesWithdrawn}`;
  }
}

/** A refused departure, said on the sheet — the route's three codes over the shared sentence. */
export function leaveRefusal(error: AppError): string {
  return codeMessage(COPY.leave.refused, error);
}
