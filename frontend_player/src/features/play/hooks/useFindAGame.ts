/**
 * Pressing *Search*: the one act, and what it leaves in the cache.
 *
 * ## The record is written, never refetched
 *
 * `POST /searches` **mints** a record and answers with it, and `GET /searches/{id}` reads the
 * same thing back *"in the same shape the `POST` returned it"*. So the response is written
 * straight into `searchKeys.detail(id)` — Part 7's *"don't immediately refetch what you were
 * just handed"* — and every later Play screen reads the search **by id** rather than from a
 * store. That is what makes an abandoned search harmless arithmetic rather than a rule
 * somebody has to remember: it wrote its rows under its own id, and nothing reads that entry.
 *
 * What is held there is the **origin search** — the id, and the sport, mode and week it was
 * asked for — **and the rows**, which joined it when a surface began drawing one: the builder
 * seats people by id and reads every fact about them back off these rows
 * ([#271](https://github.com/Raketa02/Raketa/issues/271)). The origin is what a line-up's
 * validity is derived from; the rows are what a seat is drawn from.
 *
 * ## Nothing here retries, and nothing here navigates
 *
 * Mutations ship `retry: false` and this one keeps it: a search is a recording write on a
 * route documented *"deliberately not idempotent — two taps are two searches"*, so an
 * automatic retry is a second recorded search nobody asked for. The *Try again* is the
 * screen's own *Search* control, which is `retryTarget`'s **the-search** — no record id, so
 * there is nothing to re-read.
 *
 * Where a completed search **goes** is still not decided here, and now for a second reason.
 * The builder is the destination ([#271](https://github.com/Raketa02/Raketa/issues/271)), but
 * the push is the *screen's*: the latch is a sibling of that screen and stays up over whatever
 * is pushed under it, so the moment of navigating and the moment of the wait ending are two
 * facts one component holds together. A `router.push` in here would be the screen's own
 * arrangement decided in a hook that cannot see it.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { useChangeSearchRadius } from '@/features/player_profile/types';
import type { AppError } from '@/shared/errors';

import type { SearchRecord } from '../domain/lineup';
import { findAGame, type FindAGameAsk, type SearchOutcome } from '../use-cases/findAGame';

import { searchKeys } from './searchKeys';

export function useFindAGame() {
  const client = useQueryClient();
  const radius = useChangeSearchRadius();
  const saveRadius = radius.mutateAsync;

  return useMutation<SearchOutcome, AppError, FindAGameAsk>({
    mutationFn: (ask) => findAGame(ask, { saveRadius }),
    onSuccess: ({ record }) => {
      client.setQueryData<SearchRecord>(searchKeys.detail(record.searchId), record);
    },
  });
}
