/**
 * The wire adapter for the Player profile. One of the two layers allowed to read generated
 * types, and the only place these paths are written down.
 *
 * Nothing here decides anything: which tags a player may hold and how many of them are
 * rules, and they live above.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type PlayerProfileOptionsResponse = components['schemas']['PlayerProfileOptionsResponse'];

export interface PlayerProfileApiOptions {
  readonly signal?: AbortSignal;
}

/**
 * The Social tag vocabulary, how many of them a profile must hold, and the Search radius
 * bounds — in one round trip, because they are the same kind of thing and the same part of
 * onboarding needs them at the same moment.
 *
 * **Unauthenticated**, as the route is: it is closed reference data about the platform and
 * carries nothing about the player. `authenticated` is stated rather than inferred here for
 * the reason the client gives — "the endpoints that take no token" is a different set from
 * "the endpoints that happen to have none right now".
 */
export function getProfileOptions({
  signal,
}: PlayerProfileApiOptions = {}): Promise<PlayerProfileOptionsResponse> {
  return httpRequest<PlayerProfileOptionsResponse>({
    method: 'GET',
    path: '/api/v1/player-profile/options',
    authenticated: false,
    signal,
  });
}
