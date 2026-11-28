/**
 * **Read Home's Top 10** ([#805](https://github.com/Rakieta02/Rakieta/issues/805)) — the route, asked for
 * a sport exactly or as the preferred one, folded into the row's shape. No rule of its own: the order,
 * the places, the chips and the fall-through are the server's (the Home rows mechanics §10), so this
 * is the uniform-strict pass-through.
 *
 * **An answer naming a sport this build has never heard of is no answer** (`toTopTen`): `null`, a
 * value the query may hold where `undefined` may not, and the row stays hidden as it does for a read
 * still out.
 */

import { toWireSport } from '@/features/onboarding/types';

import { getTopTen, type Cancellable } from '../api/rankingsApi';
import type { TopTen, TopTenAsk } from '../domain/topTen';
import { toTopTen } from '../mappers/rankingMappers';

export function readTopTen(ask: TopTenAsk, { signal }: Cancellable = {}): Promise<TopTen | null> {
  const sport = toWireSport(ask.sport);
  return getTopTen(
    ask.kind === 'sport' ? { sport } : { prefer: sport },
    signal === undefined ? {} : { signal },
  ).then((wire) => toTopTen(wire) ?? null);
}
