'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import type { Outcome } from '@/server/outcome';
import { isId, type RefusalAbout } from '@/ui/forms';

import {
  toAccepted,
  toCancelBody,
  toFreeCourts,
  toMoveBody,
  toRefusalBody,
  type Accepted,
  type FreeCourt,
} from './mappers';
import { checkAct, readAct } from './schemas';

/** What landed, on which game, as the page named it to the desk. */
export type Done = { readonly id: string; readonly name: string } & (
  | { readonly act: 'accept'; readonly accepted: Accepted }
  | { readonly act: 'refuse' }
  | { readonly act: 'move'; readonly court: string }
  | { readonly act: 'cancel' }
);

export interface BookingActState {
  readonly done: Done | null;
  /** What the backend or the page refused, said about the game the desk saw. */
  readonly refusal: RefusalAbout | null;
}

/**
 * Everything a request's answer can change is on more than one page: the badge in the frame,
 * Overview's list and the day on Bookings. So every page is drawn again.
 */
function redraw(): void {
  revalidatePath('/', 'layout');
}

/** A 404 or a 409 means the page was out of date: drawn again, it shows the truth. */
function redrawIfStale(error: { readonly status: number }): void {
  if (error.status === 404 || error.status === 409) redraw();
}

function settle<T>(outcome: Outcome<T>, name: string, done: (data: T) => Done): BookingActState {
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { done: null, refusal: { code: outcome.error.code, name } };
  }
  redraw();
  return { done: done(outcome.data), refusal: null };
}

/**
 * **Accept**, **Refuse**, **Move** or **Cancel** one game: which is the hidden `act`.
 *
 * - *Accept* books an On request game: everybody is charged now, all together or not at all;
 *   a payment that does not go through leaves nobody paid and the game looking for a player.
 * - *Refuse*, with a note for the club's own records: nobody paid.
 * - *Move* onto another free court of its sport at its hour, until it starts.
 * - *Cancel*, with the reason the players are told: everybody is refunded in full.
 */
export async function actOnBooking(
  _previous: BookingActState,
  form: FormData,
): Promise<BookingActState> {
  const posted = readAct(form);
  const { act, id, name, note, courtId, cancel } = posted;
  const refused = checkAct(posted);
  if (refused !== null || act === null || id === null) {
    return { done: null, refusal: { code: refused ?? 'request_invalid', name } };
  }
  const path = { params: { path: { booking_id: id } } };

  switch (act) {
    case 'accept':
      return settle(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/bookings/{booking_id}/acceptance', { ...auth, ...path }),
        ),
        name,
        (data) => ({ act, id, name, accepted: toAccepted(data) }),
      );
    case 'refuse':
      return settle(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/bookings/{booking_id}/refusal', {
            ...auth,
            ...path,
            body: toRefusalBody(note),
          }),
        ),
        name,
        () => ({ act, id, name }),
      );
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
        () => ({ act, id, name }),
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

/**
 * **How many requests wait now**, for the frame to see whether its badge is out of date: the
 * frame is not drawn again as the desk moves between pages, and a request arrives or runs out
 * while nobody acts. `null` when the backend could not say.
 */
export async function readRequestCount(): Promise<number | null> {
  const outcome = await writeAsClub((api, auth) => api.GET('/api/v1/club/bookings/waiting', auth));
  return outcome.ok ? outcome.data.bookings.length : null;
}
