/**
 * **Where a game's details live** — pushed over the group's page from its Games deck, under Play,
 * so the Play column stays lit and *back* is the deck. Named here, beside the screens that reach
 * it, and read by the route file too: a path spelled twice is the one that goes stale.
 *
 * The sport and the kind ride with the ids because the details draw the card **the deck dealt** —
 * the read for this group, this sport and this kind — and nothing else knows which read that was.
 * All four are checked where the route reads them (`schemas/gameDetailsParams`).
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { GameKind } from '../domain/vocabulary';

export function gameRoute(groupId: string, proposalId: string, sport: Sport, kind: GameKind) {
  return {
    pathname: '/play/group/[groupId]/game/[proposalId]',
    params: { groupId, proposalId, sport, kind },
  } as const;
}

/**
 * Where the Games & money row leads — a screen pushed over the You tab, under the tab's own first
 * segment so the You column stays lit (`paymentRoutes`' reason, #554).
 */
export const YOU_GAMES_AND_MONEY_ROUTE = '/you/games-and-money';

/**
 * **A booked game's details, its room and its result** — pushed over Home (#556), under a `booking`
 * segment the shell counts as Home's (`shellTabs`' `INSIDE_A_TAB`), so the Home column stays lit
 * and *back* is Home, then the details. The id is the booking's — the same id the game had while it
 * filled — and everything else is read.
 */
export function bookedGameRoute(bookingId: string) {
  return { pathname: '/booking/[bookingId]', params: { bookingId } } as const;
}

/** The game's chat, over its details — *back* is the details (A4.4). */
export function bookedChatRoute(bookingId: string) {
  return { pathname: '/booking/[bookingId]/chat', params: { bookingId } } as const;
}

/** The result, told and agreed on today's game screen, over the details. */
export function bookedResultRoute(bookingId: string) {
  return { pathname: '/booking/[bookingId]/result', params: { bookingId } } as const;
}
