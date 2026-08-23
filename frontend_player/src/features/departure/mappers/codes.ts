/**
 * The wire's closed vocabularies, named for this feature.
 *
 * Both aliases below are the union `openapi-typescript` emits from
 * `backend/openapi.player.json`. **Nothing is retyped**, because a hand-written
 * copy of a wire enum switches off the completeness rule the tables beside this
 * file depend on (`ADR-0075`): a `Record` over a hand-written union is a `Record`
 * over whatever somebody last remembered, and a `Record<string, Entry>` is an
 * index signature that never fails.
 *
 * `Outcome` is also aliased in `features/now/mappers/codes.ts`, and that is an
 * alias of one source rather than a second copy of anything: both point at the
 * same generated union, and the two features say **different things** about it —
 * Now words a leaver's own money, this screen names the outcome as a row, a button
 * and an acknowledgement. Promoting one table so both could read it would be
 * promoting a table neither of them wants.
 */

import type { components } from '@/generated/schema';

/** What a departure gets back, or will, in the four labels the model closes on. */
export type Outcome = components['schemas']['Outcome'];

/** Where one of those four stands on the quote's own timeline, right now. */
export type OutcomeStanding = components['schemas']['OutcomeStanding'];

/**
 * `false` when `T` has widened to `string`, and `true` otherwise.
 *
 * The one hazard a `Record` cannot see: `Record<Outcome, Entry>` fails to compile
 * on a missing member **only** while `Outcome` is a closed union, and becomes an
 * index signature satisfied by anything the day the backend emits the field as a
 * bare string. `ADR-0075` names that as the decision's own dependency on the
 * backend, and a guardrail that quietly stops matching is worse than none.
 *
 * Declared here rather than imported from Now: it is a type-level utility with no
 * domain content in it, so putting it on Now's public surface would make Now the
 * owner of a thing that is not Now's, and `src/shared/` does not take a
 * `types/` bucket. Eight lines twice is the cheaper of the two.
 */
export type IsClosedUnion<T extends string> = string extends T ? false : true;

/** A compile error unless `T` is `true`. A guard rather than a comment. */
export type AssertTrue<T extends true> = T;
