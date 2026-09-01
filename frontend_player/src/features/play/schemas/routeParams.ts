/**
 * The two Play routes that carry a param, validated — **the origin search, and the seat.**
 *
 * A route param is attacker-controlled and expo-router hands it over as
 * `string | string[] | undefined` whatever the route declared, so it is checked before
 * anything reads it. The check is worth having twice over here, because this string becomes
 * `ForecastRequest.search_id` and a Query key: an unchecked one would put somebody else's
 * text into a request body and into the cache under a key nothing could ever clear.
 *
 * **The sport and the mode are deliberately not params.** They are `playPreferences`', which
 * is process-scoped and cannot be linked into — and a builder whose sport came off a link
 * could disagree with the chips one screen back, which is the state the origin key exists to
 * make impossible rather than one to render.
 *
 * A link that does not survive this is not a builder at all: there is no origin, so there is
 * nothing to seat anybody from and no forecast to ask for. The route sends it to Play's start.
 */

import { z } from 'zod';

export const builderRouteParams = z.object({
  /** The search this builder was opened on. `POST /forecasts` refuses anything else. */
  search: z.string().uuid(),
});

export type BuilderRouteParams = z.infer<typeof builderRouteParams>;

/** `undefined` when the link cannot be trusted. The route decides where that goes. */
export function parseBuilderRouteParams(
  params: Record<string, string | string[] | undefined>,
): BuilderRouteParams | undefined {
  const result = builderRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}

/**
 * The pool's two params — **the search the list comes off, and the seat it is filling.**
 *
 * The first is the builder's own, checked identically and for the same two reasons: it becomes
 * a Query key and a request body. The second is what makes this visit *about* something — the
 * pool is opened **against a seat**, from a seat's own tap or from the control beneath the
 * court, and where that seat is occupied the add is a **replacement** rather than an addition.
 *
 * **The seat is not bounded here**, and that is deliberate rather than lax. Which indices exist
 * is a fact about the Sport's court, and the sport is not a param — it is the origin search's,
 * read off the record this screen holds. So the bound is applied where the court is known:
 * a seating has exactly as many entries as the court has seats, and an index outside it reads
 * as no seat at all, which is the same answer an empty one gives. A number in this schema would
 * be the seat count written down a second place, and the second place is the one that goes
 * stale when a sport with a different court arrives.
 *
 * **The pending replacement needs no clearing rule.** The court **pops** rather than pushes, so
 * this route unmounts and takes the state with it — G7's *"leaving the pool halfway through
 * replacing somebody should be forgotten"* is satisfied by the navigation decision
 * ([#228](https://github.com/Raketa02/Raketa/issues/228) §6), and a store would reintroduce
 * exactly the bug it was meant to prevent.
 */
export const poolRouteParams = z.object({
  /** The search whose rows this list draws. `POST /forecasts` refuses anything else. */
  search: z.string().uuid(),
  /**
   * Which seat the visit is filling.
   *
   * Matched as digits and then converted, rather than coerced: `z.coerce.number()` reads an
   * empty string and a `null` as **zero**, and zero is a seat — the searcher's own. A link
   * carrying no seat at all would arrive as a visit against a seat nobody tapped.
   */
  seat: z.string().regex(/^\d+$/).transform(Number),
});

export type PoolRouteParams = z.infer<typeof poolRouteParams>;

/** `undefined` when the link cannot be trusted. The route decides where that goes. */
export function parsePoolRouteParams(
  params: Record<string, string | string[] | undefined>,
): PoolRouteParams | undefined {
  const result = poolRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
