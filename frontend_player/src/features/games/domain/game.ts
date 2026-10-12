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

import type { AttendanceState, GameKind, GameSide, GameStanding, Outcome } from './vocabulary';

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
 * One side's score, on the table and not yet settled on.
 *
 * **At most one per side**, which is what bounds an argument to two rounds. Two of them is a
 * disagreement this platform does not arbitrate, and does not hide: both scores travel, and
 * either side may agree with the other's. If neither does, the game settles when the later one's
 * {@link answerBy} comes — with the closer score where both name the same winner, and `DISPUTED`
 * where they name different ones (#654).
 *
 * **An agreement is never on the table** (#654; ADR-0195 §5): *That's right* settles the result
 * at once, so there is no grace to wait out and nothing to carry about it. The wire's
 * `acceptance` and `settles_at` went with it.
 */
export interface StandingProposal {
  readonly side: GameSide;
  readonly proposedBy: string;
  readonly score: Score;
  /**
   * When the other side's silence makes this score the result — 24 hours after it went up, or
   * after its last correction. **Nothing happens at this moment** — no job runs and nothing is
   * written; the game simply reads as settled from here on. Saying nothing costs nobody anything.
   */
  readonly answerBy: string;
}

/** The player whose act called the game off. See {@link Game.calledOffBy}. */
export interface CalledOffBy {
  readonly playerId: string;
  /** The whole name. Absent where `users` no longer has the account. */
  readonly name?: string;
}

/**
 * **One player somebody on a booked game's court said was not here yet**, and what became of it
 * (#657; ADR-0195 §3). **Who tapped is on no wire**: the tap is the game's, said by somebody at the
 * club, and a name on it would be the platform pointing at one of the people who came. Nobody is
 * here who was not tapped — everybody who arrives on time does nothing at all.
 *
 * Every instant is the backend's, and the state is its fold against the list's `readAt`.
 */
export interface Attendance {
  readonly playerId: string;
  /** The whole name. Absent where `users` no longer has the account. */
  readonly name?: string;
  /**
   * What became of them. **Absent when this build cannot read the code**: the row says nothing
   * and offers nothing, and the rest of the block stands.
   */
  readonly state?: AttendanceState;
  /** When somebody at the club first said they were not here. */
  readonly notedAt: string;
  /**
   * The end of the first half hour — an arrival is taken until it and never after. **Nothing
   * happens at it**: a player still awaited simply reads *Didn't come* from here on.
   */
  readonly arriveBy: string;
  /** The arrival — the first *I'm here* or *they're here*. Absent until one. */
  readonly arrivedAt?: string;
  /** The end of the day after `arriveBy` in which *I was there* may be said and confirmed. */
  readonly claimBy: string;
  /** When they said *I was there*. */
  readonly claimedAt?: string;
  /** When somebody else on the court said *yes, they were here*. Who did is on no wire. */
  readonly confirmedAt?: string;
}

export interface Game {
  readonly gameId: string;
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
  /** The court in the order the wire handed it over. */
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
  /**
   * The score that stands. Absent until something settles on one — and on a `DISPUTED` game,
   * whose two scores named different winners.
   */
  readonly score?: Score;
  /** Win or loss **for you**, and absent for every standing but a confirmed one. */
  readonly outcome?: Outcome;
  /**
   * The scores on the table, **side A's first and never in the order they arrived**. Empty
   * unless an answer is being awaited: before that nobody has entered one, and after it the
   * ending is the answer. Two of them **is** the disagreement. Always empty on a For fun game,
   * whose score is the result the moment it is put up (#654).
   */
  readonly proposals: readonly StandingProposal[];
  /**
   * Everybody somebody on the court said was not here yet, in the court's order (#657) — **empty on
   * an ordinary game**, where everybody arrived on time and nobody tapped anything, and on every
   * game that was not booked.
   */
  readonly attendance: readonly Attendance[];
  /** The instant this game's standing and every deadline on it were folded against. */
  readonly readAt: string;
}
