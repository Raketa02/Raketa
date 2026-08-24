/**
 * The wire's closed vocabulary this feature keys a table on, and the two guards.
 *
 * `Situation` is the union `openapi-typescript` emits from
 * `backend/openapi.player.json`. **Nothing is retyped**, because a hand-written copy
 * of a wire enum switches off the completeness rule the table beside this file
 * depends on (`ADR-0075`): a `Record` over a hand-written union is a `Record` over
 * whatever somebody last remembered, and a `Record<string, Entry>` is an index
 * signature that never fails.
 *
 * It is aliased from `@/generated` rather than imported from Now's public surface,
 * which is the shape the departure feature already set: both point at the same
 * generated union, and what the two features say about it is different — Now's table
 * is the thirty-six sentences a card prints, and this one is the **two** endings a
 * result screen draws under them.
 */

import type { components } from '@/generated/schema';

/** What a match is doing, in the thirty-six names the ladder can answer with. */
export type Situation = components['schemas']['Situation'];

/**
 * `false` when `T` has widened to `string`, and `true` otherwise.
 *
 * The one hazard a `Record` cannot see: a table keyed on `Situation` is checked
 * against its members **only** while `Situation` is a closed union, and becomes an
 * index signature satisfied by anything the day the backend emits the field as a
 * bare string. `ADR-0075` names that as the decision's own dependency on the
 * backend, and a guardrail that quietly stops matching is worse than none.
 *
 * Declared here rather than imported: it is a type-level utility with no domain
 * content in it, so putting it on another feature's public surface would make that
 * feature the owner of a thing that is not its, and `src/shared/` does not take a
 * `types/` bucket.
 */
export type IsClosedUnion<T extends string> = string extends T ? false : true;

/** A compile error unless `T` is `true`. A guard rather than a comment. */
export type AssertTrue<T extends true> = T;
