/**
 * **Which sport a group page is filtered by, and the player picking another** — the fast filter's
 * state, remembered per account on the phone
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2, PRD #500 stories 52–58).
 *
 * Two reads meet here: the player's ratings, which say which sports the filter lists (onboarding's
 * `useSkillRatings`, read here first since the entry gate stopped reading it, #730), and the sport last picked,
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
 * **A player group's reader rated in nothing meets the door** (ADR-0200 §2, #730): `needsALevel`
 * says so, and the page draws *Get your level* in place of its tabs. The sport pill is drawn only
 * once there is a rating to list (`sports` is empty until then), and lists only rated sports.
 * **It ends with *+ Another sport*** while there is a sport left to offer (`toOffer`, #731): any
 * she is unrated in, or an official group's own.
 *
 * The phone read is `usePlaySegment`'s posture, for its reasons: local, never waiting on the
 * network (`networkMode: 'always'`), once per account per session and kept for good, and every
 * pick written to the cache first and the phone second. **The write is not a mutation** — one key
 * nothing waits for and nothing retries.
 */

import { queryOptions, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { currentUserQuery, useReaderId } from '@/features/auth/types';
import {
  onboardingKeys,
  prefetchSkillRatings,
  useSkillRatings,
  type SkillRating,
} from '@/features/onboarding/types';
import { phonePreferenceKeys } from '@/shared/lib/preferences';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  deckSport,
  filterSports,
  needsALevel,
  openingSport,
  sportsToAdd,
  sportsToOffer,
} from '../domain/groupPage';
import { keepLastSport, readLastSport } from '../use-cases/lastSport';

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
  /**
   * **Whether the reader meets the door where play begins** — a player group's reader rated in
   * nothing (ADR-0200 §2, `needsALevel`); `false` while either read is out, and for an official
   * group, which offers its own card instead.
   */
  readonly needsALevel: boolean;
  /**
   * **What *+ Another sport* offers** — the sports the reader is unrated in, an official group's own
   * or any (ADR-0200 §4, `sportsToOffer`); empty while there is no chip, once there is nothing left
   * to offer, and while either read is out.
   */
  readonly toOffer: readonly Sport[];
  /**
   * **Whether the filter has said** (#875) — both reads in, or the ratings read ended with nothing to
   * say: refused, or held for a connection — never while it retries. What the group page's header
   * waits on.
   */
  readonly answered: boolean;
  readonly choose: (sport: Sport) => void;
}

/** **A filter with nothing to say yet** — no sports, no sport, nothing to add, offer or ask. */
const UNREAD: Omit<GroupSport, 'choose' | 'answered'> = {
  sports: undefined,
  sport: undefined,
  toAdd: [],
  needsALevel: false,
  toOffer: [],
};

/**
 * **The sport last picked, off the phone** — one definition for every reader of it: local, never
 * waiting on the network, once per account per session and kept for good (the module note).
 */
function lastSportRead(account: string) {
  return queryOptions({
    queryKey: phonePreferenceKeys.one(account, 'lastSport'),
    queryFn: () => readLastSport(account),
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
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

  const saved = useQuery({ ...lastSportRead(account ?? ''), enabled: account !== undefined });

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
    // The ratings refused or held for a connection: nothing more is coming. Not while they retry
    // after one failure — the page keeps shimmering through the backoff, as for the group's read.
    const ended = rated === undefined && (ratings.isError || ratings.isPaused);
    return { ...UNREAD, answered: ended, choose };
  }

  return {
    sports: filterSports(rated, declared),
    sport: openingSport(rated, picked ?? undefined, declared, wanted),
    toAdd: sportsToAdd(rated, declared),
    needsALevel: needsALevel(rated, declared),
    toOffer: sportsToOffer(rated, declared),
    answered: true,
    choose,
  };
}

/**
 * **The sport the deck last showed** — what Rankings opens on when Home's trophy names no sport
 * ([#775](https://github.com/Raketa02/Raketa/issues/775); the rankings mechanics §9). The filter's own
 * answer for a player group, so the same judgement as a group page's: the sport last picked while the
 * reader is still rated in it, else the first they are rated in. `null` for a reader rated in nothing,
 * whose deck shows no sport; `undefined` while either read is out.
 */
export function useDeckSport(): Sport | null | undefined {
  const account = useReaderId();
  const ratings = useSkillRatings();
  const saved = useQuery({ ...lastSportRead(account ?? ''), enabled: account !== undefined });
  // A phone that cannot tell whose choice to read has nothing saved for it, as the filter reads it.
  return deckSport(
    ratings.data?.map((rating) => rating.sport),
    account === undefined ? null : saved.data,
  );
}

/**
 * **The deck's sport, off the cache** (#874) — `useDeckSport`'s answer where no hook can ask: the
 * launch's warm-up, which works out Top 10's opening sport before Home is drawn.
 */
export function deckSportIn(client: QueryClient): Sport | null | undefined {
  const account = readerIn(client);
  const ratings = client.getQueryData<readonly SkillRating[]>(onboardingKeys.ratings());
  return deckSport(
    ratings?.map((rating) => rating.sport),
    account === undefined ? null : client.getQueryData(lastSportRead(account).queryKey),
  );
}

/**
 * **The two reads the deck's sport is answered from, set out before Home is drawn** (#874) — the
 * ratings and the sport last picked, under the hook's own definitions, so Top 10's opening sport is
 * known within the launch's warm-up and the filter finds both read.
 */
export function prefetchDeckSport(client: QueryClient): Promise<unknown> {
  const account = readerIn(client);
  return Promise.all([
    prefetchSkillRatings(client),
    account === undefined ? undefined : client.prefetchQuery(lastSportRead(account)),
  ]);
}

/** Whose phone memory this is — the cached player, as `useReaderId` reads it. */
function readerIn(client: QueryClient): string | undefined {
  return client.getQueryData(currentUserQuery().queryKey)?.id;
}

/**
 * **An official group's declared sports, whoever is reading** — the Administrator's Members
 * (#529). Somebody who runs a group need not play, so the filter lists every sport the group
 * declares, in the order it is served (the registry's), and opens on the first. **A pick is held
 * while the screen is up and kept nowhere**: Play's last sport is the player's choice, and an
 * Administrator looking down a list has not made one. Nothing until the group is read, and never
 * *+ Another sport*: the list is the group's, not a level the reader is asked for.
 */
export function useDeclaredSport(declared: readonly Sport[] | undefined): GroupSport {
  const [picked, setPicked] = useState<Sport>();

  if (declared === undefined) return { ...UNREAD, answered: false, choose: setPicked };

  const sport = picked !== undefined && declared.includes(picked) ? picked : declared[0];
  return { ...UNREAD, sports: declared, sport, answered: true, choose: setPicked };
}
