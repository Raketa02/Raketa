/**
 * The builder's three reads, and the line between them: **one act records, one selects, and
 * one only looks at what is already held.**
 *
 * | | |
 * | --- | --- |
 * | `useFillSeats` | ⚡ — a **mutation**, because `POST /lineups` mints a search and records it |
 * | `useForecast` | a **query**, because `POST /forecasts` records nothing and is a pure function of `(search_id, the set of players)` |
 * | `useSearchRecord` | **no request at all** — the record was written by the act that minted it |
 *
 * ## The forecast is a query even though it is a `POST`
 *
 * What decides it is whether the route records, not which verb it wears. ADR-0108 built this
 * route precisely so a builder session is not entered into *searches run* six times, and the
 * consequence is that its answer is cacheable, re-readable and keyed: `searchKeys.forecast`
 * sorts the ids into the key, *"so the same four in a different seat order is the same entry —
 * re-arranging is choosing another arrangement out of a response already held, and a key that
 * kept seat order would spend a round trip on a swap that has none."*
 *
 * That is the whole of §J6's *"the evenness reading, every time a seat changes"*: **only a
 * membership change is a round trip.**
 *
 * ## `useSearchRecord` fetches nothing, and that is the honest shape
 *
 * A ranked list is *"a mutation whose response is written into `searchKeys.detail(id)`"*. So
 * the entry has no fetcher: the search that minted it wrote it, and `GET /searches/{id}` is
 * not a substitute — a read-back answers with the envelope and the rows and **not the sport or
 * the week**, which were the request's, so it cannot rebuild the origin a line-up's validity
 * is judged against. Re-reading is the pool's act, with the origin already in hand
 * ([#272](https://github.com/Raketa02/Raketa/issues/272)).
 *
 * `enabled: false` is therefore not a disabled request — it is a subscription to a cache
 * entry, which is what a screen drawing a record it did not mint needs and the only thing
 * `getQueryData` cannot give: it re-renders when the entry changes, which is what makes ⚡
 * land on the court rather than on the next unrelated render.
 *
 * **`undefined` is a real, handled state** and not a loading one: it is `lineupStanding`'s
 * `unreadable`, and the builder says so rather than acting as though the line-up were current.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { courtSeating, seatedIds, type Arrangement } from '../domain/forecast';
import type { SearchRecord } from '../domain/lineup';
import { fillSeats, type FillSeatsAsk, type FillSeatsOutcome } from '../use-cases/fillSeats';
import { forecastLineup, type ForecastAsk } from '../use-cases/forecastLineup';

import { RANKED_LIST_QUERY_OPTIONS, searchKeys } from './searchKeys';

/**
 * ⚡ — and its **cache effect, which is the whole answer under a new id.**
 *
 * The fill mints its own search, so the record it wrote is the origin the line-up is about to
 * be bound to. Writing it here rather than at the call site is Part 7's *"mutations declare
 * their cache effect"*, and it is what lets the screen's own `onSuccess` do the one thing that
 * is genuinely the screen's: seat the line-up.
 *
 * `retry: false` is the app's default for a mutation and is kept for `POST /searches`' reason —
 * a fill is a recording write on a route that is deliberately not idempotent, so an automatic
 * retry is a second recorded line-up nobody asked for. The *Try again* is ⚡ itself.
 */
export function useFillSeats() {
  const client = useQueryClient();

  return useMutation<FillSeatsOutcome, AppError, FillSeatsAsk>({
    mutationFn: fillSeats,
    onSuccess: ({ record }) => {
      client.setQueryData<SearchRecord>(searchKeys.detail(record.searchId), record);

      // **And the forecast, which the fill already answered.** A line-up carries every
      // arrangement with its own forecast, so asking `POST /forecasts` about the four it just
      // seated would be Part 7's *"immediately refetch what you were just handed"* — a second
      // request for an answer already in memory, and a beat of an empty forecast card in front
      // of a court that is complete.
      client.setQueryData<readonly Arrangement[]>(
        searchKeys.forecast(record.searchId, seatedIds(courtSeating(record.court))),
        record.court.arrangements,
      );
    },
  });
}

/**
 * Every way round a composed four, and the forecast on each.
 *
 * `undefined` is *there is nobody to ask about* — an empty court — and it disables the query
 * rather than sending `players: []`, which the contract refuses: *"one, two or three."*
 *
 * It takes `RANKED_LIST_QUERY_OPTIONS` whole. The two obvious halves are the two Play postures
 * — nothing background-refetches, nothing retries without the player asking — and the third is
 * the one that matters most here: `gcTime: Infinity`, because a player who walked to the pool
 * and thought about it for six minutes must not come back to a court with no number on it.
 */
export function useForecast(ask: ForecastAsk | undefined) {
  return useQuery<readonly Arrangement[], AppError>({
    queryKey: searchKeys.forecast(ask?.searchId ?? '', ask?.players ?? []),
    queryFn: ({ signal }) =>
      // Unreachable while `enabled` is false, and typed rather than asserted: a forecast with
      // no ask is not a request this hook may invent.
      ask === undefined ? Promise.resolve([]) : forecastLineup(ask, { signal }),
    enabled: ask !== undefined,
    ...RANKED_LIST_QUERY_OPTIONS,
  });
}

/**
 * The record a search left behind — **read, never fetched.** See the module note.
 *
 * `undefined` for the id is the state before a builder has any origin at all, and it answers
 * the same way an unheld entry does: with nothing.
 */
export function useSearchRecord(searchId: string | undefined) {
  return useQuery<SearchRecord>({
    queryKey: searchKeys.detail(searchId ?? ''),
    // Nothing calls this. The entry is written by the act that minted the record, and there is
    // no route that could rebuild it — see the module note.
    queryFn: () => Promise.reject(new Error('a search record is written, never fetched')),
    enabled: false,
    ...RANKED_LIST_QUERY_OPTIONS,
  }).data;
}
