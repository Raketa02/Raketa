/**
 * Racing for a seat: the first write Now makes for itself.
 *
 * Every other action on this screen leaves for a route and writes Now's update on
 * the way back. This one has no screen of its own — the card carries the price,
 * the button carries the act, and what happens next is drawn on the card that
 * comes back — so the write lives in the feature the card belongs to, exactly as
 * leaving standby will (`ADR-0087`).
 *
 * **Not retried, on the app's own initiative or otherwise.** The app's default is
 * `retry: false` and this is a case it was written for: the write has no
 * idempotency key, because a second tap by the player who already holds the claim
 * is refused by her own claim (`ADR-0081`) and *did my first tap land* is answered
 * by the card that comes back carrying it. A retry the client makes for her would
 * be a request she did not make, against a five-minute window her money is behind.
 *
 * **No `onMutate` and no optimistic card.** Whether the seat was still there is
 * the aggregate's answer at the instant of the write, and a phone that guessed at
 * it would be holding the rule `ADR-0053` leaves it none of — and guessing *wrong*
 * here means telling her she has five minutes to pay for a seat somebody else took.
 *
 * **One cache write and no invalidation**, which is `ADR-0074`: the answer was
 * composed by the server at the instant of the write, so asking Now for the whole
 * screen again would pay the full funnel for something already in hand — and the
 * player would watch the screen under her thumb rebuild itself.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { SeatAnswer } from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';
import { takeSeat } from '../use-cases/takeSeat';

import { writeSeatAnswer } from './writeSeatAnswer';

export interface TakeSeatIntent {
  /** The match whose card she tapped. Which *seat* is the match's answer. */
  readonly matchId: string;
}

export function useTakeSeat(sport: SportFilter) {
  const queryClient = useQueryClient();

  return useMutation<SeatAnswer, AppError, TakeSeatIntent>({
    mutationFn: (intent) => takeSeat({ matchId: intent.matchId, sport }),
    retry: false,
    // The chip the write went out under is the chip its two regions come back
    // composed under, so it is read from the same value the request used rather
    // than from the store a second time: a chip changed while the write was in
    // flight must not decide where its answer lands.
    onSuccess: (answer) => writeSeatAnswer(queryClient, answer, sport),
  });
}
