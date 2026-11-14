/**
 * **Discovery's routes** ([#801](https://github.com/Raketa02/Raketa/issues/801); the backend's #793).
 *
 * | Route | |
 * | --- | --- |
 * | `GET /new-in-raketa` | Home's row: up to 10, the server's order |
 * | `GET /new-in-raketa/all?sport&after` | See all: 20 to a page, newest first, `next` behind them |
 *
 * Both refuse `block_state_unavailable` (503) — the blocks could not be read, so no row is drawn
 * rather than one that might suggest a blocked person — and See all `not_a_new_in_raketa_page` (400)
 * for a cursor the server never wrote. Neither is said: the row is left out, and See all says the
 * failure's recovery sentence with *Try again*.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

const NEW_IN_RAKETA_PATH = '/api/v1/new-in-raketa';

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

export function getNewInRaketaPage(
  page: { readonly sport?: Schemas['Sport']; readonly after?: string },
  { signal }: Cancellable = {},
): Promise<Schemas['NewInRaketaPageResponse']> {
  const query = new URLSearchParams({
    ...(page.sport === undefined ? {} : { sport: page.sport }),
    ...(page.after === undefined ? {} : { after: page.after }),
  }).toString();
  return httpRequest<Schemas['NewInRaketaPageResponse']>({
    method: 'GET',
    path: `${NEW_IN_RAKETA_PATH}/all${query === '' ? '' : `?${query}`}`,
    authenticated: true,
    signal,
  });
}
