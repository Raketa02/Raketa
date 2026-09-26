/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler, over
 * the one `Exact` in `@/shared/vocabulary/wireAgreement`, as `games` and `play` assert theirs.
 * A code added, removed or renamed on the wire fails here.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { GroupKind, GroupRelation, JoinPolicy, ReadAs } from '../domain/vocabulary';

export const GROUP_VOCABULARY_AGREES: {
  readonly kind: Exact<GroupKind, components['schemas']['GroupKind']>;
  readonly relation: Exact<GroupRelation, components['schemas']['GroupRelation']>;
  readonly joinPolicy: Exact<JoinPolicy, components['schemas']['JoinPolicy']>;
  readonly readAs: Exact<ReadAs, components['schemas']['ReadAs']>;
} = { kind: true, relation: true, joinPolicy: true, readAs: true };
