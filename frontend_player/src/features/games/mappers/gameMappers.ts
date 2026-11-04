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
 *   different story about the same game told with no hedge in it.
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

import type { TapPosition } from '../domain/attendance';
import type { Attendance, Game, GameSeat, Score, StandingProposal } from '../domain/game';
import type {
  AttendanceState,
  GameKind,
  GameSide,
  GameStanding,
  Outcome,
} from '../domain/vocabulary';

type ArrivalRequest = components['schemas']['ArrivalRequest'];
type AttendanceSchema = components['schemas']['AttendanceSchema'];
type GameListResponse = components['schemas']['GameListResponse'];
type GameSchema = components['schemas']['GameSchema'];
type LocationFixSchema = components['schemas']['LocationFixSchema'];
type NotHereYetRequest = components['schemas']['NotHereYetRequest'];
type PresenceConfirmationRequest = components['schemas']['PresenceConfirmationRequest'];
type ScoreSchema = components['schemas']['ScoreSchema'];
type SeatingSchema = components['schemas']['SeatingSchema'];
type StandingProposalSchema = components['schemas']['StandingProposalSchema'];
type StateResultRequest = components['schemas']['StateResultRequest'];

const STANDINGS: Readonly<Record<GameStanding, true>> = {
  AWAITING_ENTRY: true,
  PLAYED_NO_SCORE: true,
  AWAITING_ANSWER: true,
  CONFIRMED: true,
  DISPUTED: true,
  CALLED_OFF: true,
  STARTED_SHORT: true,
  NOT_HERE_YET: true,
  DIDNT_COME: true,
};

const ATTENDANCE_STATES: Readonly<Record<AttendanceState, true>> = {
  WAITING: true,
  ON_TIME: true,
  CAME_LATE: true,
  DIDNT_COME: true,
  CLAIMED: true,
  CONFIRMED: true,
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
  const name = wire.nickname ?? undefined;
  return {
    side,
    ...(playerId === undefined ? {} : { playerId }),
    ...(name === undefined ? {} : { name }),
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
  };
}

/**
 * **One player somebody said was not here yet**, every `null` an absent field — a lost name, an
 * arrival, a claim or a confirmation not made. A state this build cannot read is absent rather than
 * a dropped row: the row says nothing, and the game's other rows still stand.
 */
function toAttendance(wire: AttendanceSchema): Attendance {
  const state = member(ATTENDANCE_STATES, wire.state);
  return {
    playerId: wire.player_id,
    ...(wire.nickname == null ? {} : { name: wire.nickname }),
    ...(state === undefined ? {} : { state }),
    notedAt: wire.noted_at,
    arriveBy: wire.arrive_by,
    ...(wire.arrived_at == null ? {} : { arrivedAt: wire.arrived_at }),
    claimBy: wire.claim_by,
    ...(wire.claimed_at == null ? {} : { claimedAt: wire.claimed_at }),
    ...(wire.confirmed_at == null ? {} : { confirmedAt: wire.confirmed_at }),
  };
}

/** One game, or nothing when its sport, its court or a score on it is one this build cannot draw. */
export function toGame(wire: GameSchema, readAt: string): Game | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  const seats = wire.seats.map(toSeat);
  if (seats.some((seat) => seat === undefined)) return undefined;

  const proposals = wire.proposals.map(toStandingProposal);
  if (proposals.some((proposal) => proposal === undefined)) return undefined;

  return {
    gameId: wire.game_id,
    sport,
    kind: member(KINDS, wire.kind),
    standing: member(STANDINGS, wire.standing),
    seats: seats.filter((seat): seat is GameSeat => seat !== undefined),
    plannedAt: wire.planned_at,
    playedAt: wire.played_at ?? undefined,
    entryClosesAt: wire.entry_closes_at ?? undefined,
    calledOffAt: wire.called_off_at ?? undefined,
    // Present exactly where the wire named somebody (ADR-0172 §4): the name rides with the id
    // because the leaver's seat is vacated and the court cannot supply it, and a lost name is
    // absent rather than `null` for the reason every seat's is.
    ...(wire.called_off_by == null
      ? {}
      : {
          calledOffBy: {
            playerId: wire.called_off_by.player_id,
            ...(wire.called_off_by.nickname == null ? {} : { name: wire.called_off_by.nickname }),
          },
        }),
    score: wire.score == null ? undefined : toScore(wire.score),
    outcome: wire.outcome == null ? undefined : member(OUTCOMES, wire.outcome),
    proposals: proposals.filter((one): one is StandingProposal => one !== undefined),
    attendance: wire.attendance.map(toAttendance),
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

/**
 * **The fix, as the tap carries it** — and nothing else about the phone. A platform that states no
 * accuracy sends `0`, which **claims no allowance**: the fix is measured as it stands, never given a
 * radius the device did not state.
 */
function toLocationFix(at: TapPosition): LocationFixSchema {
  return { latitude: at.latitude, longitude: at.longitude, accuracy_m: at.accuracyMetres ?? 0 };
}

/** *Oscar isn't here yet* — who, and where the tap was made. Who says so is the reader. */
export function toNotHereYetRequest(playerId: string, at: TapPosition): NotHereYetRequest {
  return { player_id: playerId, location: toLocationFix(at) };
}

/** *I'm here* with the reader's own id, *they're here* with somebody else's — and where. */
export function toArrivalRequest(playerId: string, at: TapPosition): ArrivalRequest {
  return { player_id: playerId, location: toLocationFix(at) };
}

/** *Yes, they were here* — whose *I was there* it confirms, and no position: a day later, from anywhere. */
export function toPresenceConfirmationRequest(playerId: string): PresenceConfirmationRequest {
  return { player_id: playerId };
}
