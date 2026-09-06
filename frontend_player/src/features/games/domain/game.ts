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
 * One side's score, on the table and not yet settled on.
 *
 * **At most one per side**, which is what bounds an argument to two rounds. Two of them is the
 * disagreement this platform does not resolve — and it does not resolve it by *arbitrating*,
 * not by hiding it: both scores travel, and either side may agree with the other's.
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

/**
 * Somebody agreed with the other side's score, and the grace has not run out.
 *
 * **It settles nothing on its own.** Inside the grace a disagreement still wins, which is what
 * stops a partner who is quick to their phone from closing the door on an opponent who has not
 * read the score yet. What it does change is that the proposing side has stopped waiting on
 * silence, and that the correction the aggregate now refuses is no longer worth offering.
 *
 * **Two of the wire's four fields, on the rule `StandingProposal` already follows**: this holds
 * what the screens read and nothing else. `agreed_by` names a person on a court where nobody is
 * named, and `agreed_at` answers *when did they answer* for a screen that never has to ask —
 * the refusal that would have wanted it is only reachable when no agreement had crossed at all
 * (`components/gameErrorMessage.ts`).
 */
export interface Acceptance {
  /**
   * Whose score was agreed with — **always the accepter's opposite**, because a teammate
   * agreeing with a teammate proves nothing. So it names the score *and* which of the two
   * people this is news for.
   */
  readonly ofSide: GameSide;
  /**
   * When this agreement becomes the result. Measured from the **score** and never from the tap:
   * the person the grace protects is the opponent who has not read the score yet.
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
  /**
   * The scores on the table, **side A's first and never in the order they arrived**. Empty
   * unless an answer is being awaited: before that nobody has entered one, and after it the
   * ending is the answer. Two of them **is** the disagreement.
   */
  readonly proposals: readonly StandingProposal[];
  /** The agreement waiting out its grace, and absent when none is. **A counter voids one.** */
  readonly acceptance?: Acceptance;
  /** The instant this game's standing and every deadline on it were folded against. */
  readonly readAt: string;
}
