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
  moneyLineOf,
  paymentOf,
  shareAt,
  stakeOnTheDetails,
  type BookedGame,
  type HomeGame,
  type LateRefund,
  type Leaving,
  type MoneyLine,
  type ShareAt,
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

import {
  answersByWords,
  clubName,
  gameDayWords,
  LINE_JOIN,
  paymentAwaitedClauses,
  shortMoment,
  timeWords,
  waitingWords,
  yourPaymentWords,
} from './deckPresentation';
import { seatWhen } from './fillInPresentation';
import { seatKeptBy } from './fillPresentation';
import type { FactWords } from './GameFacts';
import { HOME_GAME_COPY } from './homeCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = HOME_GAME_COPY;

/** A drawn line's parts aloud: the mocks' dots are commas to a listener. */
const SPOKEN_JOIN = ', ';

/**
 * `YOUR GAMES · n` — **the heading over Home's rail and its count**, which is the one number on
 * that screen. A rail pages through everything it holds, so the count is what says how much there
 * is; the dots under it say where you are, and neither is the other. Drawn uppercase by 3.3's
 * section rule, and never `h2`.
 */
export function gamesHeading(count: number): string {
  return `${COPY.heading} · ${count}`;
}

/**
 * **The status's colour** — the tag's dot and the facts' accent line (A4.1, A8): *Waiting for the
 * club*, *Waiting for one payment* and *Seat open* amber, *Booked* mint, *Called off* red, and the
 * result states as the old loop's cards drew them (needs a result and confirm amber, counted mint,
 * the other two ends hairline). On the dark card the amber is `arranging` and the red `gameRed`,
 * each the shade that carries on that ground.
 */
export const STATUS_INK: Readonly<Record<HomeStatus, string>> = {
  WAITING_FOR_THE_CLUB: theme.color.arranging,
  WAITING_FOR_A_PAYMENT: theme.color.arranging,
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
 * being arranged while it fills, while its club decides and while one payment is awaited
 * (`arranging`), mint once booked, red when the club turned it down, the hairline on the three ways
 * it ended unfilled — the colours above, for the same facts on a game that has not filled.
 */
export const PROPOSAL_STATUS_INK: Readonly<Record<ProposalStatus, string>> = {
  FILLING: theme.color.arranging,
  WAITING_FOR_THE_CLUB: theme.color.arranging,
  WAITING_FOR_A_PAYMENT: theme.color.arranging,
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
  WAITING_FOR_A_PAYMENT: 'settled',
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
      if (line.paid) return [money.paid, share];
      return [
        share,
        ...(line.freeToLeaveUntil === undefined
          ? []
          : [`${money.freeToLeaveUntil} ${shortMoment(line.freeToLeaveUntil)}`]),
      ];
    }
    case 'waiting':
      return line.answerBy === undefined
        ? [`${money.nobodyPaysUntil} ${line.club ?? money.theClub} ${money.confirms}`]
        : [answersByWords(line.club, line.answerBy), money.nobodyPaysUntilItConfirms];
    case 'seatOpen': {
      const open = counted(line.seats, money.seatOpen, money.seatsOpen);
      return line.fillsBy === undefined
        ? [open, money.offeredToOthers, money.goesAhead]
        : [open, `${money.fillsBy} ${shortMoment(line.fillsBy)} ${money.orTheGameIsOff}`];
    }
    case 'fillingAgain':
      return [
        counted(line.seats, money.seatOpen, money.seatsOpen),
        line.clubConfirms
          ? `${line.club ?? money.theClub} ${money.askedAgain}`
          : money.booksWhenFull,
        money.nobodyPaidInLine,
      ];
    case 'paymentAwaited':
      return paymentAwaitedClauses(line.until);
    case 'yourPayment':
      return [yourPaymentWords(line)];
    case 'calledOff':
      return [
        ...(line.reason === undefined ? [] : [calledOffWhy({ ...line, reason: line.reason })]),
        line.refundedGrosze === undefined
          ? nothingCameBack(line.reason, money)
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
 * **What each reason a game is off says of the club** — `ofTheClub`, said with the club's name
 * before it (the rest are said of the game); `answer`, the club's answer to a request — its no or
 * its silence — told in the notice's and the email's words, a new card promised first (Q105). A
 * `Record`, so a reason the wire adds is placed here before it can be drawn.
 */
const SAID_OF_THE_CLUB: Readonly<
  Record<CalledOffReason, { readonly ofTheClub: boolean; readonly answer: boolean }>
> = {
  REFUSED: { ofTheClub: true, answer: true },
  NO_ANSWER: { ofTheClub: true, answer: true },
  CANCELLED_BY_THE_CLUB: { ofTheClub: true, answer: false },
  SHORT_AT_THE_CUT_OFF: { ofTheClub: false, answer: false },
  BOOK_BY_PASSED: { ofTheClub: false, answer: false },
  COURT_HOUR_LOST: { ofTheClub: false, answer: false },
  PAYMENT_NOT_IN_TIME: { ofTheClub: false, answer: false },
};

/**
 * **The reasons a game is off whose shares were held and let go** (Q113, the mechanics §14.1) — at
 * the cut-off, or by the club's cancel before it — where nothing came back because *nothing was
 * taken*. On every other reason nothing was ever held. A `Record`, so a reason the wire adds is
 * placed here first.
 */
const HOLDS_LET_GO: Readonly<Record<CalledOffReason, boolean>> = {
  SHORT_AT_THE_CUT_OFF: true,
  CANCELLED_BY_THE_CLUB: true,
  REFUSED: false,
  NO_ANSWER: false,
  BOOK_BY_PASSED: false,
  COURT_HOUR_LOST: false,
  PAYMENT_NOT_IN_TIME: false,
};

/**
 * *Nothing was taken* where the holds were let go; else *Nobody paid*, and after the club's no or its
 * silence *— you'll get a new card first* (Q105, the screens A8): a game off with nothing given back,
 * in the card's words or the details', whichever `words` are handed in.
 */
function nothingCameBack(
  reason: CalledOffReason | undefined,
  words: {
    readonly nothingWasTaken: string;
    readonly nobodyPaid: string;
    readonly nobodyPaidNewCardFirst: string;
  },
): string {
  if (reason === undefined) return words.nobodyPaid;
  if (HOLDS_LET_GO[reason]) return words.nothingWasTaken;
  return SAID_OF_THE_CLUB[reason].answer ? words.nobodyPaidNewCardFirst : words.nobodyPaid;
}

/**
 * *A seat was still empty at the cut-off* · *Kazimierz Padel said no* · *Bonarka Arena cancelled it
 * because of the weather* — why a game is off: the club named for the three that are the club's,
 * with its own reason after a cancel (#547); its no and its silence in the notice's words (Q105).
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
  if (!SAID_OF_THE_CLUB[reason].ofTheClub) return why;
  const clause =
    reason === 'CANCELLED_BY_THE_CLUB' && clubCancelReason !== undefined
      ? COPY.money.clubCancelled[clubCancelReason]
      : undefined;
  return [club ?? COPY.money.theClubLead, why, ...(clause === undefined ? [] : [clause])].join(' ');
}

/**
 * ***Kazimierz Padel said no*** · ***… didn't answer in time*** — **the club's answer to a game it
 * turned down** (Q105), off its booking's reason: the filling details' tag, which their own read
 * cannot say, since it names one status for both. Nothing for any other ending.
 */
export function clubsAnswer(
  booking: Pick<BookedGame, 'calledOffReason' | 'where'>,
): string | undefined {
  const reason = booking.calledOffReason;
  if (reason === undefined || !SAID_OF_THE_CLUB[reason].answer) return undefined;
  const club = booking.where.name;
  return calledOffWhy({ reason, ...(club === undefined ? {} : { club }) });
}

/**
 * **The line under a Home card**: *30 zł · free to leave until Sat 17:00*, *Paid · 30 zł*, *Bonarka
 * answers by 20:45 · Nobody pays until it confirms*, *1 seat open · fills by Sat 17:00 or the game is
 * off and nothing is taken*, *Refunded 30 zł*.
 */
export function moneyWords(line: MoneyLine): string {
  return moneyParts(line).join(LINE_JOIN);
}

/** The same line aloud: *30 zł, free to leave until Fri 16:00*. */
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
  game: Pick<HomeGame, 'status' | 'fillingAgain' | 'courtName'>,
  distanceKm: number | undefined,
): string | undefined {
  const parts = [
    ...(courtIsGiven(game) && game.courtName !== undefined ? [game.courtName] : []),
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
 * (`moneyLineOf`), **its words always on a line of their own under the figure** (`below`, the
 * user's ruling of 2026-10-10): a booked game says when the share is held and when it is taken
 * (`shareAt`, Q113) — *YOUR SHARE 28 zł* over *Held on your card · taken Sat 10:00 · free to leave
 * until then*, or *Held from Tue 10:00 · taken Sat 10:00* while it is only checked, and *PAID 28 zł*
 * over *Paid* once it is taken; the share nobody pays yet while the
 * club decides, over *Bonarka answers by 20:45 · Nobody
 * pays until it confirms* — the card's own line — until its deadline passes (Q98); the share nobody
 * pays yet over *Waiting for one payment · until 14:40 · Nobody pays until it's in*, or the payer's
 * own *Confirm your payment by 14:40* (Q111) — *Fix your card by 14:40* before the cut-off (Q113),
 * and on a booked game whose holding was refused *Fix your card by 14:40 to keep your seat*, the
 * game still booked (#639); and on a game a
 * player left, one called off or one that started short, the card's own line under the share —
 * *1 seat open · fills by Fri 16:00 or the game is off…*, why it is off with what came back, *A seat
 * was empty* (§14.1). A full game gone back to filling is the share nobody pays over the card's
 * *1 seat open · Kazimierz Padel is asked again when it's full · nobody paid* (Q106). **A rescue
 * seen from outside** (A4.3) is the share *I'm in* would pay over how long the seat is offered — the
 * *Seats to fill* row's own words — or, while a refused rescuer's seat is kept for them, their time:
 * *Fix your card by 14:40 to take the seat* (#640).
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
    | 'answerBy'
    | 'fillingAgain'
    | 'paymentDueBy'
    | 'yourPaymentDueBy'
    | 'timeTo'
  >,
  now: number,
): FactWords {
  const { money } = game;
  const words = COPY.details;
  const value = formatZloty(money.shareGrosze);
  const held = shareAt(money, now);
  const share = held?.kind === 'taken' ? words.paid : words.yourShare;

  const line = moneyLineOf({ ...game, club: game.where }, now);
  // A refused rescuer's seat is kept for them alone until their time runs out (#640): their time.
  if (game.rescue !== undefined && line?.kind !== 'yourPayment') {
    return { label: words.yourShare, value, below: seatWhen(game.rescue) };
  }
  switch (line?.kind) {
    case 'calledOff': {
      const why = line.reason === undefined ? [] : [calledOffWhy({ ...line, reason: line.reason })];
      return line.refundedGrosze === undefined
        ? {
            label: words.yourShare,
            value,
            below: [...why, nothingCameBack(line.reason, words)].join(LINE_JOIN),
          }
        : {
            label: words.refunded,
            value: formatZloty(line.refundedGrosze),
            ...(why.length === 0 ? {} : { below: why.join(LINE_JOIN) }),
          };
    }
    case 'waiting':
      return { label: words.yourShare, value, below: waitingWords(line.club, line.answerBy) };
    case 'yourPayment':
      // With the seat at stake where the tag does not say it (`stakeOnTheDetails`, the screens A4.1).
      return { label: share, value, below: seatKeptBy(line, stakeOnTheDetails(game)) };
    case 'paymentAwaited':
    case 'seatOpen':
    case 'fillingAgain':
    case 'seatEmpty':
    case 'noShow':
      return { label: share, value, below: moneyWords(line) };
    case 'booked':
    case undefined: {
      const below = held === undefined ? undefined : heldWords(held);
      return { label: share, value, ...(below === undefined ? {} : { below }) };
    }
  }
}

/**
 * *Held on your card · taken Sat 10:00 · free to leave until then* · *Held from Tue 10:00 · taken
 * Sat 10:00* · *Paid* — **when the share is held and when it is taken** (Q113; the screens A4.1), on
 * the club's clock as *fills by* writes it. A 40 zł hold that appeared and vanished the day a game
 * filled far ahead is the card check this explains.
 */
function heldWords(share: ShareAt): string {
  const words = COPY.details;
  switch (share.kind) {
    case 'held':
      return [
        words.heldOnYourCard,
        `${words.taken} ${shortMoment(share.takenAt)}`,
        words.freeToLeaveUntilThen,
      ].join(LINE_JOIN);
    case 'checked':
      return [
        `${words.heldFrom} ${shortMoment(share.heldFrom)}`,
        `${words.taken} ${shortMoment(share.takenAt)}`,
      ].join(LINE_JOIN);
    case 'taken':
      return COPY.money.paid;
  }
}

/**
 * **A Home card, spoken** — one element with no action, as the Classic card's body is: *Booked,
 * new. Padel. Bonarka Arena, Court 2. Saturday, 16:00 until 17:00. Paid, 30 zł.* *Open game* and
 * the bubble's *Open the chat* are elements of their own (Q100), so neither verb is here.
 */
export function homeCardLabel({
  game,
  fresh,
  day,
  money,
}: {
  readonly game: Pick<
    HomeGame,
    'status' | 'fillingAgain' | 'sport' | 'kind' | 'club' | 'courtName' | 'startsAt'
  >;
  /** Marked *new*. */
  readonly fresh: boolean;
  /** The game's day, or nothing for an instant that names no day. */
  readonly day: GameDay | undefined;
  /** The money line, or nothing. */
  readonly money: MoneyLine | undefined;
}): string {
  const time = timeWords(game.startsAt);
  const where =
    courtIsGiven(game) && game.courtName !== undefined
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
  ]
    .map((sentence) => `${sentence}.`)
    .join(' ');
}

// ---------------------------------------------------------------------------
// Leave the game (the mechanics §13; #557)
// ---------------------------------------------------------------------------

/**
 * ***you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*** after the clause's
 * opening — the read's two figures as they come, and the payment they make together.
 */
function backIfTaken(opening: string, refund: LateRefund): string {
  const words = COPY.leave;
  const back = formatZloty(refund.backGrosze);
  const paid = formatZloty(paymentOf(refund));
  const kept = formatZloty(refund.keptGrosze);
  return `${opening} ${back} ${words.back} (${paid} ${words.lessThe} ${kept} ${words.keptOnYourPayment})`;
}

/**
 * **The line under *Leave the game*** — what leaving costs at this moment, from the read (Q113):
 * *Free to leave now — nothing is taken* before the cut-off; after it *If someone takes your seat,
 * you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*, or only *Your seat is
 * offered to others* while the read quotes no figure (#644); *Nobody has paid yet* while the club
 * decides.
 */
export function leavingLine(leaving: Leaving): string {
  const words = COPY.leave;
  switch (leaving.kind) {
    case 'BEFORE_THE_CUT_OFF':
      return words.freeNow;
    case 'AFTER_THE_CUT_OFF':
      return leaving.lateRefund === undefined
        ? words.offered
        : backIfTaken(words.ifSomeoneTakesYourSeat, leaving.lateRefund);
    case 'WHILE_WAITING_FOR_THE_CLUB':
      return words.nobodyPaidYet;
  }
}

/**
 * **The sheet's words** — the mechanics §13's table, a line a clause: before the cut-off nothing is
 * taken, and the hold on the card is let go when there is one (`leavingAt`); after it the seat is
 * offered and comes back less exactly what was kept on the payment if it is taken — a clause given
 * only with the read's figure, never without one (#644).
 */
export function leavingSheetBody(leaving: Leaving): readonly string[] {
  const words = COPY.leave;
  switch (leaving.kind) {
    case 'BEFORE_THE_CUT_OFF':
      return [
        leaving.letsAHoldGo === true ? words.holdLetGo : words.nothingTaken,
        `${words.offered}.`,
        words.onRecordIfCalledOff,
      ];
    case 'AFTER_THE_CUT_OFF':
      return [
        `${words.offered}.`,
        ...(leaving.lateRefund === undefined
          ? []
          : [`${backIfTaken(words.ifSomeoneTakesIt, leaving.lateRefund)}; ${words.ifNobodyDoes}`]),
        words.onRecordIfNobody,
      ];
    case 'WHILE_WAITING_FOR_THE_CLUB':
      return [`${words.nobodyPaidYet}.`, words.withdrawsYourYes];
  }
}

/** **The toast once the player has left** — which of the three the server says it was (Q113). */
export function leftToast(left: LeavingKind): string {
  const words = COPY.leave;
  switch (left) {
    case 'BEFORE_THE_CUT_OFF':
      return `${words.left} ${words.nothingWasTaken}`;
    case 'AFTER_THE_CUT_OFF':
      return `${words.left} ${words.offered}.`;
    case 'WHILE_WAITING_FOR_THE_CLUB':
      return `${words.left} ${words.yesWithdrawn}`;
  }
}

/** A refused departure, said on the sheet — the route's three codes over the shared sentence. */
export function leaveRefusal(error: AppError): string {
  return codeMessage(COPY.leave.refused, error);
}
