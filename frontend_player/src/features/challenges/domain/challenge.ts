/**
 * A challenge as this build reads one, and the **one question a refused send asks of it**.
 *
 * `GET /challenges` is *"every challenge you hold a seat in, newest first"*, and today it has
 * exactly one reader: a send refused with `open_challenge_stands` names nobody, so the client
 * re-reads the list that was always its own to find out who
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §5.1).
 * The screens that draw a standing arrive with the Now tab; until then this holds the fields
 * that question needs and says so, which is the shape `SearchRecord` already takes — the rest
 * of the wire joins it when a surface draws one.
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
 */

import type { SeatAnswer, Standing } from './standing';

/** One seat of a challenge: who is in it, and what they did about being asked. */
export interface ChallengeSeat {
  /** Absent on a seat nobody was put in — *an empty seat is a seat*, and it keeps its place. */
  readonly playerId?: string;
  /** Absent while they have not answered, and on a seat nobody was put in. */
  readonly answer?: SeatAnswer;
}

/**
 * A challenge, as much of it as this build has a reader for.
 *
 * `organiserId` is here rather than a side, because *"**Challenge sent** and **Challenge for
 * you** are one standing read from two sides"* and which one a reader gets is decided by
 * whether the seat is theirs — a `side` field would be that decision taken by a mapper on
 * somebody else's behalf.
 */
export interface Challenge {
  readonly challengeId: string;
  readonly organiserId: string;
  readonly standing: Standing;
  /** The court in its fixed order, empty seats included. */
  readonly seats: readonly ChallengeSeat[];
}

/**
 * The two standings that mean **this challenge has ended**.
 *
 * A `Record` keyed by the union rather than a list, for §1's reason: a sixth standing added to
 * the contract fails `pnpm typecheck` here rather than quietly counting as open.
 */
const ENDED: Readonly<Record<Standing, boolean>> = {
  AWAITING_ANSWERS: false,
  ON: false,
  LINE_UP_INCOMPLETE: false,
  DECLINED: true,
  LAPSED: true,
};

/** Whether a game still stands between the people in it. */
export function challengeStands(challenge: Challenge): boolean {
  return !ENDED[challenge.standing];
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
