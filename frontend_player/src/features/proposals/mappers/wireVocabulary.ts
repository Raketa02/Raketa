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
  CalledOffReason,
  CardType,
  ClubCancelReason,
  CourtState,
  DayRange,
  HomeStatus,
  LeavingKind,
  OverlapGrade,
  OverlapShade,
  PaymentRefusal,
  ProposalStatus,
  ReaderAction,
  UncountedReason,
  Who,
} from '../domain/vocabulary';

type Schemas = components['schemas'];

export const PROPOSALS_VOCABULARY_AGREES: {
  readonly cardType: Exact<CardType, Schemas['CardType']>;
  readonly courtState: Exact<CourtState, Schemas['CourtState']>;
  readonly grade: Exact<OverlapGrade, Schemas['OverlapGrade']>;
  readonly shade: Exact<OverlapShade, Schemas['OverlapShade']>;
  readonly range: Exact<DayRange, Schemas['DayRange']>;
  readonly paymentRefusal: Exact<PaymentRefusal, Schemas['PaymentRefusal']>;
  readonly homeStatus: Exact<HomeStatus, Schemas['HomeStatus']>;
  readonly calledOffReason: Exact<CalledOffReason, Schemas['CalledOffReason']>;
  readonly clubCancelReason: Exact<ClubCancelReason, Schemas['ClubCancelReason']>;
  readonly uncountedReason: Exact<UncountedReason, Schemas['UncountedReason']>;
  readonly leaving: Exact<LeavingKind, Schemas['Leaving']>;
  readonly proposalStatus: Exact<ProposalStatus, Schemas['ProposalStatus']>;
  readonly readerAction: Exact<ReaderAction, Schemas['ReaderAction']>;
  readonly who: Exact<Who, Schemas['Who']>;
} = {
  cardType: true,
  courtState: true,
  grade: true,
  shade: true,
  range: true,
  paymentRefusal: true,
  homeStatus: true,
  calledOffReason: true,
  clubCancelReason: true,
  uncountedReason: true,
  leaving: true,
  proposalStatus: true,
  readerAction: true,
  who: true,
};
