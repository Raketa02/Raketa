/**
 * **Block and unblock** — the two writes, and what each re-reads
 * ([#587](https://github.com/Raketa02/Raketa/issues/587);
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * | Hook | Route | Re-reads |
 * | --- | --- | --- |
 * | `useBlock` | `POST /blocks` | the list, their record, every group's deck and Fill in, and what the withdrawal moved |
 * | `useUnblock` | `DELETE /blocks/{id}` | the list, their record where it is open, every group's deck and Fill in |
 *
 * ## What a block moves, and so what it re-reads
 *
 * **Their record**, because it says whether the reader blocked them: the row at its foot flips from
 * *Block* to *Unblock* on the re-read, never on a guess. **The record re-reads itself** — the sheet
 * hands its own re-read in (`reread`), because the read is `player_record`'s, and this feature
 * importing that one's keys while that one draws this one's row would be a dependency both ways
 * (architecture Part 1: circular dependencies are defects). A record is never cached between opens,
 * so an unblock on the list has no record to re-read. **Blocked players**, which lists them now.
 * **Every group's deck and Fill in** — not the one the record was opened from: a block keeps the
 * pair off one court in every group they share, so the next card dealt anywhere respects it.
 *
 * And, for a block only, **what its withdrawal moved** (ADR-0193 §4): the reader's yeses where the
 * other person is In are taken back — the live yeses, a game still filling in detail — and a game
 * waiting for one payment drops back to filling as though the reader left it, which Home and that
 * booking's own read draw. The same reads leaving a booking re-reads, because it is the same
 * departure. An unblock brings no yes back, so it re-reads none of them.
 *
 * Each write **settles once its re-reads have**, so the sheet's *Block* stays busy until the record
 * under it already says *Unblock* — the row never reads *Block* for a frame after the block stood.
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

/** The open record's own re-read, handed in by the sheet that holds it — see the module note. */
export type Reread = () => Promise<unknown>;

export function useBlock(playerId: string, reread: Reread) {
  const client = useQueryClient();
  const mutationKey = blockKeys.block(playerId);

  const act = useMutation<void, AppError, void>({
    mutationKey,
    mutationFn: () => block(playerId),
    retry: (failures, error) => failures < 1 && error.code === RACED,
    onSuccess: () => rereadAfterBlocking(client, reread),
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

export function useUnblock(playerId: string, reread?: Reread) {
  const client = useQueryClient();

  return useMutation<void, AppError, void>({
    mutationFn: () => unblock(playerId),
    onSuccess: () => {
      // The list's row goes at once — the answer is certain — and the re-read confirms it.
      client.setQueryData<readonly BlockedPlayer[]>(blockKeys.list(), (held) =>
        held?.filter((blocked) => blocked.playerId !== playerId),
      );
      return rereadAfterUnblocking(client, reread);
    },
  });
}

function rereadAfterUnblocking(client: QueryClient, reread: Reread | undefined) {
  return Promise.all([
    client.invalidateQueries({ queryKey: blockKeys.list() }),
    reread?.(),
    // Every group's deck, and the Fill in and posting reads under each group's root.
    client.invalidateQueries({ queryKey: proposalKeys.decks() }),
  ]);
}

function rereadAfterBlocking(client: QueryClient, reread: Reread) {
  return Promise.all([
    rereadAfterUnblocking(client, reread),
    // What the withdrawal moved — see the module note.
    client.invalidateQueries({ queryKey: proposalKeys.liveYeses() }),
    client.invalidateQueries({ queryKey: proposalKeys.proposals() }),
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
    client.invalidateQueries({ queryKey: proposalKeys.bookings() }),
  ]);
}
