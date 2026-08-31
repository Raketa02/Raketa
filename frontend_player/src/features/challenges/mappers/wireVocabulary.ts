/**
 * The agreement between `domain/standing.ts` and the contract — asserted by the compiler.
 *
 * The same mechanism `features/play/mappers/wireVocabulary.ts` uses, over the one `Exact` in
 * `@/shared/vocabulary/wireAgreement`: the copy deck must be keyed by the generated union, and
 * generated types may be read only in `api/` or `mappers/`. A standing added, removed or renamed on the contract fails here, at
 * `pnpm typecheck`, in the file whose whole job is saying so.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { Standing } from '../domain/standing';

export const STANDING_AGREES: Exact<Standing, components['schemas']['Standing']> = true;
