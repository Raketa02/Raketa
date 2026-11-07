/**
 * **A friends game's sentences built from a value** — the send sheet's order and cover line, an
 * invitation's title, clock, line and answers, the sender's seats line and the details' seats
 * ([#759](https://github.com/Raketa02/Raketa/issues/759); the words §29.7–§29.10). The fixed words
 * are `friendsGameCopy.ts`'s.
 */

import { sportLabel } from '@/features/onboarding/types';
import type { AppError } from '@/shared/errors';
import { codeMessage } from '@/shared/errors';
import { platformClock } from '@/shared/date/platformZone';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { sentenceList } from '@/shared/formatting/sentenceList';

import { countdownOf, type DeckPerson } from '../domain/deck';
import {
  gamesPerWeekOf,
  waitingCapOf,
  type FriendsGame,
  type FriendsGameInvitation,
  type InvitationFace,
  type SeatShown,
  type SeatsLine,
} from '../domain/friendsGame';
import type { PayMode } from '../domain/vocabulary';
import { gameDayOf } from '../domain/when';

import {
  LINE_JOIN,
  countdownSpoken,
  countdownWords,
  gameDayWords,
  shortMoment,
  tileName,
} from './deckPresentation';
import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = FRIENDS_GAME_COPY;

/** A line's clauses aloud — commas, where the drawn line has dots. */
const SPOKEN_JOIN = ', ';

// ---------------------------------------------------------------------------
// The send sheet
// ---------------------------------------------------------------------------

/** *Send game and pay 25 zł* — the order button, naming what it charges. */
export function sendLabel(chargeGrosze: number): string {
  return `Send game and pay ${formatZloty(chargeGrosze)}`;
}

/**
 * ***We hold 100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł for any seat still
 * empty then.*** (§29.7) — *Split*'s maximum, right above the order button; in singles *… if the
 * other seat is still empty then.*
 */
export function coverLine({
  priceGrosze,
  shareGrosze,
  cutOff,
  singles,
}: {
  readonly priceGrosze: number;
  readonly shareGrosze: number;
  readonly cutOff: string | undefined;
  readonly singles: boolean;
}): string {
  const until = cutOff === undefined ? COPY.send.theClubsCutOff : shortMoment(cutOff);
  const share = formatZloty(shareGrosze);
  const then = singles ? 'if the other seat is still empty then' : 'for any seat still empty then';
  return `We hold ${formatZloty(priceGrosze)} on your card until ${until}. You pay ${share}, plus ${share} ${then}.`;
}

/** *Split the cost* / *Pay the whole court* — a choice card's title. */
export function payModeTitle(mode: PayMode): string {
  return COPY.send.payMode[mode];
}

/** *Split the cost, 25 zł* — a choice card, spoken with what its button charges. */
export function payModeSpoken(mode: PayMode, chargeGrosze: number): string {
  return `${payModeTitle(mode)}, ${formatZloty(chargeGrosze)}`;
}

/**
 * **Why a send was refused, in the sheet** (§29.7) — two games already waiting, the sender's own
 * hour or week in the invitee's two sentences with the sender's numbers, and the court's sentence
 * the deck already says; otherwise the code over the recovery sentence every screen shares.
 */
export function sendRefusal(error: AppError, startsAt: string): string {
  switch (error.code) {
    case 'friends_games_waiting':
      return `You have ${waitingCapOf(error.details)} friends games waiting for answers. Send this one once one of them is settled.`;
    case 'you_play_then':
    case 'games_per_week_booked':
      return weekOrHourRefusal(error, startsAt);
    case 'court_hour_not_for_sale':
      return COPY.send.refused.courtGone;
    default:
      return codeMessage(PROPOSALS_COPY.refused, error);
  }
}

/**
 * ***Your week is full: 3 games, the most you set in Games & money.*** and ***You already have a
 * game at 10:00.*** (§29.8) — an invitee's *Accept*, and the sender's send with their own numbers.
 */
function weekOrHourRefusal(error: AppError, startsAt: string): string {
  if (error.code === 'you_play_then') {
    return `You already have a game at ${platformClock(startsAt) ?? ''}.`;
  }
  const games = gamesPerWeekOf(error.details);
  if (games === undefined) return 'Your week is full, the most you set in Games & money.';
  return `Your week is full: ${games} ${games === 1 ? 'game' : 'games'}, the most you set in Games & money.`;
}

// ---------------------------------------------------------------------------
// FRIENDS GAME · n
// ---------------------------------------------------------------------------

/** *FRIENDS GAME · 1* — the row's title; nothing is drawn at nought. */
export function friendsGamesHeading(count: number): string {
  return `Friends game · ${count}`;
}

/** *tomek.k's game* — or *A friend's game* for a sender the read can no longer name. */
export function gameOf(sender: string | undefined): string {
  return sender === undefined ? 'A friend’s game' : `${sender}’s game`;
}

/** *tomek.k paid the court* — Whole court, on the invitation and under the details' price. */
export function paidTheCourt(sender: string | undefined): string {
  return `${sender ?? COPY.theSender} paid the court`;
}

/**
 * **The invitation's clock** — the deck ribbon's countdown, cited (*21 h 00*, *45 min*), coral
 * under an hour; and spoken.
 */
export function invitationClock(
  until: string | undefined,
  now: number,
): { readonly words: string; readonly spoken: string; readonly urgent: boolean } | undefined {
  if (until === undefined) return undefined;
  const countdown = countdownOf(until, now);
  const words = countdownWords(countdown);
  const spoken = countdownSpoken(countdown);
  if (words === undefined || spoken === undefined) return undefined;
  return { words, spoken: `${spoken} to answer`, urgent: countdown.kind === 'minutes' };
}

/**
 * ***Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive*** (§29.8; the README's note 7) —
 * the game's day and hour as the deck's court block writes them, the club, the court, the sport and
 * the kind.
 */
export function invitationLine(
  invitation: Pick<FriendsGameInvitation, 'startsAt' | 'club' | 'courtName' | 'sport' | 'kind'>,
  now: number,
): string {
  const day = gameDayOf(invitation.startsAt, now);
  const when = [
    day === undefined ? undefined : gameDayWords(day),
    platformClock(invitation.startsAt),
  ]
    .filter((part): part is string => part !== undefined)
    .join(' ');
  return [
    when,
    invitation.club.name ?? PROPOSALS_COPY.unknownClub,
    invitation.courtName,
    sportLabel(invitation.sport),
    PROPOSALS_COPY.kind[invitation.kind],
  ]
    .filter((part) => part !== '')
    .join(LINE_JOIN);
}

/** **The invitation's answer**, by the pay mode (§29.8). */
const ACCEPT: Readonly<Record<PayMode, (shareGrosze: number) => string>> = {
  SPLIT_THE_COST: (share) => `Accept and pay ${formatZloty(share)}`,
  WHOLE_COURT: () => COPY.invitation.accept,
};

/** *Accept and pay 25 zł* with *Split*; *Accept* with *Whole court*. */
export function acceptLabel(game: Pick<FriendsGame, 'payMode'>, shareGrosze: number): string {
  return ACCEPT[game.payMode](shareGrosze);
}

/** The answers aloud, naming whose game — the row may hold two. */
export function acceptSpoken(label: string, sender: string | undefined): string {
  return `${label}, ${gameOf(sender)}`;
}

export function notThisTimeSpoken(sender: string | undefined): string {
  return `${COPY.invitation.notThisTime}, ${gameOf(sender)}`;
}

/** *tomek.k, in. magda.p, in. ania.k, still to answer. You* — an invitation's faces, as one sentence. */
export function facesSpoken(faces: readonly InvitationFace[]): string {
  return faces
    .map(({ person, isIn, faded }) => {
      const name = person.isYou ? COPY.you : tileName(person);
      if (isIn) return `${name}, ${COPY.invitation.in}`;
      return faded ? `${name}, ${COPY.invitation.stillToAnswer}` : name;
    })
    .join('. ');
}

/** A face's name under it — *You* for the reader. */
export function faceName(person: DeckPerson): string {
  return person.isYou ? COPY.you : tileName(person);
}

/**
 * **Why an *Accept* was refused, on the card** (§29.8) — a full week or a game at that hour; an
 * invitation that ended; otherwise the deck's own sentence for the code.
 */
export function answerRefusal(error: AppError, startsAt: string): string {
  switch (error.code) {
    case 'you_play_then':
    case 'games_per_week_booked':
      return weekOrHourRefusal(error, startsAt);
    case 'invitation_not_waiting':
      return COPY.invitation.refused.invitation_not_waiting;
    default:
      return codeMessage(PROPOSALS_COPY.refused, error);
  }
}

// ---------------------------------------------------------------------------
// Your games, and the details
// ---------------------------------------------------------------------------

/**
 * ***2 of 3 friends in · waiting for Ania*** (§29.8) — at nought In, *Waiting for Ania*; with seats
 * empty, *… · 1 seat empty*, *… · 2 seats empty*; both, when both are true. One clause a part:
 * drawn joined by the dots, spoken joined by commas.
 */
function seatsLineParts(line: SeatsLine): readonly string[] {
  const names = line.waitingFor.map((person) => person.name ?? COPY.somebody);
  const waiting = names.length > 0;
  const head =
    waiting && line.friendsIn === 0
      ? [`Waiting for ${sentenceList(names)}`]
      : [
          `${line.friendsIn} of ${line.friendsSeated} friends in`,
          ...(waiting ? [`waiting for ${sentenceList(names)}`] : []),
        ];
  const empty =
    line.empty === 0 ? [] : [`${line.empty} ${line.empty === 1 ? 'seat' : 'seats'} empty`];
  return [...head, ...empty];
}

export function seatsLineWords(line: SeatsLine): string {
  return seatsLineParts(line).join(LINE_JOIN);
}

export function seatsLineSpoken(line: SeatsLine): string {
  return seatsLineParts(line).join(SPOKEN_JOIN);
}

/**
 * **A seat's state on the details** (§29.8): *In* · *waiting · 21 h left* · *can't make it* ·
 * *didn't answer* · *empty*. A wait with less than a minute — or a day or more — left reads
 * *waiting*.
 */
export function seatStateWords(seat: Pick<SeatShown, 'state' | 'waitingUntil'>, now: number) {
  if (seat.state !== 'WAITING') return COPY.seats.state[seat.state];
  const left =
    seat.waitingUntil === undefined
      ? undefined
      : countdownWords(countdownOf(seat.waitingUntil, now));
  return left === undefined ? 'waiting' : `waiting${LINE_JOIN}${left} left`;
}

/** *Split* · *tomek.k paid the court* — the pay mode, under the details' price, by the wire's mode. */
const PAY_MODE_WORDS: Readonly<Record<PayMode, (sender: string | undefined) => string>> = {
  SPLIT_THE_COST: () => COPY.seats.split,
  WHOLE_COURT: paidTheCourt,
};

/**
 * **The pay mode under the details' price** (§29.8) — *Split*, or *tomek.k paid the court*; the
 * sender reads their own as *You paid the court* (a call).
 */
export function payModeWords(
  game: Pick<FriendsGame, 'payMode' | 'senderNickname' | 'youAreTheSender'>,
): string {
  return PAY_MODE_WORDS[game.payMode](game.youAreTheSender ? COPY.you : game.senderNickname);
}

/** *ines.d, waiting · 21 h 00 left* — a seat on the details, spoken. */
export function seatSpoken(seat: SeatShown, now: number): string {
  return `${faceName(seat.person)}, ${seatStateWords(seat, now)}`;
}

/** ***Everyone is told, nobody pays, and the court goes back to Ogrody 33.*** (§29.10) */
export function callOffLine(club: string | undefined): string {
  return `Everyone is told, nobody pays, and the court goes back to ${club ?? 'the club'}.`;
}

/** Why *Call it off* was refused — its own two, else the deck's sentence for the code. */
export function callOffRefusal(error: AppError): string {
  return codeMessage({ ...PROPOSALS_COPY.refused, ...COPY.callOff.refused }, error);
}
