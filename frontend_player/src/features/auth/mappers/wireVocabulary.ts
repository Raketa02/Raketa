/**
 * **The wire's vocabulary and this feature's, held equal at compile time** — the union
 * `domain/vocabulary.ts` spells and the one `src/generated/` carries. A state the backend adds to an
 * invitation's link fails `pnpm typecheck` here rather than drawing a link that works as one that
 * does not.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { InvitationLinkState } from '../domain/vocabulary';

export const AUTH_VOCABULARY_AGREES: {
  readonly invitationLinkState: Exact<
    InvitationLinkState,
    components['schemas']['InvitationLinkState']
  >;
} = { invitationLinkState: true };
