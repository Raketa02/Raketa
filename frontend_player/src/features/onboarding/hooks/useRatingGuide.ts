/**
 * **The guide on _Your rating_: whether it is up, and ending it**
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8).
 *
 * The phone's flag is held in Query, as the phone's other preferences are (`phonePreferenceKeys`):
 * the read is asynchronous and the answer is wanted at once on every later *Your rating*. So
 * ending the guide writes the answer into the cache **and** the device — the cache is what keeps
 * the next sport's rating in this pass from showing it again, and the device is what keeps every
 * later launch, and every later account on this phone, from doing so. *Got it*, *Skip* and the
 * device's back all end it the same way.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { phonePreferenceKeys } from '@/shared/lib/preferences';

import { ratingGuideIsDue } from '../domain/ratingGuide';
import { readRatingGuideShown, rememberRatingGuideShown } from '../use-cases/ratingGuide';

/** Where the phone's answer is held in Query — the flag's key, not the flag. */
const SHOWN_KEY = phonePreferenceKeys.flag('ratingGuideShown');

/** @param hasRating the screen is drawing a rating, so there is something for the guide to explain. */
export function useRatingGuide(hasRating: boolean) {
  const client = useQueryClient();
  const shown = useQuery({
    queryKey: SHOWN_KEY,
    queryFn: readRatingGuideShown,
    // The device, not the network: no connection is needed to read it, and nothing refetches it.
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const done = useCallback(() => {
    client.setQueryData(SHOWN_KEY, true);
    void rememberRatingGuideShown();
  }, [client]);

  return { open: ratingGuideIsDue(hasRating, shown.data), done };
}
