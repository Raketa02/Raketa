/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler.
 *
 * The same mechanism `features/play/mappers/wireVocabulary.ts` uses, over the one `Exact` in
 * `@/shared/vocabulary/wireAgreement`, and for the same reason: `the-words.md` §1 requires each
 * copy table to be **keyed by the generated union** so that a code with no words is a build
 * failure, and generated types may be read only inside `api/` or `mappers/`. So the unions are
 * read here, once, and held equal — a value added fails here and again in every table that has
 * no words for it, and a value removed or renamed fails here alone, which is the case a
 * `Record` cannot see.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type {
  AttendanceState,
  GameKind,
  GameSide,
  GameStanding,
  Outcome,
} from '../domain/vocabulary';

export const GAME_VOCABULARY_AGREES: {
  readonly standing: Exact<GameStanding, components['schemas']['GameStanding']>;
  readonly kind: Exact<GameKind, components['schemas']['GameKind']>;
  readonly side: Exact<GameSide, components['schemas']['GameSide']>;
  // The contract has two outcomes since Rankings (#768) — a result's and a ranking row's form — so
  // the generator names each by its module.
  readonly outcome: Exact<
    Outcome,
    components['schemas']['app__modules__games__domain__results__Outcome']
  >;
  readonly attendance: Exact<AttendanceState, components['schemas']['AttendanceState']>;
} = { standing: true, kind: true, side: true, outcome: true, attendance: true };
