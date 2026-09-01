/**
 * The agreement between `domain/vocabulary.ts` and the contract — asserted by the compiler.
 *
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1 requires each copy
 * table to be *keyed by the generated union*, so that a code with no words is a build
 * failure. The wire boundary puts that union out of reach where the words live: generated
 * types may be read **only** inside a feature's `api/` or `mappers/` layer, which is
 * `docs/architecture.md` Part 1 and an ESLint rule, not a preference. So the union is read
 * here, once, and the two are held equal:
 *
 * - a value **added** to a vocabulary fails here, and then again in every table that has no
 *   words for it;
 * - a value **removed or renamed** fails here alone, which is the case a `Record` cannot
 *   see — it is happy to hold words for a code that no longer exists.
 *
 * Either way the failure names the vocabulary that moved, at `pnpm typecheck`, in a file
 * whose whole job is saying so. The alternative — importing the generated union into
 * `components/` — buys the same guarantee by putting transport types in the copy deck, which
 * is the boundary this app enforces everywhere else.
 *
 * **There are no runtime mappers here yet.** They arrive with the routes that need them, and
 * each is the same membership test `toSocialTagId` is: a served code this build has no words
 * for becomes `undefined`, and §3 decides per placement whether that is a named gap or a
 * dropped row.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { Evidence } from '../domain/evidence';
import type {
  DegradedReason,
  GroupReason,
  InclusionReason,
  LevelDirection,
  LivenessReason,
  ModifierCode,
  OptimisedFor,
  PlayIntent,
  Prompt,
  Relationship,
  RelaxationAsk,
  Rung,
  SearchMode,
  SortOption,
  Term,
  UnfilledReason,
  Window,
} from '../domain/vocabulary';

/**
 * One row per vocabulary. A `false` here is a contract change that has not reached the copy —
 * the property that fails names which one.
 *
 * Exported because a value nothing reads is a value a linter is entitled to delete, and this
 * one is load-bearing precisely by existing.
 */
export const WIRE_VOCABULARY_AGREES: {
  readonly term: Exact<Term, components['schemas']['Term']>;
  readonly levelDirection: Exact<LevelDirection, components['schemas']['LevelDirection']>;
  readonly searchMode: Exact<SearchMode, components['schemas']['SearchMode']>;
  readonly playIntent: Exact<PlayIntent, components['schemas']['PlayIntent']>;
  readonly degradedReason: Exact<DegradedReason, components['schemas']['DegradedReason']>;
  readonly modifierCode: Exact<ModifierCode, components['schemas']['ModifierCode']>;
  readonly livenessReason: Exact<LivenessReason, components['schemas']['LivenessReason']>;
  readonly inclusionReason: Exact<InclusionReason, components['schemas']['WireInclusionReason']>;
  readonly unfilledReason: Exact<UnfilledReason, components['schemas']['UnfilledReason']>;
  readonly groupReason: Exact<GroupReason, components['schemas']['GroupReason']>;
  readonly prompt: Exact<Prompt, components['schemas']['Prompt']>;
  readonly window: Exact<Window, components['schemas']['Window']>;
  readonly sortOption: Exact<SortOption, components['schemas']['SortOption']>;
  readonly relaxationAsk: Exact<RelaxationAsk, components['schemas']['RelaxationAsk']>;
  readonly rung: Exact<Rung, components['schemas']['Rung']>;
  readonly optimisedFor: Exact<OptimisedFor, components['schemas']['OptimisedFor']>;
  readonly relationship: Exact<Relationship, components['schemas']['Relationship']>;
} = {
  term: true,
  levelDirection: true,
  searchMode: true,
  playIntent: true,
  degradedReason: true,
  modifierCode: true,
  livenessReason: true,
  inclusionReason: true,
  unfilledReason: true,
  groupReason: true,
  prompt: true,
  window: true,
  sortOption: true,
  relaxationAsk: true,
  rung: true,
  optimisedFor: true,
  relationship: true,
};

/**
 * The eight evidence variants, held to the contract the same way — by `kind`.
 *
 * The payload fields are this app's spelling and deliberately not asserted: that is the
 * ordinary mapper boundary, where `shared_count` becomes `sharedCount`. What must not drift
 * is the **set of variants**, because a ninth kind with no renderer is a reason line that
 * cannot be written.
 */
type WireEvidenceKind = components['schemas']['ScoredTermSchema']['evidence']['kind'];

export const EVIDENCE_KINDS_AGREE: Exact<Evidence['kind'], WireEvidenceKind> = true;
