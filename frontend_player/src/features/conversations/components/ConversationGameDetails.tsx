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
 * **Nothing about the game screen is this ticket's.** What is here is the destination the header's
 * *Details* needs in order not to be a dead control; the three plan arms it grows are
 * [#368](https://github.com/Raketa02/Raketa/issues/368)'s, on the screen this renders.
 *
 * A room with no game has no door to reach this through, so arriving here at all means a link or
 * a stale route — and it draws the sentence a room that is not yours draws, for the same reason
 * the room screen does: there is nothing a player would do differently.
 */

import { StyleSheet, Text, View } from 'react-native';

import { GameScreen } from '@/features/games/types';
import { recoveryMessage } from '@/shared/errors';
import { Note, theme } from '@/shared/ui';

import { useConversation } from '../hooks/useConversation';

import { NO_CONVERSATION_HERE } from './conversationPresentation';

export interface ConversationGameDetailsProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly conversationId: string;
}

export function ConversationGameDetails({ conversationId }: ConversationGameDetailsProps) {
  const { data, isPending, error } = useConversation(conversationId);
  const gameId = data?.room.gameId;

  if (gameId === undefined) {
    return (
      <View style={s.screen}>
        {isPending ? null : error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        ) : (
          <Text style={s.line}>{NO_CONVERSATION_HERE}</Text>
        )}
      </View>
    );
  }

  return <GameScreen gameId={gameId} />;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper, padding: theme.size.gutter },
  line: { ...theme.type.tiny, color: theme.color.muted },
});
