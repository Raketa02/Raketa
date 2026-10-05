'use server';

import { revalidatePath } from 'next/cache';

import { isSport, type Sport } from '@/features/club-details/mappers';
import { writeAsClub } from '@/server/club';
import type { Outcome } from '@/server/outcome';
import {
  formId,
  formText,
  hasRefusals,
  placeRefusal,
  type FormState,
  type RefusalAbout,
  type Refusals,
} from '@/ui/forms';

import {
  clubDay,
  refusedSport,
  toBookedThen,
  toCourt,
  toCourtBody,
  toCourtChange,
  toExceptionBody,
  toHoursBody,
  toPricesBody,
  toSportPrice,
  type BookedThen,
  type Court,
  type SportPrice,
} from './mappers';
import {
  checkCourt,
  checkException,
  checkPrices,
  COURT_FIELDS,
  EXCEPTION_FIELDS,
  exceptionOf,
  factsOf,
  isCourtAct,
  readCourt,
  readException,
  readHours,
  readPrices,
  type CourtAct,
  type CourtField,
  type ExceptionField,
} from './schemas';

const PAGE = '/courts';

/**
 * A 404 or a 409 means the page was out of date (a court gone, a booking made, elsewhere), so it
 * is drawn again with the truth; a backend that did not answer leaves it as it was.
 */
function redrawIfStale(error: { readonly status: number }): void {
  if (error.status === 404 || error.status === 409) revalidatePath(PAGE);
}

/** The court as the backend holds it now, or `null` when the club has no such court. */
async function heldCourt(id: string): Promise<Outcome<Court | null>> {
  const outcome = await writeAsClub((api, auth) => api.GET('/api/v1/club/courts', auth));
  if (!outcome.ok) return outcome;
  const wire = outcome.data.courts.find((each) => each.id === id);
  return { ok: true, data: wire === undefined ? null : toCourt(wire) };
}

// --- A court -----------------------------------------------------------------

export interface CourtFormState extends FormState<CourtField> {
  /** The court as the backend recorded it, after a save that landed. */
  readonly saved: Court | null;
}

function settleCourt<T>(outcome: Outcome<T>, view: (data: T) => Court): CourtFormState {
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { ...placeRefusal(outcome.error, COURT_FIELDS), saved: null };
  }
  revalidatePath(PAGE);
  return { refusals: {}, formRefusal: null, saved: view(outcome.data) };
}

/**
 * **Add court**, or **Save** an edit of the court `id` names. An edit keeps whether the court is
 * offered as the backend holds it now: switching it is the table's to do, not the form's.
 */
export async function saveCourt(
  _previous: CourtFormState,
  form: FormData,
): Promise<CourtFormState> {
  const draft = readCourt(form);
  const refusals = checkCourt(draft);
  if (hasRefusals(refusals) || draft.sport === null || draft.indoor === null) {
    return { refusals, formRefusal: null, saved: null };
  }
  const facts = factsOf({ ...draft, sport: draft.sport, indoor: draft.indoor });

  if (formText(form, 'id') === '') {
    return settleCourt(
      await writeAsClub((api, auth) =>
        api.POST('/api/v1/club/courts', { ...auth, body: toCourtBody(facts) }),
      ),
      toCourt,
    );
  }
  const gone: CourtFormState = { refusals: {}, formRefusal: 'court_not_found', saved: null };
  const id = formId(form, 'id');
  if (id === null) return gone;
  const held = await heldCourt(id);
  if (!held.ok) return { refusals: {}, formRefusal: held.error.code, saved: null };
  if (held.data === null) {
    revalidatePath(PAGE);
    return gone;
  }
  const offered = held.data.offered;
  return settleCourt(
    await writeAsClub((api, auth) =>
      api.PUT('/api/v1/club/courts/{court_id}', {
        ...auth,
        params: { path: { court_id: id } },
        body: toCourtChange(facts, offered),
      }),
    ),
    toCourt,
  );
}

export interface CourtActState {
  /** What landed, and on which court. */
  readonly done: { readonly act: CourtAct; readonly id: string } | null;
  /** What the backend refused, said about the court the desk saw. */
  readonly refusal: RefusalAbout | null;
}

function settleAct<T>(outcome: Outcome<T>, act: CourtAct, id: string, name: string): CourtActState {
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { done: null, refusal: { code: outcome.error.code, name } };
  }
  revalidatePath(PAGE);
  return { done: { act, id }, refusal: null };
}

/**
 * **Switch off**, **Switch on** or a confirmed **Delete court**, for one court: which is the
 * hidden `act`. A switch changes only whether the court is offered, over the court as the
 * backend holds it now. A court with a booking ahead is never deleted (`court_has_bookings`).
 */
export async function actOnCourt(_previous: CourtActState, form: FormData): Promise<CourtActState> {
  const act = formText(form, 'act');
  const id = formId(form, 'id');
  const name = formText(form, 'name');
  if (!isCourtAct(act)) return { done: null, refusal: { code: 'request_invalid', name } };
  if (id === null) return { done: null, refusal: { code: 'court_not_found', name } };
  const path = { params: { path: { court_id: id } } };

  if (act === 'delete') {
    return settleAct(
      await writeAsClub((api, auth) =>
        api.DELETE('/api/v1/club/courts/{court_id}', { ...auth, ...path }),
      ),
      act,
      id,
      name,
    );
  }
  const held = await heldCourt(id);
  if (!held.ok) return { done: null, refusal: { code: held.error.code, name } };
  if (held.data === null) {
    revalidatePath(PAGE);
    return { done: null, refusal: { code: 'court_not_found', name } };
  }
  const court = held.data;
  return settleAct(
    await writeAsClub((api, auth) =>
      api.PUT('/api/v1/club/courts/{court_id}', {
        ...auth,
        ...path,
        body: toCourtChange(court, act === 'switch-on'),
      }),
    ),
    act,
    id,
    name,
  );
}

// --- A week ------------------------------------------------------------------

export interface HoursState {
  /** The courts the week was saved on, by name, in the order posted. */
  readonly saved: readonly string[] | null;
  readonly formRefusal: string | null;
}

/**
 * **Save hours**, **Copy** or a sport's courts at once: the same week on every court posted, the
 * first the one on screen. Never refused over a booking or a card (#535).
 */
export async function saveHours(_previous: HoursState, form: FormData): Promise<HoursState> {
  const { courtIds, hours } = readHours(form);
  if (courtIds.length === 0) return { saved: null, formRefusal: 'court_not_found' };

  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/raketa-hours', { ...auth, body: toHoursBody(courtIds, hours) }),
  );
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { saved: null, formRefusal: outcome.error.code };
  }
  revalidatePath(PAGE);
  const names = new Map(outcome.data.courts.map((wire) => [wire.id, wire.name]));
  return {
    saved: courtIds.flatMap((id) => names.get(id) ?? []),
    formRefusal: null,
  };
}

// --- An exception ------------------------------------------------------------

export interface ExceptionFormState extends FormState<ExceptionField> {
  readonly added: boolean;
  /** The booking it would close, when that is why it was refused. */
  readonly bookedThen: BookedThen | null;
}

/**
 * **Add exception**: a day, several, or hours on a day, on every court or the ones ticked, with
 * its reason. Over a booking it is refused, naming the booking (`court_booked_then`), which the
 * club cancels instead (the mechanics §16.5).
 */
export async function addException(
  _previous: ExceptionFormState,
  form: FormData,
): Promise<ExceptionFormState> {
  const draft = readException(form);
  const refusals = checkException(draft, clubDay(Date.now()));
  if (hasRefusals(refusals)) return { refusals, formRefusal: null, added: false, bookedThen: null };

  const outcome = await writeAsClub((api, auth) =>
    api.POST('/api/v1/club/exceptions', { ...auth, body: toExceptionBody(exceptionOf(draft)) }),
  );
  if (!outcome.ok) {
    if (outcome.error.status === 404) revalidatePath(PAGE);
    return {
      ...placeRefusal(outcome.error, EXCEPTION_FIELDS),
      added: false,
      bookedThen: toBookedThen(outcome.error),
    };
  }
  revalidatePath(PAGE);
  return { refusals: {}, formRefusal: null, added: true, bookedThen: null };
}

export interface RemoveState {
  readonly refusal: string | null;
}

/** **Remove** an exception: its hours open again. */
export async function removeException(
  _previous: RemoveState,
  form: FormData,
): Promise<RemoveState> {
  const id = formId(form, 'id');
  if (id === null) return { refusal: 'exception_not_found' };
  const outcome = await writeAsClub((api, auth) =>
    api.DELETE('/api/v1/club/exceptions/{exception_id}', {
      ...auth,
      params: { path: { exception_id: id } },
    }),
  );
  if (!outcome.ok) {
    redrawIfStale(outcome.error);
    return { refusal: outcome.error.code };
  }
  revalidatePath(PAGE);
  return { refusal: null };
}

// --- Prices ------------------------------------------------------------------

export interface PricesFormState extends FormState<Sport> {
  /** The table as the backend recorded it, after a save that landed. */
  readonly saved: readonly SportPrice[] | null;
}

/**
 * **Save prices**: the whole table, a sport left unpriced left out. A refusal lands under the
 * sport it names (`details.sport`); one naming none goes over the form.
 */
export async function savePrices(
  _previous: PricesFormState,
  form: FormData,
): Promise<PricesFormState> {
  const { refusals, rows } = checkPrices(readPrices(form));
  if (hasRefusals(refusals)) return { refusals, formRefusal: null, saved: null };

  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/prices', { ...auth, body: toPricesBody(rows) }),
  );
  if (!outcome.ok) {
    // A sport the club stopped offering meanwhile: the table is out of date.
    if (outcome.error.code === 'price_sport_not_offered') revalidatePath(PAGE);
    const sport = refusedSport(outcome.error);
    const placed: Refusals<Sport> = isSport(sport) ? { [sport]: outcome.error.code } : {};
    return {
      refusals: placed,
      formRefusal: isSport(sport) ? null : outcome.error.code,
      saved: null,
    };
  }
  revalidatePath(PAGE);
  return { refusals: {}, formRefusal: null, saved: outcome.data.prices.map(toSportPrice) };
}
