import { QueryClient, QueryObserver } from '@tanstack/react-query';

import { LISTS_PEOPLE, holdsPeople, rereadPeopleLists, type RelationMoved } from './peopleLists';

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

  describe('given what a friend write moved', () => {
    type Card = { readonly playerId: string; readonly relation: string };
    const withRelation = (people: readonly Card[], moved: RelationMoved) =>
      people.map((one) =>
        one.playerId === moved.playerId ? { ...one, relation: moved.relation } : one,
      );
    const ROW: readonly Card[] = [
      { playerId: 'kuba', relation: 'NONE' },
      { playerId: 'ania', relation: 'NONE' },
    ];

    it('draws it on a list that holds still, in place, and marks it stale without reading it', async () => {
      const client = new QueryClient();
      const row = jest.fn(() => Promise.resolve(ROW));
      const watching = new QueryObserver(client, {
        queryKey: ['row'],
        queryFn: row,
        meta: holdsPeople(withRelation),
        staleTime: Infinity,
      }).subscribe(() => {});
      await new Promise((resolve) => setTimeout(resolve, 0));

      await rereadPeopleLists(client, { playerId: 'kuba', relation: 'SENT' });

      expect(row).toHaveBeenCalledTimes(1);
      expect(client.getQueryData(['row'])).toEqual([
        { playerId: 'kuba', relation: 'SENT' },
        { playerId: 'ania', relation: 'NONE' },
      ]);
      expect(client.getQueryState(['row'])?.isInvalidated).toBe(true);
      watching();
      client.clear();
    });

    it('still reads again every list that does not hold still', async () => {
      const client = new QueryClient();
      const counts = jest.fn(() => Promise.resolve(['3 friends']));
      const watching = new QueryObserver(client, {
        queryKey: ['counts'],
        queryFn: counts,
        meta: LISTS_PEOPLE,
      }).subscribe(() => {});
      await new Promise((resolve) => setTimeout(resolve, 0));

      await rereadPeopleLists(client, { playerId: 'kuba', relation: 'SENT' });

      expect(counts).toHaveBeenCalledTimes(2);
      watching();
      client.clear();
    });
  });

  it('reads again a list that holds still too, on a write with nothing to hand in', async () => {
    const client = new QueryClient();
    const row = jest.fn(() => Promise.resolve([]));
    const watching = new QueryObserver(client, {
      queryKey: ['row'],
      queryFn: row,
      meta: holdsPeople((people: readonly unknown[]) => people),
    }).subscribe(() => {});
    await new Promise((resolve) => setTimeout(resolve, 0));

    // A block, or a refusal that is the state moving.
    await rereadPeopleLists(client);

    expect(row).toHaveBeenCalledTimes(2);
    watching();
    client.clear();
  });
});
