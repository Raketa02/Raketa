/**
 * **Home's reads** ([#556](https://github.com/Raketa02/Raketa/issues/556)) — the booked games
 * (`GET /home`), one booked game in detail (`GET /bookings/{id}`), which of them this phone has
 * opened, and the clock every fold over them runs on.
 *
 * **The shell holds Home all session**: the bar's Home badge is the read's `needing_you`, so the
 * query is observed for as long as the tabs are up, and whatever invalidates it — a fill, a
 * foreground — re-reads it at once. The app's defaults otherwise, `gameKeys`' reasoning: a list of
 * the player's own games, made current by foregrounding.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { currentUserQuery } from '@/features/auth/types';
import type { AppError } from '@/shared/errors';
import { phonePreferenceKeys } from '@/shared/lib/preferences';

import { bookedGameIds, openedToKeep, type BookedGame, type Home } from '../domain/home';
import { keepOpenedGames, readBooking, readHome, readOpenedGames } from '../use-cases/home';

import { proposalKeys } from './proposalKeys';
import { useDeckClock } from './useDeckClock';

export function useHome() {
  return useQuery<Home, AppError>({
    queryKey: proposalKeys.home(),
    queryFn: ({ signal }) => readHome({ signal }),
  });
}

/** One booked game's read — the details', and *It's a game!*'s when a row's join is booked. */
function bookingQuery(bookingId: string) {
  return {
    queryKey: proposalKeys.booking(bookingId),
    queryFn: ({ signal }: { readonly signal: AbortSignal }) => readBooking(bookingId, { signal }),
  };
}

/**
 * `null` is a game in a sport this build cannot name — read, and nothing to draw. `enabled` false asks
 * nothing — *It's a game!* reads the booking only when the yes held no sides of its own.
 */
export function useBooking(
  bookingId: string,
  { enabled = true }: { readonly enabled?: boolean } = {},
) {
  return useQuery<BookedGame | null, AppError>({ ...bookingQuery(bookingId), enabled });
}

/** The booking's read, as `BookingAbsent` asks about it. */
export function bookingReadState(read: ReturnType<typeof useBooking>) {
  return {
    paused: read.fetchStatus === 'paused',
    pending: read.isPending && read.fetchStatus !== 'paused',
    error: read.error,
    retry: () => void read.refetch(),
  };
}

/**
 * **Home's badge, and the Games its cards stand for** — what the shell reads for the bar. The count
 * is the server's (`needing_you`: the cards that need the reader and every payment they have to
 * confirm); the ids are every booked game's Game, which is in `GET /games` too, so the Classic half
 * of the badge — and of the rail — leaves them out rather than counting one game twice.
 */
export function useHomeBadge(): {
  readonly needingYou: number;
  readonly gameIds: ReadonlySet<string>;
} {
  const { data } = useHome();
  return { needingYou: data?.needingYou ?? 0, gameIds: bookedGameIds(data?.games ?? []) };
}

/**
 * **Now, on the read's clock** — the read's `read_at` moved on by however long the phone has held
 * it. While a card's cut-off is still ahead the clock ticks (`useDeckClock`'s thirty seconds), so
 * *free to leave until Sat 17:00* switches at that instant by itself, as the wire asks; otherwise
 * it stands at the read.
 */
export function useReadClock(readAt: string | undefined, receivedAt: number, ticking: boolean) {
  const device = useDeckClock(receivedAt, ticking);
  const served = readAt === undefined ? Number.NaN : Date.parse(readAt);
  return Number.isNaN(served) ? device : served + (device - receivedAt);
}

/**
 * **The booked games this account has opened on this phone** — what keeps a card *new until opened*
 * (the mechanics §11.4). Kept per account by `shared/lib/preferences` and forgotten at sign-out, as
 * the Play segment is; held in the query cache for the session, never in a store.
 *
 * `opened` is `undefined` while the phone is being read, and `open` keeps a game opened — pruned to
 * the games Home still holds, so the list is never longer than the player's games.
 */
export function useOpenedGames(): {
  readonly opened: ReadonlySet<string> | undefined;
  readonly open: (bookingId: string) => void;
} {
  const client = useQueryClient();
  // Whose phone memory this is — read from the cache once, as the Play segment reads it: the
  // entry gate has read the player before a tab can mount, and a sign-out tears the tree down.
  const [account] = useState(() => client.getQueryData(currentUserQuery().queryKey)?.id);

  const read = useQuery({
    queryKey: phonePreferenceKeys.one(account ?? '', 'openedGames'),
    queryFn: () => readOpenedGames(account ?? ''),
    enabled: account !== undefined,
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const open = useCallback(
    (bookingId: string) => {
      if (account === undefined) return;
      const key = phonePreferenceKeys.one(account, 'openedGames');
      // What was kept, from the cache — or from the phone, when the details were reached before
      // Home read it: writing over a list never read would forget every game opened before.
      void client
        .fetchQuery({ queryKey: key, queryFn: () => readOpenedGames(account), staleTime: Infinity })
        .then((kept) => {
          if (kept.includes(bookingId)) return undefined;
          const home = client.getQueryData<Home>(proposalKeys.home());
          const next = openedToKeep(
            kept,
            bookingId,
            home?.games.map((game) => game.bookingId),
          );
          client.setQueryData(key, next);
          return keepOpenedGames(account, next);
        });
    },
    [account, client],
  );

  return {
    opened: read.data === undefined ? undefined : new Set(read.data),
    open,
  };
}
