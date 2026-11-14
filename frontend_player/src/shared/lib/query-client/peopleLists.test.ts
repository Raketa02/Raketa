import { QueryClient, QueryObserver } from '@tanstack/react-query';

import { LISTS_PEOPLE, rereadPeopleLists } from './peopleLists';

describe('rereadPeopleLists', () => {
  it('reads again every read that lists people, and only those', async () => {
    const client = new QueryClient();
    const people = jest.fn(() => Promise.resolve(['bartek.l']));
    const other = jest.fn(() => Promise.resolve(['a court']));
    const watching = [
      new QueryObserver(client, { queryKey: ['people'], queryFn: people, meta: LISTS_PEOPLE }),
      new QueryObserver(client, { queryKey: ['other'], queryFn: other }),
    ].map((observer) => observer.subscribe(() => {}));
    await new Promise((resolve) => setTimeout(resolve, 0));

    await rereadPeopleLists(client);

    expect(people).toHaveBeenCalledTimes(2);
    expect(other).toHaveBeenCalledTimes(1);
    watching.forEach((stop) => stop());
    client.clear();
  });

  it('marks one nobody is watching stale, for its next mount', async () => {
    const client = new QueryClient();
    await client.prefetchQuery({
      queryKey: ['people', 'see-all'],
      queryFn: () => Promise.resolve([]),
      meta: LISTS_PEOPLE,
      staleTime: Infinity,
    });

    await rereadPeopleLists(client);

    expect(client.getQueryState(['people', 'see-all'])?.isInvalidated).toBe(true);
    client.clear();
  });
});
