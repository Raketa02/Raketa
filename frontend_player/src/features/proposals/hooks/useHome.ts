/**
 * **Home's reads** ([#556](https://github.com/Rakieta02/Rakieta/issues/556)) — the booked games
 * (`GET /home`), one booked game in detail (`GET /bookings/{id}`), which of them this phone has
 * opened, and the clock every fold over them runs on.
 *
 * **The shell holds Home all session**: the bar's Home badge is the read's `needing_you`, so the
 * query is observed for as long as the tabs are up, and whatever invalidates it — a fill, a
 * foreground — re-reads it at once. The app's defaults otherwise, `gameKeys`' reasoning: a list of
 * the player's own games, made current by foregrounding.
 */

import { useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { useReaderId } from '@/features/auth/types';
import type { AppError } from '@/shared/errors';
import { useReadFinished } from '@/shared/lib/query-client';
import { phonePreferenceKeys } from '@/shared/lib/preferences';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PaymentToConfirm } from '../domain/fill';
import { anySeatToOpen, invitationWaits, type FriendsGameInvitation } from '../domain/friendsGame';
import {
  openedToKeep,
  withoutLevelAsksIn,
  type BookedGame,
  type Home,
  type HomeFriendRequest,
  type HomeLevelAsk,
  type HomeRanking,
} from '../domain/home';
import {
  keepDismissedGames,
  keepOpenedGames,
  readBooking,
  readDismissedGames,
  readHome,
  readOpenedGames,
} from '../use-cases/home';

import { proposalKeys } from './proposalKeys';
import { useDeckClock } from './useDeckClock';

/** Home's one read — what every hook over it observes. */
const homeRead = {
  queryKey: proposalKeys.home(),
  queryFn: ({ signal }: { readonly signal: AbortSignal }) => readHome({ signal }),
};

export function useHome() {
  return useQuery<Home, AppError>(homeRead);
}

/**
 * **Home's read, set out before Home is drawn** (#874) — the launch's warm-up, during the splash: the
 * read every hook over Home observes, so Home finds it fresh when it mounts and asks nothing twice.
 */
export function prefetchHome(client: QueryClient): Promise<void> {
  return client.prefetchQuery<Home, AppError>(homeRead);
}

/**
 * **Whether Home's one read has finished** (#871) — landed, refused, held for a connection, or failed
 * once and retrying (`readHasFinished`): what *YOUR GAMES*, the envelope and the trophy's place wait
 * on before Home reveals them. Read off the cache, so it draws again only as it turns.
 */
export function useHomeReadFinished(): boolean {
  return useReadFinished(proposalKeys.home());
}

/**
 * **TO CONFIRM · n** (#817, #819) — the payments the reader has to confirm, off Home's one read:
 * `undefined` while it is in flight or refused, which draws no section. Selected, so the section
 * draws again only when its rows move, not on every change to Home.
 */
export function useHomePaymentsToConfirm() {
  return useQuery<Home, AppError, readonly PaymentToConfirm[]>({
    ...homeRead,
    select: (home) => home.paymentsToConfirm,
  });
}

/**
 * **FRIEND REQUESTS** (#753) — the requests waiting on the reader, off Home's one read: `undefined`
 * while it is in flight or refused, which draws no row, as an empty list does. The cards are
 * `friends`' to draw and answer; the read is Home's, and so this feature's.
 */
export function useHomeFriendRequests(): readonly HomeFriendRequest[] | undefined {
  return useHome().data?.friendRequests;
}

/**
 * **ASKED FOR A LEVEL · n** (#765) — the friends' asks for a level waiting on the reader, one per
 * sport, off Home's one read: `undefined` while it is in flight or refused, which draws no section,
 * as an empty list does. They wait in Needs your answer since #816, where `friends` draws and answers
 * them; the read is Home's, and so this feature's. Until #816 Home's *Get your level* gave way to
 * them, and told *not yet read* from *none* here; it no longer reads them (ADR-0205 §4).
 */
export function useHomeLevelAsks(): readonly HomeLevelAsk[] | undefined {
  return useHome().data?.levelAsks;
}

/**
 * **The trophy in the header's corner** (#775; right of the bell since #816) — the reader's ranking,
 * off Home's one read: `undefined` only **while Home has yet to answer**; `null` once it has and
 * there is none — no result in any sport — and while it is refused or waiting for a connection with
 * nothing held: none known. The trophy is drawn either way, a number only with a place, and Rankings opens on
 * its sport; it is `rankings`' to draw, and the read is Home's, and so this feature's.
 */
export function useHomeRanking(): HomeRanking | null | undefined {
  const home = useHome();
  return rankingOf(home.data, home.isError || home.fetchStatus === 'paused');
}

/**
 * **The trophy's ranking, off the cache** (#874) — `useHomeRanking`'s answer where no hook can ask:
 * the launch's warm-up, which works out Top 10's opening sport before Home is drawn.
 */
export function homeRankingIn(client: QueryClient): HomeRanking | null | undefined {
  const read = client.getQueryState<Home, AppError>(proposalKeys.home());
  return rankingOf(read?.data, read?.status === 'error' || read?.fetchStatus === 'paused');
}

/** The one rule both ask: the read's ranking, none once it is refused or held with nothing read. */
function rankingOf(home: Home | undefined, unanswered: boolean): HomeRanking | null | undefined {
  if (home !== undefined) return home.ranking ?? null;
  return unanswered ? null : undefined;
}

/**
 * **Home, after a level was got** in these sports (#765): their ASKED FOR A LEVEL cards are dropped
 * at once — the server ends a sport's card the moment the reader holds a level in it — and Home is
 * read again, so the card is already gone on the way back from *Your rating* and the read confirms
 * it. Handed to the entry gate through the shell, which is where a rating pass ends.
 */
export function rereadHomeAfterALevel(client: QueryClient, sports: readonly Sport[]) {
  client.setQueryData<Home>(proposalKeys.home(), (home) =>
    home === undefined ? undefined : withoutLevelAsksIn(home, sports),
  );
  return client.invalidateQueries({ queryKey: proposalKeys.home() });
}

/**
 * **FRIENDS GAME · n** (#759) — the invitations waiting on the reader, off Home's one read, with the
 * read's instant and when it landed, so the cards' clocks run on the read's clock. `undefined`
 * while it is in flight or refused, which draws no row, as an empty list does.
 */
export function useHomeFriendsGames(): {
  readonly invitations: readonly FriendsGameInvitation[] | undefined;
  readonly readAt: string | undefined;
  readonly receivedAt: number;
} {
  const home = useHome();
  return {
    invitations: home.data?.friendsGames,
    readAt: home.data?.readAt,
    receivedAt: home.dataUpdatedAt,
  };
}

/**
 * **FRIENDS GAME · n, as drawn** (#759, #817) — the invitations still waiting on the read's clock,
 * which ticks while one does: a card whose time runs out leaves at that instant
 * (`invitationWaits`), as the server would no longer list it. `undefined` while Home's read is in
 * flight or refused. Needs your answer's owner reads them once, counts them and hands them to the
 * section, so the envelope never opens on a section that has nothing left to draw.
 */
export interface FriendsGamesWaiting {
  readonly waiting: readonly FriendsGameInvitation[] | undefined;
  /** Now, on the read's clock — what each card's countdown and faces are drawn at. */
  readonly now: number;
}

export function useFriendsGamesWaiting(): FriendsGamesWaiting {
  const { invitations, readAt, receivedAt } = useHomeFriendsGames();
  const now = useReadClock(readAt, receivedAt, (invitations?.length ?? 0) > 0);
  return {
    waiting: invitations?.filter((one) => invitationWaits(one.friendsGame, now)),
    now,
  };
}

/**
 * **Home's two reads, read again** — Home's, with the games, the badge and all of Needs your
 * answer, *TO CONFIRM* among it since #819; and the payments to confirm' own, which You › Payments
 * and a booked game draw (#556, #625, #817): what a notice arriving changes. *Confirm your payment
 * by 14:40 to keep your seat* puts a row there, and *Your time to pay ran out* takes the time off
 * it, as the games' lines move with every other notice.
 */
export function rereadHome(client: QueryClient) {
  // The live yeses too: a game a notice says filled may have been filled by somebody else's yes, and
  // the player's own list would still show it until they left and came back.
  return Promise.all([
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
    client.invalidateQueries({ queryKey: proposalKeys.paymentsToConfirm() }),
    client.invalidateQueries({ queryKey: proposalKeys.liveYeses() }),
  ]);
}

/**
 * **One booked game's read** — the details', and *It's a game!*'s when a row's join is booked. `null`
 * is a game in a sport this build cannot name — read, and nothing to draw. `enabled` false asks
 * nothing — *It's a game!* reads the booking only when the yes held no sides of its own.
 */
export function useBooking(
  bookingId: string,
  { enabled = true }: { readonly enabled?: boolean } = {},
) {
  return useQuery<BookedGame | null, AppError>({ ...bookingRead(bookingId), enabled });
}

function bookingRead(bookingId: string) {
  return {
    queryKey: proposalKeys.booking(bookingId),
    queryFn: ({ signal }: { readonly signal: AbortSignal }) => readBooking(bookingId, { signal }),
  };
}

/**
 * **The group a seat of this booking may be opened to** (#760) — the details' read, shared, and its
 * group only while the reader may open some seat (`anySeatToOpen`): the route reads that group's
 * name for *Open to {group}*, and no other reader's details cost a group read.
 */
export function useSeatOpeningGroup(bookingId: string | undefined): string | undefined {
  return useQuery<BookedGame | null, AppError, string | undefined>({
    ...bookingRead(bookingId ?? ''),
    enabled: bookingId !== undefined,
    select: (game) => (game !== null && anySeatToOpen(game) ? game.groupId : undefined),
  }).data;
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
 * **Home's badge** — what the shell reads for the bar: the server's `needing_you` (the cards that
 * need the reader and every payment they have to confirm), and `undefined` — nothing drawn — when
 * it is nought, still in flight or refused. The bar is told nothing about which: a spinner or a
 * `?` on permanent chrome is anxiety with no act behind it.
 */
export function useHomeBadge(): number | undefined {
  const needingYou = useHome().data?.needingYou ?? 0;
  return needingYou === 0 ? undefined : needingYou;
}

/**
 * **Now, on the read's clock** — the read's `read_at` moved on by however long the phone has held
 * it. While a card's cut-off or a time to pay is still ahead the clock ticks (`useDeckClock`'s
 * thirty seconds, `lineCanRunOut`), so *free to leave until Sat 17:00* and *until 14:40* switch at
 * that instant by themselves, as the wire asks; otherwise it stands at the read.
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
  // Whose phone memory this is — read from the cache once, and never observed (`useReaderId`).
  const account = useReaderId();

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

/**
 * **Read a booked game's reads again** — Home (its status and the bar's badge) and the game in
 * detail — once an act on its Game has landed on the result screen: a score entered or agreed, or
 * a tap saying who's here (#560, #658). `games` invalidates its own list; these
 * are this feature's, which it cannot name, so the composer hands this in.
 */
export function useRereadBooking(bookingId: string): () => void {
  const client = useQueryClient();
  return useCallback(() => {
    void client.invalidateQueries({ queryKey: proposalKeys.home() });
    void client.invalidateQueries({ queryKey: proposalKeys.booking(bookingId) });
  }, [bookingId, client]);
}

/**
 * **The called-off games this phone has removed from Home** (the bug report's P2): a player clears a
 * stale negative card at once, and it stays cleared on this phone. Kept the way the opened games are
 * — per account, in the phone's own store, never the server's — so it is nothing the club or the
 * other players see.
 */
export function useDismissedGames(): {
  readonly dismissed: ReadonlySet<string> | undefined;
  readonly dismiss: (bookingId: string) => void;
} {
  const client = useQueryClient();
  const account = useReaderId();

  const read = useQuery({
    queryKey: phonePreferenceKeys.one(account ?? '', 'dismissedGames'),
    queryFn: () => readDismissedGames(account ?? ''),
    enabled: account !== undefined,
    networkMode: 'always',
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const dismiss = useCallback(
    (bookingId: string) => {
      if (account === undefined) return;
      const key = phonePreferenceKeys.one(account, 'dismissedGames');
      // What was kept, from the cache or the phone: writing over a list never read would forget
      // every game removed before.
      void client
        .fetchQuery({
          queryKey: key,
          queryFn: () => readDismissedGames(account),
          staleTime: Infinity,
        })
        .then((kept) => {
          if (kept.includes(bookingId)) return undefined;
          const next = [...kept, bookingId];
          client.setQueryData(key, next);
          return keepDismissedGames(account, next);
        });
    },
    [account, client],
  );

  return {
    dismissed: read.data === undefined ? undefined : new Set(read.data),
    dismiss,
  };
}
