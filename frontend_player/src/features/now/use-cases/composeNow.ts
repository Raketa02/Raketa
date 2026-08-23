/**
 * Ask for the whole screen.
 *
 * A thin pass-through, and `ADR-0009`'s escape hatch covers exactly that: the
 * client has no business rule about composing Now, because composing Now is the
 * server's whole job here and a client-side opinion about it would be a second,
 * weaker one. The folder is kept for predictability rather than filled with an
 * invented invariant.
 */

import { composeNow as fetchNow } from '../api/nowApi';
import type { ComposedScreen } from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';
import { toComposedScreen } from '../mappers/nowMappers';

export interface ComposeNowOptions {
  readonly sport: SportFilter;
  readonly signal?: AbortSignal;
}

export function composeNow({ sport, signal }: ComposeNowOptions): Promise<ComposedScreen> {
  return fetchNow({ sport, signal }).then(toComposedScreen);
}
