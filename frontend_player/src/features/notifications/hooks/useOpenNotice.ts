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
 * | no game — *Get your level* (#731) | Home, laid down (`shell`'s `openTab`) | the ratings, the groups, a run left halfway, and Home |
 * | a friend request (#753), a friends game invitation (#759) | Home with Needs your answer up, where their cards wait (`shell`'s `openNeedsYourAnswer`, #817) | Home's, as above — all four of the sheet's sections ride on it (#819) |
 * | *You're friends* (#753) | the friend's record, a sheet over wherever the player is (`NoticesHost`) | nothing — a record reads itself on every open |
 * | *Level asked* (#758) | the sport's questionnaire, a pass begun from Home (`onboarding`'s `useAddASport`) | nothing — the start answers the opening question |
 * | *Level got* (#758) | the group's page on Friends in the sport, and its picker over it (`groups`' `groupPickerRoutes`) | your friends' lists |
 *
 * **_Level asked_ walks into the questionnaire through the level pass**, as the Skill passport's chip
 * does: the sport's assessment started — or its unfinished run handed back — a pass of that one
 * sport begun **from Home**, and a `replace` to its question. So the pass's usual return is Home's:
 * every way out lands on Home, since a notice names no group to go back to. A start that fails says
 * why as a toast where the player is — **_You have a padel level already._** when they got one since
 * the ask (`sport_already_rated`), the failure's recovery sentence otherwise — and opens nothing.
 *
 * **_Level got_ lays the group's page under its picker**: pushed alone, the picker's **Done** would
 * seat the picks on a court nobody is looking at and go back to the list. With the page on its
 * Friends tab beneath, standing on the sport, Done and *back* land on the court, as they do from
 * *+ Friends*. Your friends' lists are marked stale first — the friend's Level is what arrived, and a
 * picker drawn from a read before it would still grey them.
 *
 * **Pushed over wherever the player is**, and never a stack laid down: a notice is not a tab press,
 * and *back* goes where the player was — the list, or the screen the banner was over. Which tab's
 * column lights is the route's: a booked game is Home's, the rest are Play's — as a live yes on
 * Payments opens a game's details in Play.
 *
 * **Except Home**, which is a tab's root rather than a screen over one: a second Home pushed over
 * the list would put Home behind Home, so a notice about no game lays Home down as the tab bar
 * does — from the list, from the banner over any screen, or from a push tapped — and is nothing to
 * do where Home is already on screen. Its card is drawn from the ratings, the groups and a run left
 * halfway, marked stale first: a level got on another phone since leaves no card asking for one,
 * and a group joined on another one is not a Home with no card. **A notice whose card waits in Needs
 * your answer** (#817) lays Home down the same way and asks for the sheet, which opens once Home is
 * read again — on Home already too — and not at all when nothing waits by then: an invitation
 * answered on another phone leaves Home as it is. Home's read is the sheet's whole read since #819.
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

import { friendKeys } from '@/features/friends/types';
import { gameKeys } from '@/features/games/types';
import { groupDeckRoute, groupKeys, groupPickerRoutes } from '@/features/groups/types';
import { FROM_HOME, onboardingKeys, useAddASport } from '@/features/onboarding/types';
import {
  bookedGameRoute,
  bookedResultRoute,
  gameRoute,
  proposalKeys,
  rescueRoute,
} from '@/features/proposals/types';
import { openNeedsYourAnswer, openTab } from '@/features/shell/types';
import type { AppError } from '@/shared/errors';
import { showToast, type ToastRequest } from '@/shared/store/toast.store';
import type { Sport } from '@/shared/vocabulary/sport';

import type { NoticeTarget } from '../domain/notice';
import { useRecordOpened } from '../store/recordOpened.store';

/** A screen pushed over wherever the player is — every destination but Home. */
type Pushed = Parameters<ReturnType<typeof useRouter>['push']>[0];

/**
 * Where a notice opens — pushed over the player's screen (with a screen under it, for the picker),
 * Home laid down, a record drawn over wherever the player is, or a sport's questionnaire — and its
 * reads.
 */
type Destination =
  | { readonly route: Pushed; readonly under?: Pushed; readonly reads: readonly QueryKey[] }
  | { readonly home: true; readonly reads: readonly QueryKey[] }
  | { readonly needsYourAnswer: true; readonly reads: readonly QueryKey[] }
  | { readonly record: string; readonly reads: readonly QueryKey[] }
  | { readonly questionnaire: Sport; readonly reads: readonly QueryKey[] };

/** Where a notice opens, and the reads that screen draws. */
function destinationOf(target: NoticeTarget): Destination {
  switch (target.opens) {
    case 'home':
      return {
        home: true,
        reads: [
          onboardingKeys.ratings(),
          groupKeys.mine(),
          onboardingKeys.runInProgress(),
          proposalKeys.home(),
        ],
      };
    case 'needsYourAnswer':
      // Home's, as above — Home is laid down: the sheet's four sections are drawn from Home's one read
      // (#819), and it opens on what it says once it lands.
      return {
        needsYourAnswer: true,
        reads: [
          onboardingKeys.ratings(),
          groupKeys.mine(),
          onboardingKeys.runInProgress(),
          proposalKeys.home(),
        ],
      };
    case 'record':
      // A record is read afresh every time it opens, so there is nothing to mark stale.
      return { record: target.playerId, reads: [] };
    case 'questionnaire':
      // The start answers the opening question, so there is nothing to mark stale.
      return { questionnaire: target.sport, reads: [] };
    case 'picker': {
      const { page, picker } = groupPickerRoutes(target.groupId, target.sport);
      return { route: picker, under: page, reads: [friendKeys.all] };
    }
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

/**
 * **What opening a notice says when it cannot** — the caller's, because the words are copy
 * (`components/openNoticeWords`).
 */
export interface OpenNoticeWords {
  /** *Level asked*'s questionnaire did not start (#758): the toast that says why. */
  readonly unstarted: (sport: Sport, error: AppError) => ToastRequest;
}

export function useOpenNotice(words: OpenNoticeWords): (target: NoticeTarget) => void {
  const router = useRouter();
  const client = useQueryClient();
  const pathname = usePathname();
  const openRecord = useRecordOpened((state) => state.open);
  const { rate } = useAddASport(FROM_HOME);

  return useCallback(
    (target: NoticeTarget) => {
      void rereadDestination(client, target);
      const destination = destinationOf(target);
      if ('home' in destination) {
        openTab('home', pathname);
        return;
      }
      if ('needsYourAnswer' in destination) {
        openNeedsYourAnswer(pathname);
        return;
      }
      if ('record' in destination) {
        openRecord(destination.record);
        return;
      }
      if ('questionnaire' in destination) {
        const sport = destination.questionnaire;
        rate(sport, { onError: (error) => showToast(words.unstarted(sport, error)) });
        return;
      }
      if (destination.under !== undefined) router.push(destination.under);
      router.push(destination.route);
    },
    [client, router, pathname, openRecord, rate, words],
  );
}
