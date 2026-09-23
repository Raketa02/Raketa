/**
 * **The departure** — leaving a game you had agreed to, before it is played
 * ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
 *
 * A **challenge** act reached from a game: the seat that reopens is the challenge's, so the fill,
 * the pool, the pair rule and the room's line all keep the record they already have — and the
 * game is told in the same transaction, keeps its id, its plan and its room, and draws the seat
 * empty until somebody fills it, the game is called off, or its window closes.
 *
 * **Any player on the court, the organiser included, while the game is `AWAITING_ENTRY` and its
 * agreed moment is ahead** (#411 rule 1). Past the moment the server refuses with
 * `game_moment_has_passed` — a no-show cannot vacate a seat to block the result — and the client
 * mirrors that rule on the control rather than here.
 *
 * There is no ask beyond the id: leaving takes no arguments because it makes no choices. The
 * reply is the challenge as it now stands at `LINE_UP_INCOMPLETE` with the caller's seat `LEFT`,
 * which is the server's own derived standing and therefore the redraw.
 */

import { postDeparture } from '../api/challengesApi';
import type { AnsweredChallenge } from '../domain/challengeDetail';
import { toAnsweredChallenge } from '../mappers/challengeDetailMappers';

export async function leaveGame(challengeId: string): Promise<AnsweredChallenge> {
  return toAnsweredChallenge(await postDeparture(challengeId));
}
