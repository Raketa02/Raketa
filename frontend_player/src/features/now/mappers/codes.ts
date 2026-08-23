/**
 * The wire's closed vocabularies, named for this feature.
 *
 * Every alias here is the union `openapi-typescript` emits from
 * `backend/openapi.player.json`, re-exported under the name the feature uses.
 * **Nothing is retyped**, because a hand-written copy of a wire enum is the one
 * thing that would switch off the completeness rule the tables beside this file
 * depend on (`ADR-0075`): a `Record` over a hand-written union is a `Record`
 * over whatever somebody last remembered, and a `Record<string, Entry>` is an
 * index signature that never fails.
 *
 * This is also why the tables live in `mappers/` and not in `domain/`.
 * `mappers/` is this app's declared wire boundary and the only feature layer
 * permitted to read `@/generated`; the tables map a wire code to a value object
 * `domain/` owns, which is what a mapper is.
 */

import type { components } from '@/generated/schema';

/** What a match is doing, in thirty-six sentences and no more. */
export type Situation = components['schemas']['Situation'];

/** The facts the situation's sentence prints. Grows as the contract grows. */
export type SituationFacts = components['schemas']['SituationFactsResponse'];

/** Why a court is being kept aside, in the five reasons that reach a card. */
export type HoldNote = components['schemas']['HoldNoteResponse'];

/** Five of the kernel's thirteen hold reasons — the ones a card names. */
export type CardHoldReason = components['schemas']['CardHoldReason'];

/** One reason behind the fit badge, as a machine code and no weight. */
export type FitReason = components['schemas']['FitReasonResponse'];

/** The stable machine key of every term the fit engine can emit. */
export type TermCode = components['schemas']['TermCode'];

/** The one act a card may name, from a closed set of seven. */
export type ActCode = components['schemas']['ActCode'];

/** Which claim a shelf makes, as a code and never as a title string. */
export type ShelfCode = components['schemas']['ShelfCode'];

/** Which one-line caption a shelf carries, when it carries one. */
export type CaptionCode = components['schemas']['CaptionCode'];

/** The sport bar's five fixed chips, as the one value a request carries. */
export type SportFilter = components['schemas']['SportFilter'];

/** The rule that fired, where a card names one. */
export type Cause = components['schemas']['Cause'];

/**
 * `false` when `T` has widened to `string`, and `true` otherwise.
 *
 * The one hazard a `Record` cannot see. `Record<Situation, Entry>` fails to
 * compile when a member is missing **only** while `Situation` is a closed union;
 * if the backend ever emits the field as a bare string, the same `Record`
 * becomes an index signature, silently satisfied by anything, and the missing
 * sentence ships as a blank line on somebody's home screen. `ADR-0075` names
 * this as the decision's own dependency on the backend, and a guardrail that
 * quietly stops matching is worse than none.
 */
export type IsClosedUnion<T extends string> = string extends T ? false : true;

/**
 * A compile error unless `T` is `true`.
 *
 * Paired with `IsClosedUnion` this is a *guard* rather than a comment: widening
 * a union violates the constraint and `pnpm typecheck` says so, where a type
 * that merely resolved to `never` would go on compiling.
 */
export type AssertTrue<T extends true> = T;
