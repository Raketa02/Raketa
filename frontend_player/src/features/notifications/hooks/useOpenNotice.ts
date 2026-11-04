/**
 * **A notice, opened** — the one place a tap on a notice becomes a screen, whether it was a row of
 * the recent list, the in-app banner or the phone's own notification (#559; the screens A9:
 * *tapping a notice opens the game it is about*; `docs/architecture.md` Part 13: *routing is
 * centralized*).
 *
 * | Opens | The screen | Read again |
 * | --- | --- | --- |
 * | a booked game | its details over Home (`proposals`' `bookedGameRoute`) | the booking |
 * | a step at the court (#664) | its result screen over Home (`bookedResultRoute`) | the booking, and the games |
 * | a Fill in alert's open seat | the rescue, seen from outside, in its group (`rescueRoute`) | the booking |
 * | a game still filling, or one that did not fill | its details in its group (`gameRoute`) | the game |
 * | a card waiting for the player | the group's deck, the card on top (`groups`' `groupDeckRoute`) | the group's decks |
 * | no game — *Get your level* (#731) | Home, laid down (`shell`'s `openTab`) | the ratings, and a run left halfway |
 *
 * **Pushed over wherever the player is**, and never a stack laid down: a notice is not a tab press,
 * and *back* goes where the player was — the list, or the screen the banner was over. Which tab's
 * column lights is the route's: a booked game is Home's, the rest are Play's — as a live yes on
 * Payments opens a game's details in Play.
 *
 * **Except Home**, which is a tab's root rather than a screen over one: a second Home pushed over
 * the list would put Home behind Home, so a notice about no game lays Home down as the tab bar
 * does — from the list, from the banner over any screen, or from a push tapped — and is nothing to
 * do where Home is already on screen. Its card is drawn from the ratings and a run left halfway,
 * marked stale first: a level got on another phone since leaves no card asking for one.
 *
 * **The reads behind it are marked stale first**, so the screen draws what the notice said rather
 * than a read from before it: a deck read twenty seconds ago does not hold the card a notice is
 * about, nor a games list the score *Is that right?* asks about. The result screen finds its game
 * through two reads — the booking, which names its Game, and `GET /games`, which holds it. The
 * destination is still the server's to authorize — a game the player can no longer see draws its
 * own refusal, as any screen does.
 */

import { useQueryClient, type QueryClient, type QueryKey } from '@tanstack/react-query';
import { usePathname, useRouter } from 'expo-router';
import { useCallback } from 'react';

import { gameKeys } from '@/features/games/types';
import { groupDeckRoute } from '@/features/groups/types';
import { onboardingKeys } from '@/features/onboarding/types';
import {
  bookedGameRoute,
  bookedResultRoute,
  gameRoute,
  proposalKeys,
  rescueRoute,
} from '@/features/proposals/types';
import { openTab } from '@/features/shell/types';

import type { NoticeTarget } from '../domain/notice';

/** A screen pushed over wherever the player is — every destination but Home. */
type Pushed = Parameters<ReturnType<typeof useRouter>['push']>[0];

/** Where a notice opens — pushed over the player's screen, or Home laid down — and its reads. */
type Destination =
  | { readonly route: Pushed; readonly reads: readonly QueryKey[] }
  | { readonly home: true; readonly reads: readonly QueryKey[] };

/** Where a notice opens, and the reads that screen draws. */
function destinationOf(target: NoticeTarget): Destination {
  switch (target.opens) {
    case 'home':
      return { home: true, reads: [onboardingKeys.ratings(), onboardingKeys.runInProgress()] };
    case 'booking':
      return {
        route: bookedGameRoute(target.bookingId),
        reads: [proposalKeys.booking(target.bookingId)],
      };
    case 'result':
      return {
        route: bookedResultRoute(target.bookingId),
        reads: [proposalKeys.booking(target.bookingId), gameKeys.list()],
      };
    case 'rescue':
      return {
        route: rescueRoute(target.groupId, target.bookingId),
        reads: [proposalKeys.booking(target.bookingId)],
      };
    case 'game':
      return {
        route: gameRoute(target.groupId, target.proposalId, target.sport, target.kind),
        reads: [proposalKeys.proposal(target.proposalId)],
      };
    case 'deck':
      return {
        route: groupDeckRoute(target.groupId, {
          sport: target.sport,
          kind: target.kind,
          card: target.proposalId,
        }),
        reads: [proposalKeys.group(target.groupId)],
      };
  }
}

/** Every read a destination draws, marked stale. */
export function rereadDestination(client: QueryClient, target: NoticeTarget) {
  return Promise.all(
    destinationOf(target).reads.map((queryKey) => client.invalidateQueries({ queryKey })),
  );
}

export function useOpenNotice(): (target: NoticeTarget) => void {
  const router = useRouter();
  const client = useQueryClient();
  const pathname = usePathname();

  return useCallback(
    (target: NoticeTarget) => {
      void rereadDestination(client, target);
      const destination = destinationOf(target);
      if ('home' in destination) {
        openTab('home', pathname);
        return;
      }
      router.push(destination.route);
    },
    [client, router, pathname],
  );
}
