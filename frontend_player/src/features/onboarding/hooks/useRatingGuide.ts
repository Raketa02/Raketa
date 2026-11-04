/**
 * **The guide on _Your rating_: whether it is up, and ending it**
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8, as amended
 * 2026-11-04 — once per account on a phone).
 *
 * The account's flag is held in Query, as the phone's other preferences are (`phonePreferenceKeys`):
 * the read is asynchronous and the answer is wanted at once on every later *Your rating*. So
 * ending the guide writes the answer into the cache **and** the device — the cache is what keeps
 * the next sport's rating in this pass from showing it again, and the device is what keeps every
 * later launch, and this account signing in again, from doing so. *Got it*, *Skip* and the
 * device's back all end it the same way.
 *
 * **Whose flag is the signed-in account's, observed** rather than read once from the cache as the
 * other preferences' readers do: the questions are up with nothing else holding the account, and
 * can outlast the cache's five minutes — a read once would then find nobody, and the guide would
 * wait for an account that never came. Never stale, so it costs no request while the account is
 * still cached, and one when it is not.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { currentUserQuery } from '@/features/auth/types';
import { useSessionStatus } from '@/shared/lib/auth';
import { phonePreferenceKeys } from '@/shared/lib/preferences';

import { ratingGuideIsDue } from '../domain/ratingGuide';
import { readRatingGuideShown, rememberRatingGuideShown } from '../use-cases/ratingGuide';

/** @param hasRating the screen is drawing a rating, so there is something for the guide to explain. */
export function useRatingGuide(hasRating: boolean) {
  const client = useQueryClient();
  const status = useSessionStatus();
  const account = useQuery({
    ...currentUserQuery(),
    staleTime: Infinity,
    enabled: status === 'authenticated',
  }).data?.id;

  const shown = useQuery({
    queryKey: phonePreferenceKeys.flag(account ?? '', 'ratingGuideShown'),
    queryFn: () => readRatingGuideShown(account ?? ''),
    // Until the account is known there is nobody whose flag to read, and the guide waits.
    enabled: account !== undefined,
    // The device, not the network: no connection is needed to read it, and nothing refetches it.
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const done = useCallback(() => {
    // The guide is only ever up once the account's flag was read, so the account is known here.
    if (account === undefined) return;
    client.setQueryData(phonePreferenceKeys.flag(account, 'ratingGuideShown'), true);
    void rememberRatingGuideShown(account);
  }, [account, client]);

  return { open: ratingGuideIsDue(hasRating, shown.data), done };
}
