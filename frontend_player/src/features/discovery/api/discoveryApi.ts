/**
 * **Discovery's routes** ([#801](https://github.com/Raketa02/Raketa/issues/801), the backend's #793;
 * [#802](https://github.com/Raketa02/Raketa/issues/802), the backend's #794;
 * [#803](https://github.com/Raketa02/Raketa/issues/803), the backend's #795).
 *
 * | Route | |
 * | --- | --- |
 * | `GET /new-in-raketa` | Home's row: up to 10, the server's order |
 * | `GET /new-in-raketa/all?sport&after` | See all: 20 to a page, newest first, `next` behind them |
 * | `GET /same-level` | Home's row: up to 10, fresh good matches first, then the gaps |
 * | `GET /same-level/all?sport&after` | See all: 20 to a page, best % first; a sport re-compares everybody in it |
 * | `GET /same-vibe` | Home's row: up to 10, fresh good matches first, then the gaps |
 * | `GET /same-vibe/all?sport&after` | See all: 20 to a page, most in common first; a sport keeps who holds a level in it |
 *
 * Every one refuses `block_state_unavailable` (503) — the blocks could not be read, so no row is
 * drawn rather than one that might suggest a blocked person — and each See all its own code for a
 * cursor the server never wrote (`not_a_new_in_raketa_page`, `not_a_same_level_page`,
 * `not_a_same_vibe_page`, 400). None is
 * said: the row is left out, and See all says the failure's recovery sentence with *Try again*.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

const NEW_IN_RAKETA_PATH = '/api/v1/new-in-raketa';
const SAME_LEVEL_PATH = '/api/v1/same-level';
const SAME_VIBE_PATH = '/api/v1/same-vibe';

export interface Cancellable {
  readonly signal?: AbortSignal;
}

export function getNewInRaketa({ signal }: Cancellable = {}): Promise<
  Schemas['NewInRaketaResponse']
> {
  return httpRequest<Schemas['NewInRaketaResponse']>({
    method: 'GET',
    path: NEW_IN_RAKETA_PATH,
    authenticated: true,
    signal,
  });
}

/** Which page of a See all — a sport, or every one, and the cursor it is read after. */
export interface PageAsked {
  readonly sport?: Schemas['Sport'];
  readonly after?: string;
}

export function getNewInRaketaPage(
  page: PageAsked,
  { signal }: Cancellable = {},
): Promise<Schemas['NewInRaketaPageResponse']> {
  return httpRequest<Schemas['NewInRaketaPageResponse']>({
    method: 'GET',
    path: seeAllPath(NEW_IN_RAKETA_PATH, page),
    authenticated: true,
    signal,
  });
}

export function getSameLevel({ signal }: Cancellable = {}): Promise<Schemas['SameLevelResponse']> {
  return httpRequest<Schemas['SameLevelResponse']>({
    method: 'GET',
    path: SAME_LEVEL_PATH,
    authenticated: true,
    signal,
  });
}

export function getSameLevelPage(
  page: PageAsked,
  { signal }: Cancellable = {},
): Promise<Schemas['SameLevelPageResponse']> {
  return httpRequest<Schemas['SameLevelPageResponse']>({
    method: 'GET',
    path: seeAllPath(SAME_LEVEL_PATH, page),
    authenticated: true,
    signal,
  });
}

export function getSameVibe({ signal }: Cancellable = {}): Promise<Schemas['SameVibeResponse']> {
  return httpRequest<Schemas['SameVibeResponse']>({
    method: 'GET',
    path: SAME_VIBE_PATH,
    authenticated: true,
    signal,
  });
}

export function getSameVibePage(
  page: PageAsked,
  { signal }: Cancellable = {},
): Promise<Schemas['SameVibePageResponse']> {
  return httpRequest<Schemas['SameVibePageResponse']>({
    method: 'GET',
    path: seeAllPath(SAME_VIBE_PATH, page),
    authenticated: true,
    signal,
  });
}

/** `{row}/all`, with `sport` and `after` only where asked. */
function seeAllPath(row: string, page: PageAsked): string {
  const query = new URLSearchParams({
    ...(page.sport === undefined ? {} : { sport: page.sport }),
    ...(page.after === undefined ? {} : { after: page.after }),
  }).toString();
  return `${row}/all${query === '' ? '' : `?${query}`}`;
}
