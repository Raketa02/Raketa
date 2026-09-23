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
 * ## A seat carries a handle, and nothing else about the person in it
 *
 * `SeatingSchema` is a side, a player id and a name — no Level, no band, no area, no run of
 * form ([ADR-0141](../../../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)).
 * A card is what a *searcher* reads to decide about a game that might happen; this is the record
 * of one that did, and every value on a card would be an as-of-now fact stapled to an evening in
 * the past. So the screens name **people** where a person did something — put a score up, agreed
 * with one — and **sides** where the score itself is being drawn, because a score is a fact about
 * a side and not about whoever typed it.
 *
 * The handle is the **whole** handle, always:
 * [ADR-0107](../../../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4
 * forbids deriving a familiar form from one, and `@/shared/formatting/playerName` is the single
 * formatter that turns a seat into words.
 *
 * `name` is **absent** where `users` no longer has that account, which is a `?` on screen and
 * never a dropped seat — the same fall-back a Play court draws for a seat whose row the record
 * can no longer describe.
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

/**
 * One position on one side: a person, or a seat somebody has left.
 *
 * **A seat is never dropped, and since
 * [ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)
 * it can be open.** `playerId` is absent on a seat whose occupant left the game and nobody has
 * filled yet: the seat keeps its place and its side, the court keeps its size, and every screen
 * that draws the court draws it empty. The line-up is frozen at the plan **until somebody leaves
 * it** — and the next completed line-up re-seats the same game.
 */
export interface GameSeat {
  readonly side: GameSide;
  /** Who holds this seat. **Absent on an open seat** — somebody left, and nobody has filled it. */
  readonly playerId?: string;
  /**
   * What they are called — **the whole name, and nothing may shorten it into a sentence.**
   * Absent where `users` no longer has the account, which draws the unknown player's `?` — and
   * on an open seat, which draws nobody.
   */
  readonly name?: string;
}

/**
 * **The seats nobody is in** — the fact *Needs a player* is folded from, and the one a result is
 * refused on while it is true.
 *
 * Nothing on the wire names the rung: an open seat is `player_id: null`, the standing stays
 * `AWAITING_ENTRY`, and it is the client's card that says a player is needed. One function, so
 * the screen's acts, the players card and the card's spoken label read one definition of *open*.
 * The ladder in `features/plans` spells the same field itself — a runtime import of this
 * feature's `types.ts` would pull the screen into a `domain/` module — and says so where it does.
 */
export function openSeats(seats: readonly GameSeat[]): readonly GameSeat[] {
  return seats.filter((seat) => seat.playerId === undefined);
}

/**
 * **Everybody in a seat but the reader**, by id and in the court's order — what the fill is told
 * about the court it completes ([#419](https://github.com/Raketa02/Raketa/issues/419)).
 *
 * The seats a fill may never take out, on `acceptedPlayers`' shape one feature over: *in seat
 * order and without the reader*, because the reader's own seat is what the court is composed
 * around and the builder puts it back at the send. Read off the game rather than the challenge
 * because the game's seats are the court as it stands **now** — the challenge's are the
 * arrangement as it was sent, and a re-seat has moved on from it.
 */
export function seatedOthers(seats: readonly GameSeat[], reader: string): readonly string[] {
  return seats.flatMap((seat) =>
    seat.playerId === undefined || seat.playerId === reader ? [] : [seat.playerId],
  );
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
 * **Three of the wire's four fields, on the rule `StandingProposal` already follows**: this holds
 * what the screens read and nothing else. `agreed_by` is here now that a seat carries a handle —
 * *somebody agreed* is the one sentence on these screens that was addressed to nobody. `agreed_at`
 * stays off: it answers *when did they answer* for a screen that never has to ask, and the refusal
 * that would have wanted it is only reachable when no agreement had crossed at all
 * (`components/gameErrorMessage.ts`).
 */
export interface Acceptance {
  /** Who agreed. A player id, named through the seat they hold. */
  readonly agreedBy: string;
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

/** The player whose act called the game off. See {@link Game.calledOffBy}. */
export interface CalledOffBy {
  readonly playerId: string;
  /** The whole name. Absent where `users` no longer has the account. */
  readonly name?: string;
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
  /**
   * When *we played* stops being sayable. Absent once somebody has said it happened — and on a
   * game that was called off, where the window no longer matters.
   */
  readonly entryClosesAt?: string;
  /**
   * When somebody called it off, while a seat was open
   * ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)). Present
   * exactly on `CALLED_OFF`: the act's own instant, which is what the ending card is shelved from.
   * Who is {@link calledOffBy}.
   */
  readonly calledOffAt?: string;
  /**
   * **Who called it off, and what they are called** — present exactly on `CALLED_OFF`
   * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §4), the field ADR-0163 §4 kept for the day a design wanted the name. The last leaver, whose
   * seat is drawn open — or whoever pressed *Call it off*, who still holds one; **which of the two
   * is read off the seats**, and the game screen's heading is keyed on it. The name is carried
   * because the leaver's seat is vacated and the court cannot supply it; absent where `users` no
   * longer has the account, which draws `?` as a seat's does.
   */
  readonly calledOffBy?: CalledOffBy;
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
