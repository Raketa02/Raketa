/**
 * **Block and unblock** — the two writes, and what each re-reads
 * ([#587](https://github.com/Raketa02/Raketa/issues/587);
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * | Hook | Route | Re-reads |
 * | --- | --- | --- |
 * | `useBlock` | `POST /blocks` | the list, every group's deck and Fill in, and what the withdrawal moved |
 * | `useUnblock` | `DELETE /blocks/{id}` | the list, every group's deck and Fill in |
 *
 * ## What a block moves, and so what it re-reads
 *
 * **Their record is not read again: it closes** ([#779](https://github.com/Raketa02/Raketa/issues/779),
 * ADR-0203 §8). A record never opens between two people either of whom blocked the other, so its
 * re-read would only be refused; the record sheet hands `BlockRow` its own close instead. And an
 * unblock is made on the list alone, where no record is open. **Blocked players**, which lists them
 * now. **Every group's deck and Fill in** — not the one the record was opened from: a block keeps
 * the pair off one court in every group they share, so the next card dealt anywhere respects it.
 *
 * And, for a block only, **what its withdrawal moved** (ADR-0193 §4): the reader's yeses where the
 * other person is In are taken back — the live yeses, a game still filling in detail — and a game
 * waiting for one payment drops back to filling as though the reader left it, which Home and that
 * booking's own read draw. The same reads leaving a booking re-reads, because it is the same
 * departure. An unblock brings no yes back, so it re-reads none of them.
 *
 * Each write **settles once its re-reads have**, so the sheet's *Block* stays busy until everything
 * the block moved has been read again, and only then does the record close over it.
 *
 * ## Twice is nothing
 *
 * Both routes are idempotent, which is the correctness mechanism under a double tap; the busy
 * control is only the drawing of it. A block that lost a race with another block of the same person
 * answers `concurrent_modification`, and **its retry is the contract's own no-op**, so that one code
 * is retried once here — the global rule never retries a mutation, and this is the stated reason.
 *
 * ## Offline, a block waits — and closing the sheet takes it back
 *
 * A write held for the network resumes on the next reconnect, whatever the player is looking at by
 * then. A player who closed the confirm sheet said *don't*, so `takeBack` drops a block still
 * waiting from the queue as well as letting go of it — the group exit's rule (#529 F5).
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { proposalKeys } from '@/features/proposals/types';
import type { AppError } from '@/shared/errors';

import type { BlockedPlayer } from '../domain/blockedPlayer';
import { block, unblock } from '../use-cases/blocks';

import { blockKeys } from './blockKeys';

/** The one refusal a block retries: it lost a race, and the retry is the idempotent no-op. */
const RACED = 'concurrent_modification';

export function useBlock(playerId: string) {
  const client = useQueryClient();
  const mutationKey = blockKeys.block(playerId);

  const act = useMutation<void, AppError, void>({
    mutationKey,
    mutationFn: () => block(playerId),
    retry: (failures, error) => failures < 1 && error.code === RACED,
    onSuccess: () => rereadAfterBlocking(client),
  });

  /** The sheet was closed: forget the act, and drop it from the queue if it is still waiting. */
  function takeBack() {
    const queue = client.getMutationCache();
    for (const waiting of queue.findAll({ mutationKey, predicate: (m) => m.state.isPaused })) {
      queue.remove(waiting);
    }
    act.reset();
  }

  return { act, takeBack };
}

export function useUnblock(playerId: string) {
  const client = useQueryClient();

  return useMutation<void, AppError, void>({
    mutationFn: () => unblock(playerId),
    onSuccess: () => {
      // The list's row goes at once — the answer is certain — and the re-read confirms it.
      client.setQueryData<readonly BlockedPlayer[]>(blockKeys.list(), (held) =>
        held?.filter((blocked) => blocked.playerId !== playerId),
      );
      return rereadAfterUnblocking(client);
    },
  });
}

function rereadAfterUnblocking(client: QueryClient) {
  return Promise.all([
    client.invalidateQueries({ queryKey: blockKeys.list() }),
    // Every group's deck, and the Fill in and posting reads under each group's root.
    client.invalidateQueries({ queryKey: proposalKeys.decks() }),
  ]);
}

function rereadAfterBlocking(client: QueryClient) {
  return Promise.all([
    rereadAfterUnblocking(client),
    // What the withdrawal moved — see the module note.
    client.invalidateQueries({ queryKey: proposalKeys.liveYeses() }),
    client.invalidateQueries({ queryKey: proposalKeys.proposals() }),
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
    client.invalidateQueries({ queryKey: proposalKeys.bookings() }),
  ]);
}
