/**
 * The wire boundary: `GameListResponse` in, {@link Game}s out, and a score back the other way.
 *
 * ## Two kinds of unreadable code, and they are treated differently
 *
 * Old builds live on real phones for months, so every closed vocabulary here has a value this
 * one may not know. `the-words.md` §3 splits what happens by **what the code carries**, and the
 * split lands as two rules rather than one table:
 *
 * - **Vocabulary degrades in place.** A standing, a kind or an outcome this build cannot read
 *   becomes `undefined`, and the screen writes a named gap or drops a clause. Nothing about the
 *   game stops being drawable, and the list does not get shorter — *"a list that quietly
 *   dropped this morning's is a list that lies."*
 * - **Structure is refused whole.** The sport keys the score's shape, and the side places
 *   somebody on a court *and* attributes every score on the table — so a game carrying one this
 *   build cannot read is a game with no instrument and no court. It is dropped, and it cannot
 *   arrive without a redesign that would ship a new client anyway — `wireVocabulary.ts` fails
 *   the build first. A **score** whose side is unreadable goes the same way, for a sharper
 *   reason than a seat's: dropping one of two would leave a lone proposal on screen, which is a
 *   different story about the same game told with no hedge in it. So does an **agreement**
 *   whose side is unreadable — it names the score it settles, and one that names nothing settles
 *   nothing.
 *
 * ## `null` is *this response said nothing*, and it collapses to absent
 *
 * Every optional on the wire arrives as `T | null | undefined` and every one of them becomes
 * `undefined` here, so no screen has two spellings of the same absence to branch on. This is
 * the mapper `photoStepPresentation`'s rule already applied twice over.
 *
 * ## `read_at` is copied onto each game
 *
 * It is one instant for the whole list — *"every standing and deadline here was folded against
 * it"* — and it is carried per game because the screens hold one. Copying it is what makes it
 * impossible for a component to render a countdown against a clock the standing beside it never
 * saw.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';

import type { Acceptance, Game, GameSeat, Score, StandingProposal } from '../domain/game';
import type { GameKind, GameSide, GameStanding, Outcome } from '../domain/vocabulary';

type AcceptanceSchema = components['schemas']['AcceptanceSchema'];
type GameListResponse = components['schemas']['GameListResponse'];
type GameSchema = components['schemas']['GameSchema'];
type ScoreSchema = components['schemas']['ScoreSchema'];
type SeatingSchema = components['schemas']['SeatingSchema'];
type StandingProposalSchema = components['schemas']['StandingProposalSchema'];
type StateResultRequest = components['schemas']['StateResultRequest'];

const STANDINGS: Readonly<Record<GameStanding, true>> = {
  AWAITING_ENTRY: true,
  NEVER_PLAYED: true,
  AWAITING_ANSWER: true,
  CONFIRMED: true,
  UNSCORED: true,
  CALLED_OFF: true,
};

const KINDS: Readonly<Record<GameKind, true>> = { COUNTED: true, FRIENDLY: true };

const SIDES: Readonly<Record<GameSide, true>> = { A: true, B: true };

const OUTCOMES: Readonly<Record<Outcome, true>> = { WIN: true, LOSS: true };

/**
 * A membership test per vocabulary, over a `Record` keyed by the union.
 *
 * A list would have been shorter and would not have failed the build the day the contract grew
 * a sixth standing — the `Record` is what makes an addition a `pnpm typecheck` failure here as
 * well as in the copy deck.
 */
function member<T extends string>(table: Readonly<Record<T, true>>, wire: string): T | undefined {
  return Object.hasOwn(table, wire) ? (wire as T) : undefined;
}

function toScore(wire: ScoreSchema): Score {
  return { sets: wire.sets.map((set) => ({ a: set.a, b: set.b })) };
}

/**
 * A seat, or nothing when its side is not a side this build can place on a court.
 *
 * **A missing handle is not a missing seat.** `null` here is an account `users` no longer has,
 * and the seat keeps its place: dropping it would draw a three-person doubles game. It collapses
 * to absent like every other optional in this file, and the screen draws the unknown player.
 *
 * **And a missing player is not a missing seat either** (ADR-0162): `player_id: null` is a seat
 * somebody has left and nobody has filled, and it keeps its place and its side. It collapses to
 * absent the same way, and the screens draw it open.
 */
function toSeat(wire: SeatingSchema): GameSeat | undefined {
  const side = member(SIDES, wire.side);
  if (side === undefined) return undefined;

  const playerId = wire.player_id ?? undefined;
  const nickname = wire.nickname ?? undefined;
  return {
    side,
    ...(playerId === undefined ? {} : { playerId }),
    ...(nickname === undefined ? {} : { nickname }),
  };
}

function toStandingProposal(wire: StandingProposalSchema): StandingProposal | undefined {
  const side = member(SIDES, wire.side);
  if (side === undefined) return undefined;

  return {
    side,
    proposedBy: wire.proposed_by,
    score: toScore(wire.score),
    answerBy: wire.answer_by,
    settlesAt: wire.settles_at,
  };
}

/**
 * An agreement, or nothing when the side whose score it settles is not one this build can read.
 *
 * **Three of the wire's four fields**, on the rule {@link toStandingProposal} already follows:
 * what a screen reads and nothing else. `agreed_by` is read now that a seat carries a handle to
 * name it with; `agreed_at` still is not, because it answers *when did they answer* for screens
 * that never have to ask.
 */
function toAcceptance(wire: AcceptanceSchema): Acceptance | undefined {
  const ofSide = member(SIDES, wire.of_side);
  return ofSide === undefined
    ? undefined
    : { agreedBy: wire.agreed_by, ofSide, settlesAt: wire.settles_at };
}

/** One game, or nothing when its sport, its court or a score on it is one this build cannot draw. */
export function toGame(wire: GameSchema, readAt: string): Game | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  const seats = wire.seats.map(toSeat);
  if (seats.some((seat) => seat === undefined)) return undefined;

  const proposals = wire.proposals.map(toStandingProposal);
  if (proposals.some((proposal) => proposal === undefined)) return undefined;

  // The two absences do not collapse into one here, unlike everywhere else in this file: `null`
  // is *this response carried no agreement*, and `undefined` back from the mapper is an
  // agreement naming a side with no place on this court, which takes the game with it.
  const acceptance = wire.acceptance == null ? undefined : toAcceptance(wire.acceptance);
  if (wire.acceptance != null && acceptance === undefined) return undefined;

  return {
    gameId: wire.game_id,
    challengeId: wire.challenge_id,
    sport,
    kind: member(KINDS, wire.kind),
    standing: member(STANDINGS, wire.standing),
    seats: seats.filter((seat): seat is GameSeat => seat !== undefined),
    plannedAt: wire.planned_at,
    playedAt: wire.played_at ?? undefined,
    entryClosesAt: wire.entry_closes_at ?? undefined,
    calledOffAt: wire.called_off_at ?? undefined,
    score: wire.score == null ? undefined : toScore(wire.score),
    outcome: wire.outcome == null ? undefined : member(OUTCOMES, wire.outcome),
    proposals: proposals.filter((one): one is StandingProposal => one !== undefined),
    acceptance,
    readAt,
  };
}

/** Your games, newest arrangement first — **the server's order, and nothing re-sorts it.** */
export function toGames(response: GameListResponse): readonly Game[] {
  return response.games
    .map((game) => toGame(game, response.read_at))
    .filter((game): game is Game => game !== undefined);
}

/**
 * *This is the score.* **One body for three acts**, because the record decides which.
 *
 * There is no act name on it and there must not be: a client that named which would be a client
 * that could name it wrongly, and a mislabelled correction is a proposal nobody may make.
 */
export function toStateResultRequest(score: Score): StateResultRequest {
  return { score: { sets: score.sets.map((set) => ({ a: set.a, b: set.b })) } };
}
