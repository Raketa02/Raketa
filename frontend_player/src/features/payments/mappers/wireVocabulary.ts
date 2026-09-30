/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler, over
 * the one `Exact` in `@/shared/vocabulary/wireAgreement`, as `proposals` and `games` assert theirs.
 * A wallet added, removed or renamed on the wire fails here, where the method card's badge and the
 * row's line are keyed by it.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { Wallet } from '../domain/vocabulary';

type Schemas = components['schemas'];

export const PAYMENTS_VOCABULARY_AGREES: {
  readonly wallet: Exact<Wallet, Schemas['Wallet']>;
} = { wallet: true };
