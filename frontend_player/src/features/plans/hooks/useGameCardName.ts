/**
 * **Which card this game is, for a surface that says so without drawing one.**
 *
 * The conversation header's second line is *the same state as the card in Now*
 * ([#401](https://github.com/Raketa02/Raketa/issues/401)), and this is what makes that true by
 * construction rather than by two folds agreeing: it is `gameCardName` over the same two reads the
 * rail and the pinned plan card already make — `GET /games` for the standing and its `read_at`,
 * `GET /plans` for the slots — so the header cannot say *planning* while the card three taps away
 * says *game on*. Nothing is fetched that the screen was not already holding; TanStack dedupes
 * the two lists to the queries already in flight.
 *
 * It lives here rather than in the room because the ladder reads a plan and ADR-0149 §1's arrow
 * runs one way: `features/plans` may import `features/games`, and a conversation asking either of
 * them what a game *is* was exactly what ADR-0148 §6 refused. What crosses the boundary is a card
 * name — the four rungs and the endings — and never a standing
 * ([ADR-0157](../../../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)).
 *
 * `undefined` is **no card to name**: a room with no game, a games list that has not landed or
 * failed, or an id no game of yours has. All three draw the same nothing, and none is told apart
 * here because the one caller draws the sport alone for all of them.
 */

import { useGame } from '@/features/games/types';

import { gameCardName, type GameCardName } from '../domain/gameCard';

import { usePlan } from './usePlans';

export function useGameCardName(gameId: string | undefined): GameCardName | undefined {
  const { game } = useGame(gameId);
  const { plan } = usePlan(game?.challengeId);

  return game === undefined ? undefined : gameCardName(game, plan);
}
