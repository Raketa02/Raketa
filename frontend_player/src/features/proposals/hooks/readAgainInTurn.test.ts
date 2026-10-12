/**
 * **Read again, in turn** — what an answer settling does to the reads it must show, against a real
 * `QueryClient` and reads the test lets go one at a time.
 *
 * TanStack's own invalidation throws a read that is out away and starts another; a player who
 * answers faster than the deck is read then never sees one land. These hold the replacement to its
 * three promises: the read that is out lands, one read follows it, and everyone who asked while it
 * was out shares that one.
 */

import { QueryClient, QueryObserver } from '@tanstack/react-query';

import { readAgainInTurn } from './useGroupDeck';

const KEY = ['proposals', 'deck', 'g1', 'PADEL', 'COMPETITIVE'] as const;

interface Read {
  readonly signal: AbortSignal;
  readonly answer: (value: number) => void;
}

/** A client with one deck on screen, whose every read waits until the test answers it. */
function deckOnScreen() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const reads: Read[] = [];
  const observer = new QueryObserver<number>(client, {
    queryKey: KEY,
    queryFn: ({ signal }) =>
      new Promise<number>((resolve) => {
        reads.push({ signal, answer: resolve });
      }),
  });
  const stop = observer.subscribe(() => {});
  return { client, reads, stop };
}

/** Let every promise that can settle, settle. */
async function settle() {
  for (let turn = 0; turn < 20; turn += 1) await Promise.resolve();
}

describe('readAgainInTurn', () => {
  it('lets the read that is out land, and every answer that settled meanwhile shares one more', async () => {
    const { client, reads, stop } = deckOnScreen();
    expect(reads).toHaveLength(1);

    const first = readAgainInTurn(client, ['proposals', 'deck', 'g1']);
    const second = readAgainInTurn(client, ['proposals', 'deck', 'g1']);
    await settle();
    // Nothing thrown away, nothing started beside it.
    expect(reads).toHaveLength(1);

    reads[0]!.answer(1);
    await settle();
    expect(reads[0]!.signal.aborted).toBe(false);
    expect(client.getQueryData(KEY)).toBe(1);
    // It may predate both answers: one read follows it, for both.
    expect(reads).toHaveLength(2);

    reads[1]!.answer(2);
    await Promise.all([first, second]);
    expect(client.getQueryData(KEY)).toBe(2);
    expect(reads).toHaveLength(2);
    stop();
  });

  it('reads at once when nothing is out', async () => {
    const { client, reads, stop } = deckOnScreen();
    reads[0]!.answer(1);
    await settle();

    const again = readAgainInTurn(client, ['proposals', 'deck', 'g1']);
    await settle();
    expect(reads).toHaveLength(2);

    reads[1]!.answer(2);
    await again;
    expect(client.getQueryData(KEY)).toBe(2);
    stop();
  });

  it('marks a read nobody is drawing stale, and reads nothing for it', async () => {
    const client = new QueryClient();
    client.setQueryData(KEY, 1);

    await readAgainInTurn(client, ['proposals', 'deck', 'g1']);

    expect(client.getQueryState(KEY)?.isInvalidated).toBe(true);
    expect(client.getQueryState(KEY)?.fetchStatus).toBe('idle');
  });
});
