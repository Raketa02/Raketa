/**
 * **Home and a booked game, read** (#556) — pass-throughs: which games are on Home, in what order,
 * with which status and money, is the server's projection (#542), and nothing about it is decided
 * on the way in. What the phone keeps — which games were opened — is read and kept here too, as
 * the Play segment's choice is one feature over.
 */

import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';

import { getBooking, getHome, postDeparture, type Cancellable } from '../api/proposalsApi';
import { openedFrom, type BookedGame, type Home } from '../domain/home';
import type { LeavingKind } from '../domain/vocabulary';
import { toBookedGame, toHome, toLeft } from '../mappers/homeMappers';

export async function readHome(options: Cancellable = {}): Promise<Home> {
  return toHome(await getHome(options));
}

/** One booked game — or nothing, for a game in a sport this build cannot name. */
export async function readBooking(
  bookingId: string,
  options: Cancellable = {},
): Promise<BookedGame | null> {
  return toBookedGame(await getBooking(bookingId, options)) ?? null;
}

/**
 * **Leave the game** (#544) — a pass-through: what leaving costs is the server's, folded on its own
 * clock and quoted by the read the sheet was drawn from. Answers which of the three it was.
 */
export async function leaveGame(bookingId: string): Promise<LeavingKind> {
  return toLeft(await postDeparture(bookingId));
}

/** The booked games whose details this account has opened on this phone. */
export async function readOpenedGames(account: string): Promise<readonly string[]> {
  return openedFrom(await readPhonePreference(account, 'openedGames'));
}

export function keepOpenedGames(account: string, opened: readonly string[]): Promise<void> {
  return savePhonePreference(account, 'openedGames', JSON.stringify(opened));
}

/** The called-off games this account has removed from Home on this phone. */
export async function readDismissedGames(account: string): Promise<readonly string[]> {
  return openedFrom(await readPhonePreference(account, 'dismissedGames'));
}

export function keepDismissedGames(account: string, dismissed: readonly string[]): Promise<void> {
  return savePhonePreference(account, 'dismissedGames', JSON.stringify(dismissed));
}
