import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  ConversationGameDetails,
  parseConversationRouteParams,
} from '@/features/conversations/types';

/**
 * The game behind a room — **`features/games`' own screen at a second route.**
 *
 * The second instance of ADR-0149 §5's shape on this tab, after the builder: each route lights its
 * own column and *back* is correct in both directions by construction. The component under it does
 * the join, because the game id is the room's and no route serves it any other way.
 */
export default function ConversationGameRoute() {
  const params = useLocalSearchParams();
  const parsed = parseConversationRouteParams(params);

  if (parsed === undefined) return <Redirect href="/chats" />;

  return <ConversationGameDetails conversationId={parsed.conversationId} />;
}
