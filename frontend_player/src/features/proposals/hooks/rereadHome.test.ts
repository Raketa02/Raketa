/**
 * **A notice's re-read takes the live yeses too** ([#711]-adjacent: a game that filled because
 * somebody else's yes was the last one stayed in You › Payments' LIVE YESES until the player left
 * and came back — the server had ended it, and nothing on the phone asked again).
 *
 * `rereadHome` is what every notice that brings news of a game calls, so it is the one place the
 * list is marked stale for them. The cache flag is what is pinned, not a request count: the query
 * has no observer here, so nothing is fetched — the mark is all a screen will see on its next read.
 */

import { QueryClient } from '@tanstack/react-query';

import { proposalKeys } from './proposalKeys';
import { rereadHome } from './useHome';

describe('rereadHome', () => {
  it('marks the live yeses stale along with Home', async () => {
    const client = new QueryClient();
    client.setQueryData(proposalKeys.liveYeses(), { yeses: [] });
    client.setQueryData(proposalKeys.home(), { games: [] });

    await rereadHome(client);

    expect(client.getQueryState(proposalKeys.liveYeses())?.isInvalidated).toBe(true);
    expect(client.getQueryState(proposalKeys.home())?.isInvalidated).toBe(true);
  });
});
