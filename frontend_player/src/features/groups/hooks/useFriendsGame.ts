/**
 * **The game being built on a group's Friends tab, and its card** — the line-up's store, the
 * friends it seats and the card it is read for, in one place
 * ([#757](https://github.com/Raketa02/Raketa/issues/757); the friends mechanics §7.1–§7.5).
 *
 * The rules are `friendsLineUp`'s; this is where they meet the reads:
 *
 * - **The faces are the picker's read** (`friends`' `useFriendsIn`), and a friend no longer on it
 *   leaves an empty seat (`withoutStrangers`).
 * - **The card is `proposals`'** (`useFriendsCard`), asked once every seat is filled, with this
 *   game's kind; **the court draws its sides** (`shownSeats`) — the same read the card under it is
 *   drawn from.
 * - **A card refused for somebody no longer a friend, or no longer rated, reads the friends again**,
 *   so the seat empties or the picker greys them.
 * - **Every act takes what the court shows as its base**, so a swap, a ×, a kind or a court never
 *   moves a face the player is looking at.
 * - **Sent** (#759), the court is empty again: the game is in Your games, and the tab starts over.
 */

import { useCallback, useEffect, useMemo } from 'react';

import { useFriendsIn } from '@/features/friends/types';
import {
  refusalOf,
  useFriendsCard,
  type FriendsCardAsk,
  type FriendsCourtPick,
} from '@/features/proposals/types';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  cardAskOf,
  emptyLineUp,
  keptAsShown,
  shownSeats,
  swapSeats,
  takeOff,
  withCourt,
  withoutCourt,
  withoutStrangers,
  type FriendsLineUp,
} from '../domain/friendsLineUp';
import type { GameIntent } from '../domain/groupPage';
import { lineUpKey, useFriendsGame } from '../store/friendsGame.store';

/** `seats` is how many stand beside the reader on the sport's court: three, or one. */
export function useFriendsGameOn(groupId: string, sport: Sport, seats: number) {
  const kind = useFriendsGame((state) => state.kind);
  const choose = useFriendsGame((state) => state.choose);
  const put = useFriendsGame((state) => state.put);
  const stored = useFriendsGame((state) => state.lineUps[lineUpKey(groupId, sport)]);

  const friendsRead = useFriendsIn(sport);
  const friends = friendsRead.data;
  const stillFriends = useMemo(
    () => (friends === undefined ? undefined : new Set(friends.map((one) => one.playerId))),
    [friends],
  );
  const lineUp = withoutStrangers(stored ?? emptyLineUp(seats), stillFriends);

  const ask = cardAskOf(lineUp);
  // A new object each render is the same question: Query keys by value.
  const cardAsk: FriendsCardAsk | undefined = ask === undefined ? undefined : { kind, ...ask };
  const card = useFriendsCard(groupId, sport, cardAsk);
  const shown = shownSeats(lineUp, card.data?.sides);

  const refusal = refusalOf(card.error?.code);
  const rereadFriends = friendsRead.refetch;
  useEffect(() => {
    if (refusal === 'not_a_friend' || refusal === 'no_level') void rereadFriends();
  }, [refusal, card.errorUpdatedAt, rereadFriends]);

  const set = (next: FriendsLineUp) => put(groupId, sport, next);

  // Read off the store when called: the card answers `court_hour_not_for_sale` for the court the
  // line-up holds then, not the one this render saw.
  const courtGone = useCallback(() => {
    const now = useFriendsGame.getState().lineUps[lineUpKey(groupId, sport)];
    if (now?.court !== undefined) put(groupId, sport, withoutCourt(now));
  }, [groupId, sport, put]);

  return {
    kind,
    friends,
    shown,
    cardAsk,
    chooseKind: (next: GameIntent) => {
      choose(next);
      const kept = keptAsShown(lineUp, shown);
      if (kept !== lineUp) set(kept);
    },
    swap: (first: string, second: string) => set(swapSeats(lineUp, shown, first, second)),
    takeOff: (playerId: string) => set(takeOff(lineUp, shown, playerId)),
    pickCourt: (court: FriendsCourtPick) => set(withCourt(lineUp, shown, court)),
    courtGone,
    /** The game was sent (#759): an empty court, as the page opens on. */
    sent: () => set(emptyLineUp(seats)),
  };
}
