/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler, over
 * the one `Exact` in `@/shared/vocabulary/wireAgreement`, as `games`, `play` and `groups` assert
 * theirs. A code added, removed or renamed on the wire fails here.
 *
 * The kind is not among them: it is spelled as the switch spells it, and `deckMappers`' two
 * tables are what hold the pair together — a `Record` over the wire's union, so a third mode would
 * fail to compile there.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type {
  CardType,
  CourtState,
  DayRange,
  OverlapGrade,
  OverlapShade,
} from '../domain/vocabulary';

type Schemas = components['schemas'];

export const PROPOSALS_VOCABULARY_AGREES: {
  readonly cardType: Exact<CardType, Schemas['CardType']>;
  readonly courtState: Exact<CourtState, Schemas['CourtState']>;
  readonly grade: Exact<OverlapGrade, Schemas['OverlapGrade']>;
  readonly shade: Exact<OverlapShade, Schemas['OverlapShade']>;
  readonly range: Exact<DayRange, Schemas['DayRange']>;
} = { cardType: true, courtState: true, grade: true, shade: true, range: true };
