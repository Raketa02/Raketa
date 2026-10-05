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
 * **An official group plays what it declares** (#519, story 56): handed its sports, the filter
 * lists only the rated ones among them and opens on one of them, whatever was picked elsewhere —
 * and the saved value stays what the player last picked, since opening is not picking. A reader
 * rated in none of them has no sport here, and `toAdd` names what they would add to have one.
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

import { filterSports, openingSport, sportsToAdd } from '../domain/groupPage';
import { keepLastSport, readLastSport } from '../use-cases/lastSport';

import { useReaderId } from './useReaderId';

export interface GroupSport {
  /** The filter's sports, in the registry's order — `undefined` while either read is out. */
  readonly sports: readonly Sport[] | undefined;
  /** The sport the page is filtered by — `undefined` while either read is out, or for nobody rated. */
  readonly sport: Sport | undefined;
  /**
   * **What the reader would add to see an official group** — every sport it plays, for a reader
   * rated in none of them (story 57); empty otherwise, and while either read is out.
   */
  readonly toAdd: readonly Sport[];
  readonly choose: (sport: Sport) => void;
}

/**
 * `declared` is an official group's declared sports; `undefined` for a player group, or none yet
 * read. `opening` is the sport a notice opened the page in (#559) — the page stands on it until the
 * player picks another, and it is never saved as a pick.
 */
export function useGroupSport(declared?: readonly Sport[], opening?: Sport): GroupSport {
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
  // The notice's sport, until the player picks one.
  const [wanted, setWanted] = useState(opening);

  const choose = useCallback(
    (sport: Sport) => {
      setWanted(undefined);
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
    return { sports: undefined, sport: undefined, toAdd: [], choose };
  }

  return {
    sports: filterSports(rated, declared),
    sport: openingSport(rated, picked ?? undefined, declared, wanted),
    toAdd: sportsToAdd(rated, declared),
    choose,
  };
}

/**
 * **An official group's declared sports, whoever is reading** — the Administrator's Members
 * (#529). Somebody who runs a group need not play, so the filter lists every sport the group
 * declares, in the order it is served (the registry's), and opens on the first. **A pick is held
 * while the screen is up and kept nowhere**: Play's last sport is the player's choice, and an
 * Administrator looking down a list has not made one. Nothing until the group is read.
 */
export function useDeclaredSport(declared: readonly Sport[] | undefined): GroupSport {
  const [picked, setPicked] = useState<Sport>();

  if (declared === undefined) {
    return { sports: undefined, sport: undefined, toAdd: [], choose: setPicked };
  }

  const sport = picked !== undefined && declared.includes(picked) ? picked : declared[0];
  return { sports: declared, sport, toAdd: [], choose: setPicked };
}
