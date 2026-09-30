import { Redirect, useLocalSearchParams } from 'expo-router';

import { BuilderScreen, parseBuilderRouteParams } from '@/features/play/types';
import { parseChallengeRouteParams } from '@/features/challenges/types';

/**
 * **The builder, completing a challenge** — `features/play`'s own screen at a second route.
 *
 * One screen component and two routes, which is
 * [ADR-0149](../../../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §9's shape reused for the second time on this map: each route lights its own column, *back* is
 * correct in both directions **by construction**, and neither `tabForPathname` nor `INSIDE_A_TAB`
 * grows a `from` parameter that would make a pure function impure
 * ([`the-loop-screens.md`](../../../../../../../docs/specs/the-loop/the-loop-screens.md) §0.2).
 * Being under `/chats` is what lights the Chats column, for free.
 *
 * **It is a plain push, and nothing here resets the shell stack.** That reset dismisses the stack
 * and ends the Play session, and `landOnHome`'s *"there is nothing left to be behind: the court is
 * gone"* is false here — the thing behind is the challenge being completed, and it is the surface
 * the send pops back to.
 *
 * **The screen is handed the search and never the challenge.** The challenge is already stamped on
 * the record that search minted, so the builder reads it off the origin; the id in this path is
 * there because a path has to say what it is looking at, and a second spelling reaching the screen
 * would be one more thing that can disagree with the answer it is drawing.
 *
 * Both params are checked before anything reads them, for the reasons each route already states:
 * a search id becomes a request body and a Query key, and a challenge id is the path of a `POST`
 * that asks people to a game. A link that survives neither has no builder behind it — but it does
 * have a challenge, so a bad **search** goes back to the challenge screen rather than to Play,
 * which is where the player would have come from.
 */
export default function ChallengeFillRoute() {
  const params = useLocalSearchParams();
  const challenge = parseChallengeRouteParams(params);
  const builder = parseBuilderRouteParams(params);

  if (challenge === undefined) return <Redirect href="/chats" />;
  if (builder === undefined) {
    return <Redirect href={`/chats/challenge/${challenge.challengeId}`} />;
  }

  return <BuilderScreen arrivalSearchId={builder.search} />;
}
