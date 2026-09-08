/**
 * The agreement between this feature's vocabulary and the contract — asserted by the compiler.
 *
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1 requires each copy
 * table to be *keyed by the generated union*, so that a code with no words is a build failure.
 * The wire boundary puts that union out of reach where the words live: generated types may be
 * read **only** inside a feature's `api/` or `mappers/` layer, which is
 * `docs/architecture.md` Part 1 and an ESLint rule. So the union is read here, once, and the
 * two are held equal:
 *
 * - a strand **added** to the vocabulary fails here, and then again in the table that has no
 *   words for it;
 * - one **removed or renamed** fails here alone, which is the case a `Record` cannot see — it
 *   is happy to hold words for a code that no longer exists.
 *
 * The runtime narrowing is beside the mapper that needs it, as `toSocialTagId` and
 * `toGameResult` already are: a served code this build cannot name is dropped from the list
 * rather than drawn as a row with no label on it.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { ReliabilityStrand } from '../domain/playerRecord';

/**
 * Exported because a value nothing reads is a value a linter is entitled to delete, and this
 * one is load-bearing precisely by existing.
 */
export const WIRE_VOCABULARY_AGREES: {
  readonly reliabilityStrand: Exact<ReliabilityStrand, components['schemas']['ReliabilityStrand']>;
} = {
  reliabilityStrand: true,
};
