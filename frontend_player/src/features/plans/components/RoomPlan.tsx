/**
 * **The join, and the whole of what the room hands down is a game id.**
 *
 * The card needs `(game, plan | undefined)` and no route serves the pair: the plan is deliberately
 * not a field on a game — *a game is a record of an evening and a plan is an agreement about a
 * future, and the two contexts do not read each other* — so it is one list beside the other, joined
 * by game id at the surface
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §8,
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §1).
 *
 * **`features/plans` may import `features/games`, and never the reverse.** That is the direction
 * ADR-0148 already pays for on the server, and it keeps the client half of ADR-0145 §4's clause
 * true for free: `features/games` never learns a plan exists. The rule is one-way, it is stated as
 * such so a future reader cannot read the existing edge as symmetry, and `eslint.config.mjs`
 * enforces the half that is a grep rather than a judgement.
 *
 * **A game this reader is not on the court of draws nothing**, and so does a list that has not
 * landed. Both are the same nothing on purpose: there is no plan to draw and no sentence worth
 * writing about the absence, because the room behind this card is the whole screen and a card that
 * announced its own loading would be chrome flickering above a stream.
 *
 * Two reads and neither is this component's to own — they are the app's lists, shared with Now and
 * with the game screen, so on a warm cache this costs nothing at all.
 */

import { useGame } from '@/features/games/types';

import { usePlan } from '../hooks/usePlans';

import { PlanCard } from './PlanCard';

export interface RoomPlanProps {
  /** The game this room's line-up completed into. A room without one draws no card at all. */
  readonly gameId: string;
  /** The account may not write here. Every chip greys, and the screen owns the one note. */
  readonly refused?: boolean;
}

export function RoomPlan({ gameId, refused = false }: RoomPlanProps) {
  const { game } = useGame(gameId);
  const { plan } = usePlan(gameId);

  if (game === undefined) return null;

  return (
    <PlanCard
      gameId={gameId}
      plannedAt={game.plannedAt}
      readAt={game.readAt}
      plan={plan}
      refused={refused}
    />
  );
}
