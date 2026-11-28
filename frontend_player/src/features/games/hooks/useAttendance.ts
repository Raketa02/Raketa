/**
 * **Who turned up** — the four writes at a booked game's court, and the one place a tap reads where
 * the phone is ([#658](https://github.com/Rakieta02/Rakieta/issues/658); ADR-0195 §3).
 *
 * | | |
 * | --- | --- |
 * | `useNoteNotHereYet` | `POST /attendance/not-here-yet` — *Oscar isn't here yet*, at the club |
 * | `useNoteArrival` | `POST /attendance/arrival` — *I'm here* or *they're here*, at the club |
 * | `useClaimPresence` | `POST /attendance/claim` — *I was there*, a day later at most |
 * | `useConfirmPresence` | `POST /attendance/confirmation` — *yes, they were here* |
 *
 * ## The position is read at the tap, inside the write, and kept by nobody
 *
 * The two writes made at the club read **one precise fix** through the location port the moment
 * they run — asking for the permission first, where asking achieves something — and hand it
 * straight to the request. It is never a mutation's variables, so the cache that remembers what
 * was sent never holds it: it goes out of scope with the function that read it, as the area's does
 * in `player_profile`'s `useLocationCapture`. A refused permission, a blocked one and a phone that
 * produced no fix are {@link LocationAtTheTap}, said beside the tap like any refusal.
 *
 * ## Made online or not at all — the two at the club
 *
 * The app's writes pause offline and resume on reconnect. These two do not
 * (`networkMode: 'always'`): **when an arrival lands decides what it was** — on time, Came late,
 * or nothing at all after the half hour — and the fix it carries was read where the player stood at
 * the tap. Queued to the next reconnect, an *I'm here* made at 17:08 could land as Came late, from
 * a position read somewhere else. So a tap with no connection fails now and says so
 * (`offlineMessage('does-not-resume')`). **The late claim and its confirmation pause like
 * everything else**: they carry no position, and their day is the same day however late they land
 * inside it — a claim queued past it is refused by name.
 *
 * ## Every write invalidates, and none is optimistic
 *
 * What a game becomes — awaited, on time, Came late, Didn't come — is the server's fold against its
 * own clock, so the only client that can be right about it is one that asks. The list is invalidated
 * and the booking re-read (`AfterAWrite`), as the result's writes do.
 */

import { useMutation } from '@tanstack/react-query';

import { isAppError, type AppError } from '@/shared/errors';
import { ensurePermission, useLocation, type LocationPort } from '@/shared/lib/platform';

import { isRoughFix, type LocationRefusal, type TapPosition } from '../domain/attendance';
import {
  claimPresence,
  confirmPresence,
  noteArrival,
  noteNotHereYet,
  type AboutAPlayer,
} from '../use-cases/attendance';

import { useAfterAWrite, type AfterAWrite } from './useGames';

/**
 * **The phone could not say where it is** (`LocationRefusal`) — so nothing was sent, or what it sent
 * was too rough for the backend to place at the club.
 */
export class LocationAtTheTap extends Error {
  override readonly name = 'LocationAtTheTap';

  constructor(readonly refusal: LocationRefusal) {
    super(`No position at the tap: ${refusal}`);
  }
}

/** What a tap at the club can be refused with: the server's word, or the phone's. */
export type AttendanceError = AppError | LocationAtTheTap;

/**
 * **A tap made at the club** — where the phone is, asked for where asking achieves something, then
 * one precise fix, handed to `send` and returned to nobody. **A fix too rough for the check** that
 * the backend answers *not at the club* is said as that (`isRoughFix`): a phone sharing only an
 * approximate position is the likeliest reason a player standing there hears it, and its remedy is
 * a setting rather than a walk. The backend still decides; this only chooses the sentence.
 */
async function fromTheClub(
  location: LocationPort,
  send: (at: TapPosition) => Promise<void>,
): Promise<void> {
  const permission = await ensurePermission(location);
  if (permission !== 'granted') {
    throw new LocationAtTheTap(permission === 'blocked' ? 'blocked' : 'refused');
  }
  const at = await location.readPreciseFix();
  if (at === null) throw new LocationAtTheTap('no-fix');
  try {
    await send(at);
  } catch (error) {
    if (isAppError(error) && error.code === 'not_at_the_club' && isRoughFix(at)) {
      throw new LocationAtTheTap('rough');
    }
    throw error;
  }
}

/** ***Oscar isn't here yet*** — made at the club, in the first half hour. */
export function useNoteNotHereYet(after: AfterAWrite = {}) {
  const location = useLocation();
  const onSuccess = useAfterAWrite(after);

  return useMutation<void, AttendanceError, AboutAPlayer>({
    mutationFn: (about) => fromTheClub(location, (at) => noteNotHereYet(about, at)),
    networkMode: 'always',
    onSuccess,
  });
}

/** ***I'm here*** with the reader's own id, ***they're here*** with somebody else's — at the club. */
export function useNoteArrival(after: AfterAWrite = {}) {
  const location = useLocation();
  const onSuccess = useAfterAWrite(after);

  return useMutation<void, AttendanceError, AboutAPlayer>({
    mutationFn: (about) => fromTheClub(location, (at) => noteArrival(about, at)),
    networkMode: 'always',
    onSuccess,
  });
}

/** ***I was there*** — no position, a day later at most. Pauses offline like the app's writes. */
export function useClaimPresence(after: AfterAWrite = {}) {
  const onSuccess = useAfterAWrite(after);

  return useMutation<void, AppError, string>({ mutationFn: claimPresence, onSuccess });
}

/** ***Yes, they were here*** — about somebody else's claim. Pauses offline like the app's writes. */
export function useConfirmPresence(after: AfterAWrite = {}) {
  const onSuccess = useAfterAWrite(after);

  return useMutation<void, AppError, AboutAPlayer>({ mutationFn: confirmPresence, onSuccess });
}
