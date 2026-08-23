/**
 * What leaving is worth, asked fresh every time the screen opens.
 *
 * **`staleTime: 0`, against the app's 30-second default**, and the default's own
 * comment invites exactly this: *"data classes that differ (slow reference data,
 * live availability) override it in their own feature hook."* This is the live
 * class. The quote is the basis of an irreversible decision and it turns on
 * clocks the phone does not hold, so a screen opened twice in half a minute must
 * ask twice — a cached quote is the one thing this screen must never show.
 *
 * It is still not a promise that what is on screen stays true, and nothing here
 * pretends otherwise: the server refuses a write made against a quote that has
 * fallen and hands back the new one, which is the correction that matters.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Departure } from '../domain/Departure';
import { readDeparture } from '../use-cases/readDeparture';

import { departureKeys } from './departureKeys';

export function useDeparture(matchId: string) {
  return useQuery<Departure, AppError>({
    queryKey: departureKeys.screen(matchId),
    queryFn: ({ signal }) => readDeparture({ matchId, signal }),
    staleTime: 0,
  });
}
