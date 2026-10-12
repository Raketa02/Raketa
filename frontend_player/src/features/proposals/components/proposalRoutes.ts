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
 * **A rescue seen from outside** (#557) — a *Seat open* card's details, or a *Seats to fill* row's,
 * pushed over the group's page under Play like a game's details: the booked game, read by its
 * booking's id, for a reader its open seat is offered to.
 */
export function rescueRoute(groupId: string, bookingId: string) {
  return {
    pathname: '/play/group/[groupId]/rescue/[bookingId]',
    params: { groupId, bookingId },
  } as const;
}

/**
 * ***Post a game*** (#558) — pushed over the group's page from Fill in's floating button or *Nothing
 * picked right now*'s third door, under Play like a game's details, so *back* is the group. Only the
 * group rides in the route: the draft is the store's, and the sport and kind are the page's.
 */
export function postAGameRoute(groupId: string) {
  return { pathname: '/play/group/[groupId]/post', params: { groupId } } as const;
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

/**
 * **The game's chat** — over its details (A4.4), or straight over Home from the card's bubble
 * (Q100): *back* is whichever screen opened it.
 */
export function bookedChatRoute(bookingId: string) {
  return { pathname: '/booking/[bookingId]/chat', params: { bookingId } } as const;
}

/**
 * The result, told and agreed on today's game screen, over the details — or over wherever the player
 * is, from a notice of a step at the court (#664).
 */
export function bookedResultRoute(bookingId: string) {
  return { pathname: '/booking/[bookingId]/result', params: { bookingId } } as const;
}
