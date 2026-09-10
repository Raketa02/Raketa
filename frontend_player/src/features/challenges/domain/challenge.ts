/**
 * A challenge as this build reads one — and the two questions asked of it.
 *
 * `GET /challenges` is *"every challenge you hold a seat in, newest first"*, and until the
 * Chats tab it had exactly one reader: a send refused with `open_challenge_stands` names
 * nobody, so the client re-reads the list that was always its own to find out who
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §5.1).
 * The second reader is the inbox — `domain/challengeInbox.ts`, which is where every rule about
 * *whose turn it is* lives. This file holds what a challenge **is** and the pair rule read
 * from this side.
 *
 * ## The pair rule, read from this side
 *
 * *"Sharing a line-up makes a pair"*: every occupied seat but your own is somebody you have an
 * open game with, organiser and co-invitees alike, and a seat that declined or lapsed is empty
 * again — so that person is a stranger to you once more the moment they leave.
 *
 * **The clock is not read here, and that is deliberate.** A standing is *"derived from the
 * seats and the clock, never stored"*, and it was derived **at the moment this list was
 * answered**. Folding it again on this side would be a second implementation of a rule whose
 * whole consumer is a name in one sentence, and the two would disagree first about the seat
 * that lapsed between the read and the render. So an ended challenge is one the server called
 * ended, and a seat is out of it when it says it declined or lapsed.
 *
 * **This names nobody the server refused about.** The gate ran server-side and refused whole;
 * all this decides is which of the organiser's **own** open games to point at, which #222 puts
 * on the *embarrassment* side rather than the safety side.
 *
 * ## A standing this build cannot read
 *
 * `standing` is optional, and the absence is *the server sent a code this app is too old for*.
 * `the-words.md` §3 puts a challenge's standing among the five placements that owe a **named
 * gap** rather than a drop — the code *is* the whole line, so the row prints `OUT_OF_DATE_GAP`
 * and stays. The pair rule reads the absence the safe way round: an unreadable standing has
 * not been called ended, so the people on that court stay paired.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';
import type { Sport } from '@/shared/vocabulary/sport';

import type { ChallengeSide, SeatAnswer, Standing, StandingFacts } from './standing';

/** One seat of a challenge: who is in it, what they did about being asked, and by when. */
export interface ChallengeSeat {
  /** Absent on a seat nobody was put in — *an empty seat is a seat*, and it keeps its place. */
  readonly playerId?: string;
  /** Absent while they have not answered, and on a seat nobody was put in. */
  readonly answer?: SeatAnswer;
  /**
   * The whole handle, and never a familiar form derived from it (ADR-0107).
   *
   * Absent on an empty seat and absent where `users` no longer has the account. The seat stays
   * either way — a seat with no handle is still a position on the court, and every sentence
   * that would have named them says `?` instead.
   */
  readonly nickname?: string;
  /**
   * When this seat's answer stops being wanted — **this seat's own**, dated when it was
   * invited.
   *
   * Absent exactly where nobody was asked: an empty seat, the organiser's, and both seats of a
   * challenge born from a mutual yes. A nullable deadline is how a later reader invents one
   * that never existed, so the absence is the fact rather than a gap to fill in.
   */
  readonly answerBy?: string;
}

/**
 * A challenge, as much of it as this build has a reader for.
 *
 * `organiserId` is here rather than a side, because *"**Challenge sent** and **Challenge for
 * you** are one standing read from two sides"* and which one a reader gets is decided by
 * whether the seat is theirs — a `side` field would be that decision taken by a mapper on
 * somebody else's behalf.
 *
 * `readAt` is the instant every standing and deadline on the list was folded against, copied
 * onto each row the way `gameMappers` copies `GameListResponse`'s. It is carried per challenge
 * because the screens hold one at a time, and carrying it is what makes it impossible for a row
 * to print a countdown against a clock the standing beside it never saw.
 */
export interface Challenge {
  readonly challengeId: string;
  readonly organiserId: string;
  /** Absent when the contract sent a code this build has no words for. See the module note. */
  readonly standing?: Standing;
  readonly sport: Sport;
  readonly openedAt: string;
  /** The instant the whole list was folded against. Every duration on the row is read from it. */
  readonly readAt: string;
  /** The court in its fixed order, empty seats included. */
  readonly seats: readonly ChallengeSeat[];
}

/**
 * The three standings that mean **this challenge has ended**.
 *
 * A `Record` keyed by the union rather than a list, for §1's reason: a seventh standing added
 * to the contract fails `pnpm typecheck` here rather than quietly counting as open.
 */
const ENDED: Readonly<Record<Standing, boolean>> = {
  AWAITING_ANSWERS: false,
  ON: false,
  LINE_UP_INCOMPLETE: false,
  DECLINED: true,
  LAPSED: true,
  WITHDRAWN: true,
};

/**
 * Whether a game still stands between the people in it.
 *
 * A standing this build cannot read answers **yes**, and that is the safe direction: the pair
 * rule is what stops somebody being invited into a refusal, so a code nobody here understands
 * keeps the pair rather than releasing it on a guess.
 */
export function challengeStands(challenge: Challenge): boolean {
  return challenge.standing === undefined ? true : !ENDED[challenge.standing];
}

/**
 * Everybody still in this game: an occupied seat that has neither declined nor lapsed.
 *
 * Empty on an ended challenge, which is the whole of *the pair releases when the challenge
 * does* — stated here rather than left to each caller to remember.
 */
export function playersStillIn(challenge: Challenge): readonly string[] {
  if (!challengeStands(challenge)) return [];

  return challenge.seats.flatMap((seat) =>
    seat.playerId === undefined || seat.answer === 'DECLINED' || seat.answer === 'LAPSED'
      ? []
      : [seat.playerId],
  );
}

/**
 * **Who on this court you already have a game with** — the name the refusal would not carry.
 *
 * @param invitees the people being invited, in seat order and **without the organiser**: they
 *   hold a seat in every challenge of their own, so including them would match all of them.
 *
 * `undefined` covers two states and does not tell them apart, because the screen says the same
 * thing either way: nothing of yours is in the way, and the pair the send refused about is
 * between two of your invitees — a game that is theirs and not yours to read.
 *
 * The **first** in seat order, because §21's sentence names one person. Counting them would be
 * a figure the refusal deliberately did not send, arrived at by the client doing the
 * arithmetic instead — the ceiling the withheld mark is already held to.
 */
export function pairAlreadyPlaying(
  challenges: readonly Challenge[],
  invitees: readonly string[],
): string | undefined {
  const inAGame = new Set(challenges.flatMap(playersStillIn));
  return invitees.find((player) => inAGame.has(player));
}

/** The reader's own seat, or nothing where they hold none — an id the list should not answer. */
export function ownSeat(challenge: Challenge, playerId: string): ChallengeSeat | undefined {
  return challenge.seats.find((seat) => seat.playerId === playerId);
}

/**
 * What this challenge's standing says **to this reader** — the fold every sentence is keyed on.
 *
 * `undefined` where the standing is one this build has no words for: the row draws
 * `OUT_OF_DATE_GAP` in its place, which is `the-words.md` §3's named gap rather than a shorter
 * list.
 *
 * Three of the readings are worth stating, because each was wrong somewhere before it was
 * written down:
 *
 * - **`open` counts seats nobody has accepted**, never seats still to answer. At the rung that
 *   yields `LINE_UP_INCOMPLETE` nothing is awaiting, so an `awaiting` count there is
 *   structurally zero — a field that could only ever be zero is what let the shipped sentence
 *   read *"2 in, 0 still to answer"*.
 * - **The invitee's sentence reads their own seat**, not only their side (§13.1). A padel four
 *   where one declines and two accept is `LINE_UP_INCOMPLETE` for the player who declined too,
 *   and *"You're in"* is false for them in both clauses.
 * - **And it reads it on `AWAITING_ANSWERS` too** (§13.2,
 *   [#389](https://github.com/Raketa02/Raketa/issues/389)). That standing holds while *any* seat
 *   is awaiting, so the reader's own answer may already be given, and *"They're waiting on you"*
 *   was drawn for somebody who had already spoken.
 *
 * **Who a sentence names is read off the seats in court order**, and it is always the whole
 * handle or nobody: a seat `users` can no longer answer for is `unknown`, which draws `?`
 * rather than a name this app invented.
 */
export function standingFactsFor(
  challenge: Challenge,
  playerId: string,
): StandingFacts | undefined {
  if (challenge.standing === undefined) return undefined;

  const side: ChallengeSide = challenge.organiserId === playerId ? 'organiser' : 'invitee';
  // What the reader's own seat says. Both **live** standings key an invitee's sentence on it
  // (§13.1, §13.2) and the four endings never do, so it is read once here rather than twice
  // below. Absence means opposite things on the two — see `StandingFacts`.
  const ownAnswer = ownSeat(challenge, playerId)?.answer;

  switch (challenge.standing) {
    case 'AWAITING_ANSWERS':
      // This standing holds while *anybody* is awaiting, so the reader's own answer may already
      // be given — which is the whole of #389.
      return {
        side,
        standing: 'AWAITING_ANSWERS',
        awaiting: countAwaiting(challenge),
        ...(ownAnswer === undefined ? {} : { ownAnswer }),
      };
    case 'ON':
      return { side, standing: 'ON' };
    case 'LINE_UP_INCOMPLETE':
      return {
        side,
        standing: 'LINE_UP_INCOMPLETE',
        accepted: challenge.seats.filter((seat) => seat.answer === 'ACCEPTED').length,
        // A seat is open unless somebody has accepted it — an empty one, and one whose
        // occupant has left. ADR-0142: *a decline reopens that one seat*.
        open: challenge.seats.filter((seat) => seat.answer !== 'ACCEPTED').length,
        ...(ownAnswer === undefined ? {} : { ownAnswer }),
      };
    case 'DECLINED':
      return { side, standing: 'DECLINED', player: whoAnswered(challenge, 'DECLINED') };
    case 'LAPSED':
      return { side, standing: 'LAPSED', player: whoAnswered(challenge, 'LAPSED') };
    case 'WITHDRAWN':
      return { side, standing: 'WITHDRAWN', player: seatName(organiserSeat(challenge)) };
  }
}

/** Occupied seats nobody has answered for. The organiser's is accepted from birth. */
function countAwaiting(challenge: Challenge): number {
  return challenge.seats.filter((seat) => seat.playerId !== undefined && seat.answer === undefined)
    .length;
}

/**
 * The **first** seat in court order to have given this answer.
 *
 * One person, because the sentence names one. A doubles court where two people declined is a
 * court that has ended once, and counting them would be a figure this list was never asked
 * for — the ceiling every refusal in this feature is already held to.
 */
function whoAnswered(challenge: Challenge, answer: SeatAnswer): NamedPlayer {
  return seatName(challenge.seats.find((seat) => seat.answer === answer));
}

function organiserSeat(challenge: Challenge): ChallengeSeat | undefined {
  return challenge.seats.find((seat) => seat.playerId === challenge.organiserId);
}

/**
 * A seat as a sentence may name it — **the whole handle, or the question mark.**
 *
 * `unknown` covers an empty seat and a seat whose account `users` can no longer answer for, and
 * the two stay one case on purpose: there is no word to draw in either, and inventing one is
 * exactly what ADR-0107 forbids.
 */
export function seatName(seat: ChallengeSeat | undefined): NamedPlayer {
  return seat?.nickname === undefined
    ? { kind: 'unknown' }
    : { kind: 'player', nickname: seat.nickname };
}
