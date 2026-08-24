/**
 * The route the *enter a score* and *answer the score* acts on a card open.
 *
 * The param is **untrusted input** — this route is reachable from a deep link and
 * the match id becomes a request path — so it is validated before anything reads
 * it, and a link that does not survive goes home rather than issuing a request
 * built from somebody else's string. Checking it is not the authorisation
 * boundary: the server answers a stranger with a 404 whatever the phone believes.
 *
 * **The path mirrors the contract's** (`/matches/{matchId}/result`), and it sits
 * beside the departure route with no `matches/[matchId]/index` between them. The
 * backend refused a general match resource on the ground that it would author the
 * match-detail screen's contract inside a ticket that is not about it; the same
 * holds here, and an address is not a promise that its parent exists.
 *
 * A route file and nothing else: the screen, its asks and its two writes live in
 * the feature. Closing goes **back**, because this route is pushed over the tab
 * tree and back is where she came from — a hard-coded home would take a player who
 * arrived from a deep link somewhere she was not.
 */

import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useCallback } from 'react';

import { ResultScreen, parseResultRouteParams } from '@/features/result/types';

export default function MatchResultRoute() {
  const params = parseResultRouteParams(useLocalSearchParams());

  const onClose = useCallback(() => {
    if (router.canGoBack()) {
      router.back();
      return;
    }
    // A cold open on a deep link has nothing behind it, and dismissing into an
    // empty stack leaves a player on a blank screen.
    router.replace('/');
  }, []);

  if (params === undefined) return <Redirect href="/" />;

  return <ResultScreen matchId={params.matchId} onClose={onClose} />;
}
