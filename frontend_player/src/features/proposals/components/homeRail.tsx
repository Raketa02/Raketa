/**
 * **Home's booked games, as cards for the rail** ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the screens A8).
 *
 * Home is one rail — *today's Now rail of game cards, renamed* — and the rail is `plans`', because
 * a Classic card needs a plan beside its game. The booked games are this feature's, so what crosses
 * is a slot the shell fills: the cards drawn at the rail's width, how many, whether the read
 * failed, and **the Games they stand for** — a booked game's Game is in `GET /games` too (#542), and
 * the rail leaves those out rather than drawing one game twice. Every booked Game is in the set,
 * the shelved ones too, so an ended booking the shelf has dropped does not come back as a Classic
 * card.
 *
 * Each card is handed what the surface already holds — the read's clock, whether it is *new*, and
 * whether its room is open, from one join over the rooms (`useGameRooms`) — and reads nothing
 * itself. *Open game* pushes the details over Home, so *back* is Home.
 */

import { router } from 'expo-router';

import { useGameRooms } from '@/features/conversations/types';
import type { BookedOnTheRail } from '@/features/plans/types';

import { bookedGameIds, chatIsOpen, isNew, onHome } from '../domain/home';
import { useHome, useOpenedGames, useReadClock } from '../hooks/useHome';

import { HomeGameCard } from './HomeGameCard';
import { bookedGameRoute } from './proposalRoutes';

/** What the rail takes from this feature — `plans`' own slot type, crossed as a type alone. */
export type BookedCards = BookedOnTheRail;

export function useBookedCards(): BookedCards {
  const home = useHome();
  const rooms = useGameRooms();
  const { opened } = useOpenedGames();

  const all = home.data?.games ?? [];
  // The clock runs while a cut-off is ahead, so *free to leave until …* leaves the line by itself.
  const ticking = all.some((game) => game.money.freeToLeaveUntil !== undefined);
  const now = useReadClock(home.data?.readAt, home.dataUpdatedAt, ticking);
  const games = all.filter((game) => onHome(game, now));

  return {
    gameIds: bookedGameIds(all),
    count: games.length,
    // A failure is said only while there is nothing to draw: a re-read that failed behind cards
    // already on screen leaves them, as every list here does.
    error: home.data === undefined ? home.error : null,
    cards: (width) =>
      games.map((game) => (
        <HomeGameCard
          key={game.bookingId}
          game={game}
          now={now}
          fresh={isNew(game, opened)}
          chat={chatIsOpen(game.status) && game.gameId !== undefined && rooms.has(game.gameId)}
          width={width}
          onOpen={() => router.push(bookedGameRoute(game.bookingId))}
        />
      )),
  };
}
