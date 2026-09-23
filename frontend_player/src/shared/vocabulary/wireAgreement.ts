/**
 * How a hand-written vocabulary is held to the contract: **by the compiler, in one type.**
 *
 * Every closed vocabulary the platform serves is written down twice — once in
 * `backend/openapi.player.json`, and once as the list of values *this build can draw*, which
 * is what a copy table is keyed by and what makes a code with no words a build failure
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1). Two lists that must
 * agree and nothing checking it is the drift every table in this folder exists to prevent.
 *
 * The check cannot live beside the copy: generated wire types may be read **only** inside a
 * feature's `api/` or `mappers/` layer (`docs/architecture.md` Part 1, and an ESLint rule). So
 * each feature asserts the agreement in one `mappers/wireVocabulary.ts`, and the type that
 * expresses it lives here, once, where both can cite it.
 *
 * **One assertion is not in a feature, and it is not an exception to that rule so much as the
 * rule reaching a route with no feature.** `shared/lib/platform/liveStream.ts` parses the live
 * channel's frame, which ADR-0147 §7 requires to be the generated `LiveNudgeSchema` — and a
 * transport may not be imported by a feature's `api/` layer, so the port *is* that route's `api/`
 * layer. It carries its own `Exact` row for the same reason every other one does. The linter's
 * exemption is one file wide and `pnpm test:boundaries` asserts both halves of it.
 */

/**
 * True only when the two unions are the **same set**.
 *
 * Both directions, because each catches a different mistake: one way round a value added to
 * the contract passes unnoticed, the other way round a retired one does — and a `Record` can
 * only ever see the first, since it is perfectly happy to hold words for a code that no longer
 * exists.
 */
export type Exact<Ours, Wire> = [Ours] extends [Wire]
  ? [Wire] extends [Ours]
    ? true
    : false
  : false;
