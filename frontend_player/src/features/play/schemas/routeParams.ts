/**
 * The builder's one param, validated — **the origin search it arrives on.**
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
