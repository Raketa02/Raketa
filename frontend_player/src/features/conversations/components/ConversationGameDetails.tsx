/**
 * **The game behind a room**, under the room's own address.
 *
 * `GameScreen` at a second route, which is
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §5's shape: one screen component and two addresses, each lighting its own column, with *back*
 * correct in both directions **by construction** rather than through a `from` parameter that would
 * make `tabForPathname` impure.
 *
 * **The join is here because the door is the conversation's.** No route serves a room's game
 * except the room itself, and `features/games` may not learn that a conversation exists — so the
 * room is read for its `game_id` and the game screen is handed one. That read is already in the
 * cache: it is the same query the screen behind this one is mounted on.
 *
 * **What is mounted is `GameScreenWithPlan`**, which is `GameScreen` with its plan composed into
 * it: `features/games` may not learn a plan exists, so the screen takes a slot and one component
 * in `features/plans` does the join, folds the arm and fills it
 * ([#368](https://github.com/Raketa02/Raketa/issues/368), ADR-0149 §2). It is the same component
 * the Now route mounts, and it is told nothing about which door mounted it.
 *
 * A room with no game has no door to reach this through, so arriving here at all means a link or
 * a stale route — and it draws `RoomAbsent`, the same nothing the room screen draws, for the same
 * reason: there is nothing a player would do differently, and both doors under this address land
 * on one read.
 */

import { useEffect } from 'react';
import { router } from 'expo-router';

import { GameScreenWithPlan } from '@/features/plans/types';

import { useConversation } from '../hooks/useConversation';
import { roomIsGone } from '../domain/roomGone';

import { RoomAbsent } from './RoomAbsent';

export interface ConversationGameDetailsProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly conversationId: string;
}

export function ConversationGameDetails({ conversationId }: ConversationGameDetailsProps) {
  const { data, isPending, error } = useConversation(conversationId);
  const gameId = data?.room.gameId;

  // A room that has gone takes this screen with it — the door and what is behind it are one
  // read. It lands on the room beneath, which is the screen that keeps what it held and says the
  // chat has ended (§3.7 as amended by #429); there is nothing of the game left to draw here.
  useEffect(() => {
    if (roomIsGone(error)) router.back();
  }, [error]);

  if (gameId === undefined) return <RoomAbsent arriving={isPending} error={error} />;

  return <GameScreenWithPlan gameId={gameId} />;
}
