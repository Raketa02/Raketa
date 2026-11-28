/**
 * **When a read counts as finished** (PRD #867, [#871](https://github.com/Rakieta02/Rakieta/issues/871);
 * the loading shimmer log §5, Q13) — the rule a screen built from several reads waits on before it
 * reveals: a read has finished once it has landed, been refused, paused for a connection, or failed
 * once and started retrying. Read off Query's own state.
 */

import {
  QueryClient,
  QueryClientProvider,
  QueryObserver,
  onlineManager,
  type QueryState,
} from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react-native';
import type { ReactNode } from 'react';

import {
  readHasFinished,
  readStage,
  useQueryCacheAnswer,
  useReadFinished,
  type ReadStage,
} from './readFinished';

type Read = Pick<QueryState, 'data' | 'status' | 'fetchStatus' | 'fetchFailureCount'>;

const OUT: Read = {
  data: undefined,
  status: 'pending',
  fetchStatus: 'fetching',
  fetchFailureCount: 0,
};

describe('readHasFinished', () => {
  it.each<[string, Read | undefined, boolean]>([
    ['a read nobody has asked for yet', undefined, false],
    ['a read on its way', OUT, false],
    ['a read waiting for what it is asked with', { ...OUT, fetchStatus: 'idle' }, false],
    [
      'a read that landed',
      { ...OUT, data: ['Inés'], status: 'success', fetchStatus: 'idle' },
      true,
    ],
    [
      'a read refused',
      { ...OUT, status: 'error', fetchStatus: 'idle', fetchFailureCount: 3 },
      true,
    ],
    ['a read paused for a connection', { ...OUT, fetchStatus: 'paused' }, true],
    ['a read that failed once and is retrying', { ...OUT, fetchFailureCount: 1 }, true],
    [
      'a landed read being read again',
      { ...OUT, data: ['Inés'], status: 'success', fetchStatus: 'fetching' },
      true,
    ],
  ])('%s', (_case, read, finished) => {
    expect(readHasFinished(read)).toBe(finished);
  });
});

/**
 * **How far a read has come** (#875) — for a skeleton that must stand again when a read that ended
 * with nothing to show sets out once more: *Try again*, or the connection back.
 */
describe('readStage', () => {
  it.each<[string, Read | undefined, ReadStage]>([
    ['a read nobody has asked for yet', undefined, 'reading'],
    ['a read on its way', OUT, 'reading'],
    ['a read waiting for what it is asked with', { ...OUT, fetchStatus: 'idle' }, 'reading'],
    [
      'a read that landed',
      { ...OUT, data: ['Inés'], status: 'success', fetchStatus: 'idle' },
      'landed',
    ],
    [
      'a landed read being read again',
      { ...OUT, data: ['Inés'], status: 'success', fetchStatus: 'fetching' },
      'landed',
    ],
    [
      'a landed read whose re-read was refused',
      { ...OUT, data: ['Inés'], status: 'error', fetchStatus: 'idle', fetchFailureCount: 3 },
      'landed',
    ],
    [
      'a read refused',
      { ...OUT, status: 'error', fetchStatus: 'idle', fetchFailureCount: 3 },
      'ended',
    ],
    ['a read paused for a connection', { ...OUT, fetchStatus: 'paused' }, 'ended'],
    ['a read that failed once and is retrying', { ...OUT, fetchFailureCount: 1 }, 'ended'],
  ])('%s', (_case, read, stage) => {
    expect(readStage(read)).toBe(stage);
  });
});

function harness() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: 1, retryDelay: 1_000, gcTime: Infinity } },
  });
  function wrapper({ children }: { readonly children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  }
  return { client, wrapper };
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  onlineManager.setOnline(true);
  jest.useRealTimers();
});

describe('useReadFinished', () => {
  it('says so once the read lands', async () => {
    const { client, wrapper } = harness();
    let land: (names: string[]) => void = () => {};
    const observer = new QueryObserver(client, {
      queryKey: ['people'],
      queryFn: () => new Promise<string[]>((resolve) => (land = resolve)),
    });
    const stop = observer.subscribe(() => {});
    const { result } = renderHook(() => useReadFinished(['people']), { wrapper });

    expect(result.current).toBe(false);
    await act(async () => land(['Inés']));
    await act(() => jest.advanceTimersByTimeAsync(0));

    expect(result.current).toBe(true);
    stop();
  });

  it('says so at its first failure, while Query retries it', async () => {
    const { client, wrapper } = harness();
    const observer = new QueryObserver(client, {
      queryKey: ['people'],
      queryFn: () => Promise.reject(new Error('Network request failed')),
    });
    const stop = observer.subscribe(() => {});
    const { result } = renderHook(() => useReadFinished(['people']), { wrapper });

    await act(() => jest.advanceTimersByTimeAsync(0));

    expect(client.getQueryState(['people'])?.status).toBe('pending');
    expect(result.current).toBe(true);
    stop();
  });

  it('says so while the read waits for a connection', async () => {
    const { client, wrapper } = harness();
    onlineManager.setOnline(false);
    const observer = new QueryObserver(client, {
      queryKey: ['people'],
      queryFn: () => Promise.resolve(['Inés']),
    });
    const stop = observer.subscribe(() => {});
    const { result } = renderHook(() => useReadFinished(['people']), { wrapper });

    await act(() => jest.advanceTimersByTimeAsync(0));

    expect(result.current).toBe(true);
    stop();
  });

  it('is already true at the first draw for a read in the cache', () => {
    const { client, wrapper } = harness();
    client.setQueryData(['people'], ['Inés']);

    const { result } = renderHook(() => useReadFinished(['people']), { wrapper });

    expect(result.current).toBe(true);
  });
});

describe('useQueryCacheAnswer', () => {
  it('draws again only when its answer changes, not on every move in the cache', async () => {
    const { client, wrapper } = harness();
    let draws = 0;
    const { result } = renderHook(
      () => {
        draws += 1;
        return useQueryCacheAnswer((reading) => reading.getQueryData(['people']) !== undefined);
      },
      { wrapper },
    );
    const before = draws;

    await act(async () => {
      client.setQueryData(['courts'], ['Court 2']);
      client.setQueryData(['clubs'], ['Bonarka Arena']);
      await jest.advanceTimersByTimeAsync(0);
    });
    expect(draws).toBe(before);

    await act(async () => {
      client.setQueryData(['people'], ['Inés']);
      await jest.advanceTimersByTimeAsync(0);
    });
    expect(result.current).toBe(true);
    expect(draws).toBeGreaterThan(before);
    const after = draws;

    // Moving on: the read refetched, and other reads with it — the answer stands, so nothing is drawn.
    await act(async () => {
      client.setQueryData(['people'], ['Inés', 'Bartek']);
      client.setQueryData(['courts'], ['Court 3']);
      await jest.advanceTimersByTimeAsync(0);
    });
    expect(draws).toBe(after);
  });
});
