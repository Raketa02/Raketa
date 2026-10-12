'use server';

import { revalidatePath } from 'next/cache';

import { writeAsClub } from '@/server/club';
import type { Outcome } from '@/server/outcome';
import { isId } from '@/ui/forms';

import {
  isCancelReason,
  toCancelBody,
  toCancelOutcome,
  toFreeCourts,
  toGameCourt,
  toMoveBody,
  type CancelGivesBack,
  type CancelOutcome,
  type FreeCourt,
  type GameCourt,
} from './mappers';
import { checkAct, readAct, type ActRefused, type BookingAct, type Foretold } from './schemas';

/** What landed, on which game, as the page named it to the desk. */
export type Done = { readonly id: string; readonly name: string } & (
  | { readonly act: 'move'; readonly court: GameCourt }
  | {
      readonly act: 'cancel';
      /** Moved to another court, or called off: the cancel's own answer. */
      readonly landed: CancelOutcome;
      /** What the dialog said it would do; `null` for *Cancel the game anyway*, or unsaid. */
      readonly foretold: Foretold | null;
      readonly givesBack: CancelGivesBack | null;
    }
);

export interface BookingActState {
  readonly done: Done | null;
  /** What the backend or the page refused, said about the game the desk saw. */
  readonly refusal: ActRefused | null;
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
function settle<T>(
  outcome: Outcome<T>,
  act: BookingAct,
  name: string,
  done: (data: T) => Done,
): BookingActState {
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { done: null, refusal: { code: outcome.error.code, name, act } };
  }
  redraw();
  return { done: done(outcome.data), refusal: null };
}

/**
 * **Move** or **Cancel** one game: which is the hidden `act`.
 *
 * - *Move* onto another free court of its sport at its hour, of its kind of court or indoor for an
 *   outdoor game, until it starts.
 * - *Cancel*, with the reason the players are told. Another of the club's courts takes the game
 *   when one can, and it moves there, nobody refunded (Q122); otherwise, or *anyway*, it is called
 *   off: before the cut-off every hold is let go, after it everybody is refunded in full.
 */
export async function actOnBooking(
  _previous: BookingActState,
  form: FormData,
): Promise<BookingActState> {
  const posted = readAct(form);
  const { act, id, name, courtId, cancel, givesBack, anyway, foretold } = posted;
  const refused = checkAct(posted);
  if (refused !== null || act === null || id === null) {
    return { done: null, refusal: { code: refused ?? 'request_invalid', name, act } };
  }
  const path = { params: { path: { booking_id: id } } };

  switch (act) {
    case 'move':
      if (courtId === null) {
        return { done: null, refusal: { code: 'court_required', name, act } };
      }
      return settle(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/bookings/{booking_id}/move', {
            ...auth,
            ...path,
            body: toMoveBody(courtId),
          }),
        ),
        act,
        name,
        (data) => ({ act, id, name, court: toGameCourt(data) }),
      );
    case 'cancel':
      if (cancel === null) {
        return { done: null, refusal: { code: 'cancel_reason_required', name, act } };
      }
      return settle(
        await writeAsClub((api, auth) =>
          api.POST('/api/v1/club/bookings/{booking_id}/cancellation', {
            ...auth,
            ...path,
            body: toCancelBody(cancel, anyway),
          }),
        ),
        act,
        name,
        // *Anyway* always calls the game off: nothing the dialog said is there to differ from.
        (data) => ({
          act,
          id,
          name,
          landed: toCancelOutcome(data),
          foretold: anyway ? null : foretold,
          givesBack,
        }),
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

/** What a cancel with one reason would do now, or why it cannot be asked (a refusal's code). */
export type CancelPreviewAnswer =
  | { readonly outcome: CancelOutcome; readonly refusal: null }
  | { readonly outcome: null; readonly refusal: string };

/**
 * **The Cancel dialog's preview** (Q122): what cancelling with the reason the desk chose would do
 * now, read each time a reason is chosen, since a dialog has no render to read in. A game no
 * longer cancellable says why, and the page is drawn again with the truth.
 */
export async function readCancelPreview(
  bookingId: string,
  reason: string,
): Promise<CancelPreviewAnswer> {
  if (!isId(bookingId)) return { outcome: null, refusal: 'booking_not_found' };
  if (!isCancelReason(reason)) return { outcome: null, refusal: 'cancel_reason_required' };
  const outcome = await writeAsClub((api, auth) =>
    api.GET('/api/v1/club/bookings/{booking_id}/cancellation/preview', {
      ...auth,
      params: { path: { booking_id: bookingId }, query: { reason } },
    }),
  );
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { outcome: null, refusal: outcome.error.code };
  }
  return { outcome: toCancelOutcome(outcome.data), refusal: null };
}
