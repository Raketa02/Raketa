/**
 * The result route's wire fixtures, typed from the generated schema.
 *
 * The same rule as `now.ts`: a fake response is typed against the contract so a
 * backend shape change fails `pnpm typecheck` rather than a test run, and no test
 * can describe a screen the contract cannot produce.
 *
 * **The three booleans are not defaulted from the situation**, and neither is the
 * block from the score. The server composes each of them from the record and the
 * viewer, and a builder that derived one from another would make the client's
 * refusal to derive them untestable — a leaver's screen is exactly a played match
 * with a score on it and every boolean false.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import { matchCard } from './now';
import type { Transport, Wire } from './transport';
import { json } from './transport';

export function resultPath(matchId: string): string {
  return `/api/v1/matches/${matchId}/result`;
}

export function acceptancePath(matchId: string): string {
  return `${resultPath(matchId)}/acceptance`;
}

/** A score as the server composes one: the viewer's side first, in both halves. */
export function scoreLine(
  sides: readonly (readonly string[])[],
  sets: readonly (readonly [number, number])[],
): Wire['ScoreLineResponse'] {
  return {
    sides: sides.map((players) => ({ players: [...players] })),
    sets: sets.map(([first, second]) => ({ first, second })),
  };
}

/** Nothing on the table: an empty block, never an absent one. */
export function emptyResultBlock(): Wire['ResultBlockResponse'] {
  return { agreed: false, proposals: 0, score: null, proposed_by: null };
}

export interface ResultScreenOptions {
  readonly matchId: string;
  readonly situation?: Wire['Situation'];
  readonly clubName?: string;
  readonly amount?: number;
  readonly result?: Wire['ResultBlockResponse'];
  readonly counts?: Partial<Wire['SeatCountsResponse']>;
  readonly mayEnter?: boolean;
  readonly mayAccept?: boolean;
  readonly mayCounter?: boolean;
  /** The hero clock. `null` once the answer is in — it counts to nothing, not to zero. */
  readonly settlementDeadline?: string | null;
  /** The quieter clock, sent only while it runs. */
  readonly acceptanceGrace?: string | null;
}

export function resultScreen({
  matchId,
  situation = 'needsResult',
  clubName = 'Sunset Padel',
  amount = 3800,
  result = emptyResultBlock(),
  counts = {},
  mayEnter = false,
  mayAccept = false,
  mayCounter = false,
  settlementDeadline = null,
  acceptanceGrace = null,
}: ResultScreenOptions): Wire['ResultScreenResponse'] {
  // The spine and the situation half are the *same* objects `GET /now` sends, so
  // the fixture composes them from the card builder rather than restating them —
  // two definitions of *where and when* in one test-support module is how two
  // fixtures come to describe two different matches under one name.
  const card = matchCard({ matchId, situation, clubName, amount });

  return {
    match_id: matchId,
    where: card.where,
    price: card.price,
    situation: card.situation,
    result,
    counts: { seats: 4, paid: 4, held: 0, turned_up: 4, ...counts },
    may_enter: mayEnter,
    may_accept: mayAccept,
    may_counter: mayCounter,
    settlement_deadline: settlementDeadline,
    acceptance_grace: acceptanceGrace,
  };
}

/** A write's answer: its own screen, and Now's update, in one response. */
export function resultWrite(
  screen: Wire['ResultScreenResponse'],
  card: Wire['MatchCardResponse'],
): Wire['ResultWriteResponse'] {
  return { screen, update: { update_type: 'card', card } };
}

export function stubResult(transport: Transport, screen: Wire['ResultScreenResponse']): void {
  transport.on('GET', resultPath(screen.match_id), () => json(screen));
}
