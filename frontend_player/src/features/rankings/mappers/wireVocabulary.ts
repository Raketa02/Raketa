/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler, over the
 * one `Exact` in `@/shared/vocabulary/wireAgreement`, as `friends` and `groups` assert theirs. A card
 * state, a chip or a view added, removed or renamed on the wire fails here; so does a form that
 * stops being a win or a loss, which the record's *Run of form* draws.
 */

import type { components } from '@/generated/schema';
import type { GameResult } from '@/shared/vocabulary/gameResult';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { CardState, ChipKind, RankingView } from '../domain/vocabulary';

type Schemas = components['schemas'];

export const RANKINGS_VOCABULARY_AGREES: {
  readonly cardState: Exact<CardState, Schemas['CardState']>;
  readonly chip: Exact<ChipKind, Schemas['ChipKind']>;
  readonly view: Exact<RankingView, Schemas['RankingView']>;
  readonly form: Exact<GameResult, Schemas['app__modules__rankings__domain__ranking__Outcome']>;
} = { cardState: true, chip: true, view: true, form: true };
