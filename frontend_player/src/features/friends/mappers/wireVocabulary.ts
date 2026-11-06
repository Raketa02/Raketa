/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler, over the
 * one `Exact` in `@/shared/vocabulary/wireAgreement`, as `groups` and `notifications` assert theirs
 * (#753). A relation or an origin added, removed or renamed on the wire fails here.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { AskedFrom, FriendRelation } from '../domain/vocabulary';

type Schemas = components['schemas'];

export const FRIENDS_VOCABULARY_AGREES: {
  readonly relation: Exact<FriendRelation, Schemas['FriendRelation']>;
  readonly askedFrom: Exact<AskedFrom, Schemas['AskedFrom']>;
} = { relation: true, askedFrom: true };
