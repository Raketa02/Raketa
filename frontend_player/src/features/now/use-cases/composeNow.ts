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
  // The sport goes out on the request and comes back into the mapper, because the
  // one block that has no sport of its own — the door — is worded with it. It is
  // the request's own value rather than a second read of the store: the answer
  // being mapped is the answer to *this* ask, and a chip changed while it was in
  // flight must not word it.
  return fetchNow({ sport, signal }).then((wire) => toComposedScreen(wire, sport));
}
