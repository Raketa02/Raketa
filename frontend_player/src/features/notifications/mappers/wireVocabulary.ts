/**
 * The agreement between the domain's unions and the contract — asserted by the compiler, over the
 * one `Exact` in `@/shared/vocabulary/wireAgreement`, as `payments` and `proposals` assert theirs
 * (#559). A notice kind added, removed or renamed on the wire fails here; so does a place a tap
 * opens, which the push's payload is checked against.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { NoticeKind, Opens } from '../domain/vocabulary';

type Schemas = components['schemas'];

export const NOTIFICATIONS_VOCABULARY_AGREES: {
  readonly kind: Exact<NoticeKind, Schemas['NoticeKind']>;
  readonly opens: Exact<Opens, Schemas['Opens']>;
} = { kind: true, opens: true };
