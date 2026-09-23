import { Redirect, useLocalSearchParams } from 'expo-router';

import { ConversationScreen, parseConversationRouteParams } from '@/features/conversations/types';

/**
 * One room, opened from its row in the Chats tab.
 *
 * The path carries a static `conversation` above the id, and that is a decision rather than a
 * style ([`the-loop-screens.md`](../../../../../../../docs/specs/the-loop/the-loop-screens.md)
 * §0.2): a challenge id and a conversation id are different ids of different things, and
 * `/chats/[id]` for both is one segment a router cannot resolve and a reader cannot read. Being
 * under `/chats` is what lights the Chats column, for free and with no change to `INSIDE_A_TAB`.
 *
 * A param that does not survive the schema has no room behind it, so what it would draw is the
 * *no conversation of yours has this address* screen — and the honest place to say that is the
 * list rather than a screen about nothing. `Redirect` rather than a push, because a link this app
 * cannot read never was a place the player came from.
 */
export default function ConversationRoute() {
  const params = useLocalSearchParams();
  const parsed = parseConversationRouteParams(params);

  if (parsed === undefined) return <Redirect href="/chats" />;

  return <ConversationScreen conversationId={parsed.conversationId} />;
}
