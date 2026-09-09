import { Redirect, useLocalSearchParams } from 'expo-router';

import { parseGameRouteParams } from '@/features/games/types';
import { GameScreenWithPlan } from '@/features/plans/types';

/**
 * One game — **pushed over the Now tab, and genuinely a push.**
 *
 * The shell's ordinary move is a replace, and this is one of the few screens it is not: the Now
 * tab stays underneath, and backing out of a game returns to the list it was tapped from.
 *
 * A param that does not survive the schema has no game behind it, so the screen it would draw is
 * the *no game of yours has this address* one — and the honest place to say that is the list
 * rather than a screen about nothing. `Redirect` rather than a push, because a link this app
 * cannot read never was a place the player came from.
 *
 * **What is mounted is the screen with its plan composed into it.** `GameScreen` is
 * `features/games`' and never learns a plan exists, so the join, the arm and the child are
 * `GameScreenWithPlan`'s — one composition, mounted unchanged at this address and at the room's
 * `details` one, and told nothing about which of the two it is.
 */
export default function GameRoute() {
  const params = useLocalSearchParams();
  const parsed = parseGameRouteParams(params);

  if (parsed === undefined) return <Redirect href="/" />;

  return <GameScreenWithPlan gameId={parsed.gameId} />;
}
