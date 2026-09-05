import { Redirect, useLocalSearchParams } from 'expo-router';

import { ResultScreen, parseGameRouteParams } from '@/features/games/types';

/**
 * The result conversation for one game — **pushed over the Now tab, and genuinely a push.**
 *
 * The shell's ordinary move is a replace, and this is one of the few screens it is not: the Now
 * tab stays underneath, and backing out of a game returns to the list it was tapped from.
 *
 * A param that does not survive the schema has no game behind it, so the screen it would draw is
 * the *no game of yours has this address* one — and the honest place to say that is the list
 * rather than a screen about nothing. `Redirect` rather than a push, because a link this app
 * cannot read never was a place the player came from.
 */
export default function GameRoute() {
  const params = useLocalSearchParams();
  const parsed = parseGameRouteParams(params);

  if (parsed === undefined) return <Redirect href="/" />;

  return <ResultScreen gameId={parsed.gameId} />;
}
