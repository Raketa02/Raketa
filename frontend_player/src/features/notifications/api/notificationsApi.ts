/**
 * **The notices on the wire** — one of the two layers allowed to read generated types, and the only
 * place these paths are written down ([#559](https://github.com/Raketa02/Raketa/issues/559); the
 * routes are #549's).
 *
 * | | |
 * | --- | --- |
 * | `getChoices` | `GET /players/me/notifications` — the three choices |
 * | `putChoices` | `PUT` the same path — all three, as a tap leaves them; answers what is saved |
 * | `postDevice` | `POST /players/me/devices` — push this phone; the token in the body, never a path |
 * | `getNotices` | `GET /players/me/notices` — the recent list, newest first, and the bell's number |
 * | `postVisit` | `POST /players/me/notices/visit` — the list was opened; the number is nought (#621) |
 *
 * A phone's removal at sign-out is the sign-out's own step, in `auth`'s api: it is one of the acts
 * that must happen while the session can still make them.
 *
 * ## A `signal` on the reads and none on the writes
 *
 * `proposalsApi`'s asymmetry, for its reason: a cancelled write can land with nobody holding the
 * reply that says so.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

const ME = '/api/v1/players/me';

/** The read may be abandoned; a write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

export function getChoices({ signal }: Cancellable = {}): Promise<
  Schemas['NotificationChoicesSchema']
> {
  return httpRequest({ method: 'GET', path: `${ME}/notifications`, authenticated: true, signal });
}

export function putChoices(
  body: Schemas['NotificationChoicesSchema'],
): Promise<Schemas['NotificationChoicesSchema']> {
  return httpRequest({ method: 'PUT', path: `${ME}/notifications`, body, authenticated: true });
}

/**
 * Push this phone. `204` — also when it already was; `push_token_invalid` (400) for a token that is
 * not Expo's. The same answer twice is the same phone, so a repeat is safe.
 */
export function postDevice(body: Schemas['PushDeviceRequest']): Promise<void> {
  return httpRequest({ method: 'POST', path: `${ME}/devices`, body, authenticated: true });
}

export function getNotices({ signal }: Cancellable = {}): Promise<
  Schemas['RecentNoticesResponse']
> {
  return httpRequest({ method: 'GET', path: `${ME}/notices`, authenticated: true, signal });
}

/**
 * The list behind the bell was opened — sent **right after the read the open list is drawn from**:
 * whatever is listed by the time it arrives counts as seen, and the bell is nought on every phone.
 * `204`, also when nothing moved; a visit never moves the last one back, so a repeat is safe.
 */
export function postVisit(): Promise<void> {
  return httpRequest({ method: 'POST', path: `${ME}/notices/visit`, authenticated: true });
}
