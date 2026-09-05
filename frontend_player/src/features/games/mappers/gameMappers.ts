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
 * - **Structure is refused whole.** The sport keys the score's shape and the side places
 *   somebody on a court, so a game carrying one this build cannot read is a game with no
 *   instrument and no court. It is dropped, and it cannot arrive without a redesign that would
 *   ship a new client anyway — `wireVocabulary.ts` fails the build first.
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

import type { Game, GameSeat, Score, StandingProposal } from '../domain/game';
import type { GameKind, GameSide, GameStanding, Outcome } from '../domain/vocabulary';

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

/** A seat, or nothing when its side is not a side this build can place on a court. */
function toSeat(wire: SeatingSchema): GameSeat | undefined {
  const side = member(SIDES, wire.side);
  return side === undefined ? undefined : { side, playerId: wire.player_id };
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

/** One game, or nothing when its sport or its court is not one this build can draw. */
export function toGame(wire: GameSchema, readAt: string): Game | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  const seats = wire.seats.map(toSeat);
  if (seats.some((seat) => seat === undefined)) return undefined;

  const proposal =
    wire.standing_proposal == null ? undefined : toStandingProposal(wire.standing_proposal);

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
    score: wire.score == null ? undefined : toScore(wire.score),
    outcome: wire.outcome == null ? undefined : member(OUTCOMES, wire.outcome),
    standingProposal: proposal,
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
