/**
 * **A notice, opened** — the one place a tap on a notice becomes a screen, whether it was a row of
 * the recent list, the in-app banner or the phone's own notification (#559; the screens A9:
 * *tapping a notice opens the game it is about*; `docs/architecture.md` Part 13: *routing is
 * centralized*).
 *
 * | Opens | The screen | Read again |
 * | --- | --- | --- |
 * | a booked game | its details over Home (`proposals`' `bookedGameRoute`) | the booking |
 * | a Fill in alert's open seat | the rescue, seen from outside, in its group (`rescueRoute`) | the booking |
 * | a game still filling, or one that did not fill | its details in its group (`gameRoute`) | the game |
 * | a card waiting for the player | the group's deck, the card on top (`groups`' `groupDeckRoute`) | the group's decks |
 *
 * **Pushed over wherever the player is**, and never a stack laid down: a notice is not a tab press,
 * and *back* goes where the player was — the list, or the screen the banner was over. Which tab's
 * column lights is the route's: a booked game is Home's, the rest are Play's — as a live yes on
 * Payments opens a game's details in Play.
 *
 * **The read behind it is marked stale first**, so the screen draws what the notice said rather than
 * a read from before it: a deck read twenty seconds ago does not hold the card a notice is about.
 * The destination is still the server's to authorize — a game the player can no longer see draws
 * its own refusal, as any screen does.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useCallback } from 'react';

import { groupDeckRoute } from '@/features/groups/types';
import { bookedGameRoute, gameRoute, proposalKeys, rescueRoute } from '@/features/proposals/types';

import type { NoticeTarget } from '../domain/notice';

/** Where a notice opens, and the read that screen draws. */
export function destinationOf(target: NoticeTarget) {
  switch (target.opens) {
    case 'booking':
      return {
        route: bookedGameRoute(target.bookingId),
        read: proposalKeys.booking(target.bookingId),
      };
    case 'rescue':
      return {
        route: rescueRoute(target.groupId, target.bookingId),
        read: proposalKeys.booking(target.bookingId),
      };
    case 'game':
      return {
        route: gameRoute(target.groupId, target.proposalId, target.sport, target.kind),
        read: proposalKeys.proposal(target.proposalId),
      };
    case 'deck':
      return {
        route: groupDeckRoute(target.groupId, {
          sport: target.sport,
          kind: target.kind,
          card: target.proposalId,
        }),
        read: proposalKeys.group(target.groupId),
      };
  }
}

export function useOpenNotice(): (target: NoticeTarget) => void {
  const router = useRouter();
  const client = useQueryClient();

  return useCallback(
    (target: NoticeTarget) => {
      const { route, read } = destinationOf(target);
      void client.invalidateQueries({ queryKey: read });
      router.push(route);
    },
    [client, router],
  );
}
