import { Redirect, useLocalSearchParams } from 'expo-router';

import { YesScreen, parseYesRouteParams } from '@/features/challenges/types';

/**
 * **The yes screen** — the screen a yes lands on, under the challenge it is about
 * ([ADR-0167](../../../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)).
 *
 * Pushed over the challenge screen the instant *I'm in* is answered, and over wherever the
 * player is the instant the deck's *Let's play* comes back mutual and naming a chat
 * ([#434](https://github.com/Raketa02/Raketa/issues/434)); genuinely a push either way: it is
 * one-shot, and every exit removes it — *Later* down to the Chats list with the challenge screen
 * after a challenge's yes and a plain pop after a mutual's, *Open the chat* to the list and then
 * into the room. It is a stack screen and not a modal, the shell stands its bar down on it as it
 * does in the room, and its swipe-back is off (`TabShell`), because a swipe that popped to the
 * challenge screen underneath would land somewhere *Later* never does.
 *
 * Two params, both checked first: the challenge id, for the reasons its sibling route states,
 * and **which yes** this is — a closed union, because a route param is not app state and a
 * value outside it is a link this app cannot read. A link that survives neither has no yes
 * behind it, so the honest place to land is the list; `Redirect` rather than a push, because a
 * link this app cannot read never was a place the player came from. A link whose challenge the
 * reader holds no accepted seat on is the screen's own question — it needs the read — and the
 * screen dismisses down to the same list.
 */
export default function YesRoute() {
  const params = useLocalSearchParams();
  const parsed = parseYesRouteParams(params);

  if (parsed === undefined) return <Redirect href="/chats" />;

  return <YesScreen challengeId={parsed.challengeId} which={parsed.which} />;
}
