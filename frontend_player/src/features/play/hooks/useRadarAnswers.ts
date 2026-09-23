/**
 * The radar's two answers — **the deck's own yes and no, given from the record sheet, with a
 * reading for their origin** ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §5).
 *
 * ## The same routes, the same ledgers, the same effects
 *
 * *Let's play* is `POST /interest` and *Not today* is `POST /passes`, exactly as the deck sends
 * them (`use-cases/answerCard`), carrying the **reading's** `search_id` as the Origin key: a
 * reading is a recorded search, so an answer given on it names it as an answer on a deal names
 * the deal. A yes's reply settles as the deck's does — `settleYes`, the one function: the count,
 * the two lists, every held deal's chip, and the yes screen pushed for a mutual naming a
 * challenge — so the two surfaces cannot disagree about what a yes did.
 *
 * ## What is the radar's own: the row is marked, and never removed
 *
 * The person **stays on the radar** — the radar hides nobody for a pass — and their card's last
 * line says what was said (`domain/reading`'s `withAnswer`). The mark is written **on the press**
 * and taken back on a refusal, which is the deck's own optimistic path with the card's leaving
 * read as a line: the retry is the button the reader already pressed, on the sheet they can
 * open again. It lives in the mutation's own `onMutate` / `onError` and not in a per-press
 * callback, for the reason the deck pushes the yes screen from its `onSuccess`: callbacks handed
 * to `mutate()` are dropped when the component that called it unmounts, the sheet closes on the
 * press, and the pane may be left before the reply lands.
 *
 * The reading's chip counting down on a liker's mutual is `settleYes`'s too, because a deck
 * yes reaches the held reading exactly as a radar yes reaches every held deal.
 *
 * ## Paused, not failed
 *
 * `networkMode: 'online'` is inherited as the deck inherits it: an answer given offline is held
 * until the connection returns, the mark stays, and the pane's amber sentence says the act
 * resumes. Nothing retries.
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { withAnswer, type RadarAnswer, type Reading } from '../domain/reading';
import { sayNo, sayYes, type CardAnswer, type InterestExpressed } from '../use-cases/answerCard';

import { settleYes } from './useDeck';
import { searchKeys } from './searchKeys';

/** *Let's play*, from the sheet: the row marked on the press, the deck's effects on the reply. */
export function useRadarYes() {
  const client = useQueryClient();

  return useMutation<InterestExpressed, AppError, CardAnswer>({
    mutationFn: sayYes,
    ...marking(client, 'yes'),
    onSuccess: (reply, answer) => settleYes(client, reply, answer),
  });
}

/** *Not today*, from the sheet: recorded, the row marked, and answered by nothing else. */
export function useRadarNo() {
  const client = useQueryClient();

  return useMutation<void, AppError, CardAnswer>({ mutationFn: sayNo, ...marking(client, 'no') });
}

/**
 * The optimistic path, as the two mutations' own handlers: the row marked on the press, and
 * the mark taken back on a refusal. One pair, so the yes and the no cannot mark differently.
 */
function marking(client: QueryClient, answered: RadarAnswer) {
  return {
    onMutate: (answer: CardAnswer) => markRow(client, answer, answered),
    onError: (_refusal: AppError, answer: CardAnswer) => markRow(client, answer, undefined),
  };
}

/** The held reading for the answer's sport, with the person's row marked — or unmarked. */
function markRow(client: QueryClient, answer: CardAnswer, answered: RadarAnswer | undefined): void {
  client.setQueryData<Reading>(searchKeys.reading(answer.sport), (held) =>
    held === undefined ? undefined : withAnswer(held, answer.playerId, answered),
  );
}
