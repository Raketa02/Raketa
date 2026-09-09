import { Redirect, useLocalSearchParams } from 'expo-router';

import { ChallengeScreen, parseChallengeRouteParams } from '@/features/challenges/types';

/**
 * One challenge — **pushed over the Chats tab, and genuinely a push.**
 *
 * The shell's ordinary move is a replace, and this is one of the few screens it is not: the
 * Chats tab stays underneath, and backing out of a challenge returns to the inbox it was tapped
 * from.
 *
 * The path carries a static `challenge` above the id, and that is a decision rather than a style
 * ([`the-loop-screens.md`](../../../../../../docs/specs/the-loop/the-loop-screens.md) §0.2): a
 * challenge id and a conversation id are different ids of different things, and `/chats/[id]`
 * for both is one segment a router cannot resolve and a reader cannot read. Being under `/chats`
 * is what lights the Chats column, for free.
 *
 * A param that does not survive the schema has no challenge behind it, so the screen it would
 * draw is the *no challenge of yours has this address* one — and the honest place to say that is
 * the inbox rather than a screen about nothing. `Redirect` rather than a push, because a link
 * this app cannot read never was a place the player came from.
 */
export default function ChallengeRoute() {
  const params = useLocalSearchParams();
  const parsed = parseChallengeRouteParams(params);

  if (parsed === undefined) return <Redirect href="/chats" />;

  return <ChallengeScreen challengeId={parsed.challengeId} />;
}
