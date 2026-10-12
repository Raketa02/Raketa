'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import type { Outcome } from '@/server/outcome';
import { isId, type RefusalAbout } from '@/ui/forms';

import {
  toCancelBody,
  toFreeCourts,
  toMoveBody,
  type CancelGivesBack,
  type FreeCourt,
} from './mappers';
import { checkAct, readAct } from './schemas';

/** What landed, on which game, as the page named it to the desk. */
export type Done = { readonly id: string; readonly name: string } & (
  | { readonly act: 'move'; readonly court: string }
  | { readonly act: 'cancel'; readonly givesBack: CancelGivesBack | null }
);

export interface BookingActState {
  readonly done: Done | null;
  /** What the backend or the page refused, said about the game the desk saw. */
  readonly refusal: RefusalAbout | null;
}

/**
 * A move or a cancel changes more than the day on Bookings: the hours Courts & prices holds for a
 * game, and Money's month. So every page is drawn again.
 */
function redraw(): void {
  revalidatePath('/', 'layout');
}

/** A 404 or a 409 means the page was out of date: drawn again, it shows the truth. */
function redrawIfStale(error: { readonly status: number }): void {
  if (error.status === 404 || error.status === 409) redraw();
}

/** What came of an act: what was refused, or what landed, which is on the page, drawn again. */
function settle<T>(outcome: Outcome<T>, name: string, done: (data: T) => Done): BookingActState {
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { done: null, refusal: { code: outcome.error.code, name } };
  }
  redraw();
  return { done: done(outcome.data), refusal: null };
}

/**
 * **Move** or **Cancel** one game: which is the hidden `act`.
 *
 * - *Move* onto another free court of its sport at its hour, until it starts.
 * - *Cancel*, with the reason the players are told: before the cut-off every hold is let go,
 *   after it everybody is refunded in full.
 */
export async function actOnBooking(
  _previous: BookingActState,
  form: FormData,
): Promise<BookingActState> {
  const posted = readAct(form);
  const { act, id, name, courtId, cancel, givesBack } = posted;
  const refused = checkAct(posted);
  if (refused !== null || act === null || id === null) {
    return { done: null, refusal: { code: refused ?? 'request_invalid', name } };
  }
  const path = { params: { path: { booking_id: id } } };

  switch (act) {
    case 'move':
      if (courtId === null) return { done: null, refusal: { code: 'court_required', name } };
      return settle(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/bookings/{booking_id}/move', {
            ...auth,
            ...path,
            body: toMoveBody(courtId),
          }),
        ),
        name,
        (data) => ({ act, id, name, court: data.name }),
      );
    case 'cancel':
      if (cancel === null) {
        return { done: null, refusal: { code: 'cancel_reason_required', name } };
      }
      return settle(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/bookings/{booking_id}/cancellation', {
            ...auth,
            ...path,
            body: toCancelBody(cancel),
          }),
        ),
        name,
        () => ({ act, id, name, givesBack }),
      );
  }
}

/** Where a game can be moved, or why it cannot be moved now (a refusal's code). */
export type FreeCourtsAnswer =
  | { readonly courts: readonly FreeCourt[]; readonly refusal: null }
  | { readonly courts: null; readonly refusal: string };

/**
 * **The Move dialog's courts**: every other court of the game's sport the club still sells at
 * its hour, read as the dialog opens, since a dialog opens with no render to read in. A game no
 * longer movable says why, and the page is drawn again with the truth.
 */
export async function readFreeCourts(bookingId: string): Promise<FreeCourtsAnswer> {
  if (!isId(bookingId)) return { courts: null, refusal: 'booking_not_found' };
  const outcome = await writeAsClub((api, auth) =>
    api.GET('/api/v1/club/bookings/{booking_id}/free-courts', {
      ...auth,
      params: { path: { booking_id: bookingId } },
    }),
  );
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { courts: null, refusal: outcome.error.code };
  }
  return { courts: toFreeCourts(outcome.data), refusal: null };
}
