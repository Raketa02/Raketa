/**
 * A game as this app reads one: the court it was arranged on, and what it is right now.
 *
 * **One list and not several** — *"a game awaiting an entry, one awaiting an answer and one
 * that never happened are one thing at three moments of its life"* — so there is one type and
 * the standing says which moment. Splitting it into an arranged shape and a played shape would
 * make the client's shelves the platform's opinion about which of them matters.
 *
 * ## `readAt` travels with the list and not with the game
 *
 * Every deadline on the wire is a **moment the backend computed**, and `read_at` is the instant
 * every standing beside it was folded against. So a duration is rendered from `readAt` and
 * never from the device clock: a countdown taken from `Date.now()` would eventually disagree
 * with the standing printed next to it, which is the one thing the field exists to prevent. It
 * is carried on each game rather than left with the list because the screens hold **one** game
 * and would otherwise each need to be handed the pair.
 *
 * ## Nobody on this court has a name
 *
 * `SeatingSchema` is a side and a player id, and that is all the games contract carries — no
 * handle, no level, no relationship. It is the gap `SearchEnvelope.myAreaCode` is
 * ([#279](https://github.com/Raketa02/Raketa/issues/279)): stated here rather than worked
 * around, because the alternative is this feature learning to guess a nickname, which
 * [ADR-0107](../../../../../docs/adr/0107-a-handle-is-the-whole-handle.md) forbids in one
 * sentence. So the screens name **sides** — *your side*, *the other side* — derived from which
 * seat is yours, and no sentence in this feature says anybody's handle.
 *
 * Which seat *is* yours is a **join and not a rule**: `ArrangementSeatSchema` states a
 * `Relationship` and this one does not, so the client looks its own id up in the seats. That
 * id comes from `GET /users/me`, which is the only route in the app that serves it.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { GameKind, GameSide, GameStanding, Outcome } from './vocabulary';

/**
 * The four sports, as this feature needs them: a score's shape is the sport's.
 *
 * Aliased from the shared vocabulary rather than spelled again — a fifth sport is one table's
 * problem, not five.
 */
export type GameSport = Sport;

/** One set, **absolute**: what side A took, and what side B took. Never relative to a reader. */
export interface SetScore {
  readonly a: number;
  readonly b: number;
}

/** The sets, in the order they were played. One to five, and it names a winner. */
export interface Score {
  readonly sets: readonly SetScore[];
}

/** One person, on one side. The court is frozen at the plan. */
export interface GameSeat {
  readonly side: GameSide;
  readonly playerId: string;
}

/**
 * The score waiting on an answer, **when exactly one is**.
 *
 * Absent in two cases the screens must not confuse: nothing has been entered, or both sides
 * have spoken and neither score is *the* one. The second is read off the standing, never off
 * this absence.
 */
export interface StandingProposal {
  readonly side: GameSide;
  readonly proposedBy: string;
  readonly score: Score;
  /**
   * When the other side's silence becomes agreement. **Nothing happens at this moment** — no
   * job runs and nothing is written; the game simply reads as confirmed from here on.
   */
  readonly answerBy: string;
  /**
   * When an acceptance of this score would become final — earlier than {@link answerBy}, and
   * the grace an opponent who has not read the score yet is given. Inside it a counter wins.
   */
  readonly settlesAt: string;
}

export interface Game {
  readonly gameId: string;
  readonly challengeId: string;
  readonly sport: GameSport;
  /**
   * Whether this evening is evidence. **Absent when this build has no word for what the wire
   * said** — the clause it writes is dropped, and every other sentence on the screen stands.
   */
  readonly kind?: GameKind;
  /**
   * What this game is right now. **Absent when this build cannot read the code**, which draws
   * the out-of-date sentence and offers nothing: a standing *is* the whole line, so it is one
   * of `the-words.md` §3's named gaps rather than one of its drops.
   */
  readonly standing?: GameStanding;
  /** The court in the order the challenge handed it over. */
  readonly seats: readonly GameSeat[];
  /** When the last seat accepted and this became a game. */
  readonly plannedAt: string;
  /** When somebody said it happened. Absent while nobody has. */
  readonly playedAt?: string;
  /** When *we played* stops being sayable. Absent once somebody has said it happened. */
  readonly entryClosesAt?: string;
  /** The agreed score. Absent until something settles on one. */
  readonly score?: Score;
  /** Win or loss **for you**, and absent for every standing but a confirmed one. */
  readonly outcome?: Outcome;
  readonly standingProposal?: StandingProposal;
  /** The instant this game's standing and every deadline on it were folded against. */
  readonly readAt: string;
}
