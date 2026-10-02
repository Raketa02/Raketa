/**
 * ***Kuba didn't come*** and ***I was there*** — the two acts on a no-show report
 * ([#560](https://github.com/Raketa02/Raketa/issues/560); the Games & Fill in mechanics §15.3).
 *
 * **Both answers are dropped**, for `stateResult`'s reason: each route replies with the game as it
 * now stands, folded against the server's clock, and splicing it into a list folded against an
 * older `read_at` would put two readings of the clock in one list. The caller invalidates, and the
 * next read is one fold over everything.
 */

import { postNoShow, postNoShowDispute } from '../api/gamesApi';
import { toReportANoShowRequest } from '../mappers/gameMappers';

export interface NoShowToReport {
  readonly gameId: string;
  /** Who did not come — somebody else on the court. */
  readonly playerId: string;
}

export async function reportNoShow({ gameId, playerId }: NoShowToReport): Promise<void> {
  await postNoShow(gameId, toReportANoShowRequest(playerId));
}

export async function disputeNoShow(gameId: string): Promise<void> {
  await postNoShowDispute(gameId);
}
