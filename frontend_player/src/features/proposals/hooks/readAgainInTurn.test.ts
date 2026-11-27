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

import { proposalKeys } from './proposalKeys';
import { readAgainInTurn, reread } from './useGroupDeck';

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

/**
 * **An answer only starts the live yeses' read** (#847): the group page's tab bar reads them on every
 * tab for You’re in's badge, so a write that waited for them would hold a card hidden, or a
 * *Booking…* busy, for a badge's read. A pull and a withdrawal still wait: they draw them.
 */
describe('reread and the live yeses', () => {
  /** A client with the live yeses observed, as the page's tab bar observes them — read once. */
  async function yesesObserved() {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const reads: Read[] = [];
    const observer = new QueryObserver<number>(client, {
      queryKey: proposalKeys.liveYeses(),
      queryFn: ({ signal }) =>
        new Promise<number>((resolve) => {
          reads.push({ signal, answer: resolve });
        }),
    });
    const stop = observer.subscribe(() => {});
    reads[0]!.answer(0);
    await settle();
    return { client, reads, stop };
  }

  it('starts their read for an answer, and settles without it', async () => {
    const { client, reads, stop } = await yesesObserved();
    let settled = false;

    void reread(client, 'g1', { yeses: 'start' }).then(() => {
      settled = true;
    });
    await settle();

    expect(reads).toHaveLength(2);
    expect(settled).toBe(true);
    reads[1]!.answer(1);
    stop();
  });

  it('waits for their read on a pull and a withdrawal', async () => {
    const { client, reads, stop } = await yesesObserved();
    let settled = false;

    void reread(client, 'g1', { yeses: 'wait' }).then(() => {
      settled = true;
    });
    await settle();
    expect(reads).toHaveLength(2);
    expect(settled).toBe(false);

    reads[1]!.answer(1);
    await settle();
    expect(settled).toBe(true);
    stop();
  });

  it('leaves them alone for a no', async () => {
    const { client, reads, stop } = await yesesObserved();

    await reread(client, 'g1', { yeses: 'leave' });

    expect(reads).toHaveLength(1);
    stop();
  });
});
