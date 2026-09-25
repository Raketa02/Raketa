/**
 * **Which sport a group page is filtered by, and the player picking another** — the fast filter's
 * state, remembered per account on the phone
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2, PRD #500 stories 52–58).
 *
 * Two reads meet here: the player's ratings, which say which sports the filter lists (onboarding's
 * `useSkillRatings`, already in the cache since the entry gate read it), and the sport last picked,
 * off the phone. **Nothing is drawn until both are in** (§4: *no screen draws one choice and then
 * jumps to another*), so `sport` is `undefined` until then. The saved value is judged against the
 * ratings every time it is read — a sport the player is no longer rated in opens on the default —
 * and is **one value for every group**: the sport last picked anywhere in Play.
 *
 * The phone read is `usePlaySegment`'s posture, for its reasons: local, never waiting on the
 * network (`networkMode: 'always'`), once per account per session and kept for good, and every
 * pick written to the cache first and the phone second. **The write is not a mutation** — one key
 * nothing waits for and nothing retries.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { useSkillRatings } from '@/features/onboarding/types';
import { phonePreferenceKeys } from '@/shared/lib/preferences';
import type { Sport } from '@/shared/vocabulary/sport';

import { filterSports, openingSport } from '../domain/groupPage';
import { keepLastSport, readLastSport } from '../use-cases/lastSport';

import { useReaderId } from './useReaderId';

export interface GroupSport {
  /** The filter's sports, in the registry's order — `undefined` while either read is out. */
  readonly sports: readonly Sport[] | undefined;
  /** The sport the page is filtered by — `undefined` while either read is out, or for nobody rated. */
  readonly sport: Sport | undefined;
  readonly choose: (sport: Sport) => void;
}

export function useGroupSport(): GroupSport {
  const client = useQueryClient();
  const account = useReaderId();
  const ratings = useSkillRatings();

  const saved = useQuery({
    queryKey: phonePreferenceKeys.one(account ?? '', 'lastSport'),
    queryFn: () => readLastSport(account ?? ''),
    enabled: account !== undefined,
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // A phone that cannot tell whose choice to read is a store that cannot be read, and that gives
  // the default (ADR-0188 §4) — a pick is held in memory for as long as the page is up, kept nowhere.
  const [unkept, setUnkept] = useState<Sport>();

  const choose = useCallback(
    (sport: Sport) => {
      if (account === undefined) {
        setUnkept(sport);
        return;
      }
      client.setQueryData(phonePreferenceKeys.one(account, 'lastSport'), sport);
      void keepLastSport(account, sport);
    },
    [account, client],
  );

  const rated = ratings.data?.map((rating) => rating.sport);
  const picked = account === undefined ? unkept : saved.data;

  // `null` is a phone that answered *nothing saved*; `undefined` is one still being read.
  if (rated === undefined || (account !== undefined && picked === undefined)) {
    return { sports: undefined, sport: undefined, choose };
  }

  return { sports: filterSports(rated), sport: openingSport(rated, picked ?? undefined), choose };
}
